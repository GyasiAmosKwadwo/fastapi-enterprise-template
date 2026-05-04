from typing import Optional

from fastapi import HTTPException, status

from app.models.application import Applicant
from app.models.user import UserRole
from app.repositories.applicant_repository import ApplicantRepository


class ApplicantService:
    def __init__(self, db):
        self.db = db
        self.repo = ApplicantRepository(db)

    def verify_client_role(self, user):
        if user.role != UserRole.CLIENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only clients can perform this action"
            )

    async def create_applicant(self, data, current_user):
        self.verify_client_role(current_user)
        new_applicant = await self.repo.create(
            {
                "client_id": current_user.client_id,
                "full_name": data.full_name,
                "email": data.email,
                "validation_status": "pending",
                "vetting_form_id": data.vetting_form_id,
            }
        )
        return new_applicant

    async def update_applicant(self, applicant_id, data, current_user):
        self.verify_client_role(current_user)
        return await self.repo.update(applicant_id, data.dict(exclude_unset=True))

    async def delete_applicant(self, applicant_id, current_user):
        self.verify_client_role(current_user)
        await self.repo.delete(applicant_id)

    async def get_applicant_by_id(self, applicant_id, current_user):
        self.verify_client_role(current_user)
        return await self.repo.get_by_id(applicant_id)

    async def get_all_applicants_by_client(
        self, current_user, page: int, per_page: int, search: Optional[str] = None
    ):
        self.verify_client_role(current_user)

        applicants, total = await self.repo.get_by_client(
            client_id=current_user.client_id, page=page, per_page=per_page, search=search
        )

        return {
            "data": applicants,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
            },
        }
