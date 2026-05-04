from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Applicant
from app.repositories.applicant_group_repository import ApplicantGroupRepository
from app.schemas.applicant_group import ApplicantGroupCreate, ApplicantGroupUpdate


class ApplicantGroupService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ApplicantGroupRepository(db)

    async def create_group(self, data: ApplicantGroupCreate, client_id: str):
        # Ensure unique name under same client (optional)
        groups = await self.repo.get_by_client(client_id)
        if any(g.name.lower() == data.name.lower() for g in groups):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group with this name already exists",
            )
        return await self.repo.create({"name": data.name, "client_id": client_id})

    async def add_applicant_to_group(self, group_id: str, applicant_id: str, client_id: str):
        group = await self.repo.get_by_id_and_client(group_id, client_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        applicant = await self.db.get(Applicant, applicant_id)
        if not applicant or str(applicant.client_id) != str(client_id):
            raise HTTPException(status_code=404, detail="Applicant not found for this client")

        await self.repo.add_applicant_to_group(group_id, applicant_id)
        return {"detail": "Applicant added successfully"}

    async def remove_applicant_from_group(self, group_id: str, applicant_id: str, client_id: str):
        group = await self.repo.get_by_id_and_client(group_id, client_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        await self.repo.remove_applicant_from_group(group_id, applicant_id)
        return {"detail": "Applicant removed successfully"}

    async def list_groups(self, client_id: str):
        return await self.repo.get_by_client(client_id)

    async def list_applicants_in_group(self, group_id: str, client_id: str):
        group = await self.repo.get_by_id_and_client(group_id, client_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return await self.repo.list_applicants_in_group(group_id)

    async def delete_group(self, group_id: str, client_id: str):
        group = await self.repo.get_by_id_and_client(group_id, client_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        await self.repo.delete(group_id)
        return {"detail": "Group deleted successfully"}
