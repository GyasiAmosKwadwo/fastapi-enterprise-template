import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Applicant, ApplicantGroup
from app.models.notification import Notification, NotificationPriority, NotificationType
from app.models.service_request import (
    ConsentStatus,
    ServiceRequest,
    ServiceRequestNotification,
    ServiceRequestStatus,
    ServiceType,
)
from app.models.vettingForm import (
    EducationalBg,
    EmploymentHistory,
    MaritalStatus,
    PersonalDetails,
    VettingForm,
)
from app.schemas.service_request import ServiceRequestCreate, VettingFormSubmit
from app.services.email_service import EmailService


class ServiceRequestService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_service = EmailService()

    def _generate_reference_number(self) -> str:
        """Generate unique reference number"""
        prefix = "SR"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_suffix = secrets.token_hex(4).upper()
        return f"{prefix}-{timestamp}-{random_suffix}"

    async def create_service_request(
        self,
        data: ServiceRequestCreate,
        client_id: uuid.UUID,  # Changed type to UUID
        created_by_id: uuid.UUID,
    ) -> ServiceRequest:
        """Create service request and notify applicants"""
        # Verify service type exists
        service_type = await self.db.get(ServiceType, data.service_type_id)
        if not service_type or not service_type.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Service type not found or inactive"
            )

        # Get all applicants (from both direct IDs and groups)
        applicants = []

        # Direct applicant IDs
        if data.applicant_ids:
            result = await self.db.execute(
                select(Applicant).where(
                    and_(Applicant.id.in_(data.applicant_ids), Applicant.client_id == client_id)
                )
            )
            applicants.extend(result.scalars().all())

        # Applicants from groups
        if data.applicant_group_ids:
            result = await self.db.execute(
                select(ApplicantGroup)
                .options(selectinload(ApplicantGroup.applicants))
                .where(
                    and_(
                        ApplicantGroup.id.in_(data.applicant_group_ids),
                        ApplicantGroup.client_id == client_id,
                    )
                )
            )
            groups = result.scalars().all()
            for group in groups:
                applicants.extend(group.applicants)

        if not applicants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No valid applicants found"
            )

        # Remove duplicates
        unique_applicants = {app.id: app for app in applicants}.values()

        # Create service request
        service_request = ServiceRequest(
            reference_number=self._generate_reference_number(),
            client_id=client_id,
            service_type_id=data.service_type_id,
            created_by_id=created_by_id,
            status=ServiceRequestStatus.PENDING_APPLICANT,
            notes=data.notes,
            expires_at=datetime.now(timezone.utc) + timedelta(days=data.expires_in_days),
        )

        # Add applicants
        service_request.applicants = list(unique_applicants)

        self.db.add(service_request)
        await self.db.flush()
        await self.db.refresh(service_request)

        # Send email invitations to each applicant
        for applicant in unique_applicants:
            await self._send_form_invitation_email(service_request, applicant)

            # Create notification record
            notification = ServiceRequestNotification(
                service_request_id=service_request.id,
                applicant_id=applicant.id,
                notification_type="form_invitation",
            )
            self.db.add(notification)

        await self.db.commit()
        await self.db.refresh(service_request)

        return service_request

    async def _send_form_invitation_email(
        self, service_request: ServiceRequest, applicant: Applicant
    ):
        """Send form invitation email to applicant"""
        self.email_service.send_vetting_form_invitation_email(
            to_email=applicant.email,
            applicant_name=applicant.full_name,
            service_type_name=service_request.service_type.name,
            reference_number=service_request.reference_number,
            service_request_id=str(service_request.id),
            expires_at=service_request.expires_at,
            applicant_id=str(applicant.id),
        )

    async def submit_vetting_form(
        self, service_request_id: str, applicant_id: str, data: VettingFormSubmit, ip_address: str
    ) -> ServiceRequest:
        """Applicant submits vetting form"""
        result = await self.db.execute(
            select(ServiceRequest)
            .options(
                selectinload(ServiceRequest.created_by)
            )  # Eagerly load the user who created the request
            .options(selectinload(ServiceRequest.client))  # Eagerly load the client relationship
            .options(selectinload(ServiceRequest.applicants))
            .where(ServiceRequest.id == service_request_id)
        )
        service_request = result.scalar_one_or_none()

        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found"
            )

        # Verify applicant is part of this request
        submitting_applicant = next(
            (app for app in service_request.applicants if str(app.id) == applicant_id), None
        )
        if not submitting_applicant:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        if service_request.expires_at and service_request.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Service request has expired"
            )

        # Update service request
        # service_request.vetting_form_data = jsonable_encoder(data) # We will now save to separate tables
        # Create a new VettingForm instance
        new_vetting_form = VettingForm()
        self.db.add(new_vetting_form)
        await self.db.flush()  # To get the ID of the new_vetting_form

        # Link the new VettingForm to the Applicant
        submitting_applicant.vetting_form_id = new_vetting_form.id
        self.db.add(submitting_applicant)  # Mark for update

        service_request.vetting_form_submitted_at = datetime.now(timezone.utc)
        service_request.consent_status = ConsentStatus.ACCEPTED
        service_request.consent_accepted_at = datetime.now(timezone.utc)
        service_request.consent_ip_address = ip_address  # This is fine
        service_request.status = ServiceRequestStatus.SUBMITTED

        # 🔔 Create notification for client
        self._add_client_notification_to_session(service_request)

        # Save form data to respective tables
        if data.personal_details:
            personal_details = PersonalDetails(
                **data.personal_details.dict(), vetting_form_id=new_vetting_form.id
            )
            self.db.add(personal_details)
        if data.marital_status:
            marital_status = MaritalStatus(
                **data.marital_status.dict(), vetting_form_id=new_vetting_form.id
            )
            self.db.add(marital_status)
        if data.education_bg:
            for edu_item in data.education_bg:
                education_bg = EducationalBg(**edu_item.dict(), vetting_form_id=new_vetting_form.id)
                self.db.add(education_bg)
        if data.employment_history:
            for emp_item in data.employment_history:
                employment_history = EmploymentHistory(
                    **emp_item.dict(), vetting_form_id=new_vetting_form.id
                )
                self.db.add(employment_history)

        await self.db.commit()  # Commit both service_request changes and the new notification
        await self.db.refresh(service_request)

        return service_request

    async def forward_to_admin(
        self, service_request_id: uuid.UUID, client_id: uuid.UUID, user_id: uuid.UUID
    ) -> ServiceRequest:
        """Client forwards request to admin for background check"""
        service_request = await self.db.get(ServiceRequest, service_request_id)

        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found"
            )

        # Verify client owns this request
        if str(service_request.client_id) != client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        # Verify status
        if service_request.status != ServiceRequestStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service request must be submitted before forwarding",
            )

        # Update status
        service_request.status = ServiceRequestStatus.FORWARDED
        service_request.submitted_to_admin_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(service_request)

        # Send notification to admins
        await self._notify_admins_of_new_request(service_request)

        return service_request

    async def _notify_admins_of_new_request(self, service_request: ServiceRequest):
        """Notify all admins of new service request"""
        from sqlalchemy import select

        from app.models.user import User
        from app.services.notification_service import NotificationService

        # Get all admin users
        result = await self.db.execute(select(User.id).where(User.role == "administrator"))
        admin_ids = [row[0] for row in result.all()]

        # Create notifications
        notification_service = NotificationService(self.db)
        for admin_id in admin_ids:
            from app.models.notification import NotificationPriority, NotificationType
            from app.schemas.notification import NotificationCreate

            await notification_service.create_notification(
                NotificationCreate(
                    user_id=admin_id,
                    type=NotificationType.APPLICATION_SUBMITTED,
                    priority=NotificationPriority.HIGH,
                    title="New Background Check Request",
                    message=f"Service request {service_request.reference_number} has been forwarded for processing.",
                    resource_type="service_request",
                    resource_id=str(service_request.id),
                    action_url=f"/service-requests/{service_request.id}",
                )
            )

    def _add_client_notification_to_session(self, service_request):
        # This method is no longer async and does not commit.
        # It prepares the notification and adds it to the session.
        """Send a notification to the client when a vetting form is submitted."""
        client_user = (
            service_request.created_by
        )  # The notification should go to the user who created the service request.

        if not client_user:
            return  # no recipient

        notification = Notification(
            id=uuid.uuid4(),
            user_id=client_user.id,
            type=NotificationType.APPLICATION_SUBMITTED,
            priority=NotificationPriority.MEDIUM,
            title="Vetting Form Submitted",
            message=f"The vetting form for request {service_request.reference_number} has been submitted successfully.",
            resource_type="service_request",
            resource_id=service_request.id,
            action_url=f"/dashboard/requests/{service_request.id}",
            data={
                "reference_number": service_request.reference_number,
                "status": service_request.status,
            },
            created_at=datetime.utcnow().replace(tzinfo=timezone.utc),
        )

        self.db.add(notification)
