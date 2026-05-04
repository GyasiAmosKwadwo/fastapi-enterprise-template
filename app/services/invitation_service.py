import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SecurityService
from app.models.client import Client
from app.models.invitation import Invitation, InvitationStatus
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.invitation import InvitationAccept, InvitationCreate
from app.services.email_service import EmailService
from app.services.two_factor_service import TwoFactorService


class InvitationService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.email_service = EmailService()

    def _generate_token(self) -> str:
        """Generate secure invitation token"""
        return secrets.token_urlsafe(32)

    async def create_invitation(self, data: InvitationCreate, invited_by_id: int) -> Invitation:
        """Create team member or client invitation"""
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Check if there's already a pending invitation for this email
        result = await self.db.execute(
            select(Invitation).where(
                Invitation.email == data.email, Invitation.status == InvitationStatus.PENDING
            )
        )
        existing_invite = result.scalars().first()
        if existing_invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An invitation for this email is already pending",
            )

        # Check if role exists
        role = await self.role_repo.get_by_id(data.role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        # Validate invitation type
        if data.invitation_type not in ["team", "client"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invitation_type must be 'team' or 'client'",
            )

        # For client invitations, company_name is required
        if data.invitation_type == "client" and not data.company_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="company_name is required for client invitations",
            )

        # For team invitations, role must be admin role
        if data.invitation_type == "team" and not role.is_admin_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team member invitations require an admin role",
            )

        # For client invitations, role must be client role
        if data.invitation_type == "client" and not role.is_client_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client invitations require a client role",
            )

        # Get inviter details for email
        inviter = await self.user_repo.get_by_id(invited_by_id)
        inviter_name = f"{inviter.first_name} {inviter.last_name}"

        # Create invitation
        invitation = Invitation(
            email=data.email,
            token=self._generate_token(),
            invited_by_id=invited_by_id,
            role_id=data.role_id,
            client_id=data.client_id,
            invitation_type=data.invitation_type,
            company_name=data.company_name,
            message=data.message,
            expires_at=datetime.utcnow() + timedelta(days=7),
            status=InvitationStatus.PENDING,
        )
        print(invitation)

        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)

        # Send invitation email
        if data.invitation_type == "team":
            self.email_service.send_team_invitation_email(
                to_email=data.email,
                inviter_name=inviter_name,
                role_name=role.name,
                invitation_token=invitation.token,
                message=data.message,
            )
        else:  # client
            self.email_service.send_client_invitation_email(
                to_email=data.email,
                inviter_name=inviter_name,
                company_name=data.company_name,
                invitation_token=invitation.token,
                message=data.message,
            )

        return invitation

    async def accept_invitation(self, data: InvitationAccept) -> dict:
        """Accept invitation and create user account"""
        # Find invitation
        result = await self.db.execute(select(Invitation).where(Invitation.token == data.token))
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invitation token"
            )

        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already used or expired"
            )

        if invitation.expires_at < datetime.utcnow():
            invitation.status = InvitationStatus.EXPIRED
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired"
            )

        # Get role
        role = await self.role_repo.get_by_id(invitation.role_id)

        # Determine base role
        if role.is_admin_role:
            base_role = "administrator"
        elif role.is_client_role:
            base_role = "client"
        else:
            base_role = "applicant"

        # For client invitations, create company if needed
        client_id = invitation.client_id

        if invitation.invitation_type == "client" and not client_id:
            # Create client company
            if not data.company_details:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Company details required for client invitation acceptance",
                )

            client = Client(
                company_name=invitation.company_name or data.company_details.company_name,
                company_registration_number=data.company_details.registration_number,
                email=data.company_details.company_email or invitation.email,
                phone_number=data.company_details.phone_number,
                address=data.company_details.address,
                contact_person_name=f"{data.first_name} {data.last_name}",
                contact_person_email=invitation.email,
                contact_person_phone=data.phone_number,
                is_active=True,
            )

            self.db.add(client)
            await self.db.flush()
            client_id = client.id

        # Create user account
        security = SecurityService()
        user_data = {
            "email": invitation.email,
            "hashed_password": security.get_password_hash(data.password),
            "first_name": data.first_name,
            "last_name": data.last_name,
            "phone_number": data.phone_number,
            "role": base_role,
            "client_id": client_id,
            "is_active": True,
            "is_verified": True,
        }

        user = await self.user_repo.create(user_data)

        # Assign role via junction table
        from sqlalchemy import insert

        from app.models.role import user_roles

        stmt = insert(user_roles).values(user_id=user.id, role_id=role.id)
        await self.db.execute(stmt)

        # Update invitation status
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.utcnow()

        # Enable 2FA after setup
        if data.phone_number:
            two_fa_service = TwoFactorService(self.db, self.redis)
            await two_fa_service.enable_2fa(user)

        await self.db.commit()
        await self.db.refresh(user)

        return {
            "user_id": user.id,
            "email": user.email,
            "role": base_role,
            "client_id": client_id,
            "message": "Account created successfully",
        }
