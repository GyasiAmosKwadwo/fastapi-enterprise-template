import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.repositories.application_repository import ApplicationRepository
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.services.notification_service import NotificationService
from app.tasks.report_tasks import process_background_checks


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.app_repo = ApplicationRepository(db)

    def _generate_reference_number(self) -> str:
        """Generate unique reference number"""
        prefix = "BCCI"
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = secrets.token_hex(4).upper()
        return f"{prefix}-{timestamp}-{random_suffix}"

    async def create_application(
        self, data: ApplicationCreate, applicant_id: int, client_id: int
    ) -> Application:
        """Create new background check application"""
        reference_number = self._generate_reference_number()

        application_data = {
            "reference_number": reference_number,
            "applicant_id": applicant_id,
            "client_id": client_id,
            "date_of_birth": data.date_of_birth,
            "ghana_card_number": data.ghana_card_number,
            "permanent_address": data.permanent_address,
            "current_address": data.current_address,
            "employment_history": [record.dict() for record in data.employment_history],
            "education_history": [record.dict() for record in data.education_history],
            "client_instructions": data.client_instructions,
            "status": ApplicationStatus.DRAFT,
        }

        application = await self.app_repo.create(application_data)
        return application

    async def submit_application_with_notification(self, application_id: int) -> Application:
        """Submit application for processing"""
        application = await self.app_repo.get_by_id(application_id)

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )

        if application.status != ApplicationStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Application already submitted"
            )

        # Update status
        application = await self.app_repo.update(
            application_id,
            {"status": ApplicationStatus.SUBMITTED, "submitted_at": datetime.utcnow()},
        )

        # Get all admin users to notify
        from sqlalchemy import select

        from app.models.user import User

        result = await self.db.execute(select(User.id).where(User.role == "administrator"))
        admin_ids = [row[0] for row in result.all()]

        # Send notifications to admins
        notification_service = NotificationService(self.db)
        await notification_service.create_application_submitted_notification(application, admin_ids)

        # Trigger background checks asynchronously
        process_background_checks.delay(application_id)

        return application

    async def assign_to_investigator(
        self, application_id: int, investigator_id: int
    ) -> Application:
        """Assign application to investigator"""
        application = await self.app_repo.update(
            application_id,
            {"assigned_to_id": investigator_id, "status": ApplicationStatus.IN_PROGRESS},
        )

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )

        return application
