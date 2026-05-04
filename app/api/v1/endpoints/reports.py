from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.report import Report, ReportSection, SectionChallenge
from app.models.user import User
from app.schemas.service_request import (
    ReportCreate,
    SectionChallengeCreate,
    SectionChallengeResponse,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_report(
    data: ReportCreate,
    current_user: User = Depends(require_permission("report.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create report with sections (Admin only)"""
    # Create report
    report = Report(
        service_request_id=data.service_request_id,
        applicant_id=data.applicant_id,
        executive_summary=data.executive_summary,
        current_version=1,
    )

    db.add(report)
    await db.flush()

    # Create sections
    for section_data in data.sections:
        section = ReportSection(report_id=report.id, **section_data.dict())
        db.add(section)

    # Create initial version
    from app.models.report import ReportVersion

    version = ReportVersion(
        report_id=report.id,
        number=1,
        created_by_id=current_user.id,
        changes_summary="Initial report",
    )
    db.add(version)

    await db.commit()
    await db.refresh(report)

    return {"message": "Report created successfully", "report_id": str(report.id)}


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get report with all sections"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .options(selectinload(Report.sections), selectinload(Report.versions))
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Check authorization
    # TODO: Add proper authorization checks

    return report


@router.post("/sections/{section_id}/challenge", response_model=SectionChallengeResponse)
async def challenge_section(
    section_id: str,
    data: SectionChallengeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Applicant challenges a report section"""
    section = await db.get(ReportSection, section_id)

    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    # Create challenge
    challenge = SectionChallenge(
        section_id=section_id,
        applicant_id=current_user.id,  # Assuming user is applicant
        reason=data.reason,
        supporting_docs=data.supporting_docs,
        status="pending",
    )

    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)

    # Notify admins
    # TODO: Send notification to admins

    return challenge


@router.get("/sections/{section_id}/challenges", response_model=List[SectionChallengeResponse])
async def list_section_challenges(
    section_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all challenges for a section"""
    from sqlalchemy import select

    result = await db.execute(
        select(SectionChallenge)
        .where(SectionChallenge.section_id == section_id)
        .order_by(SectionChallenge.created_at.desc())
    )

    return result.scalars().all()


@router.patch("/challenges/{challenge_id}")
async def respond_to_challenge(
    challenge_id: str,
    admin_response: str,
    resolve_status: str,
    current_user: User = Depends(require_permission("report.update")),
    db: AsyncSession = Depends(get_db),
):
    """Admin responds to section challenge"""
    challenge = await db.get(SectionChallenge, challenge_id)

    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    challenge.admin_response = admin_response
    challenge.status = resolve_status
    challenge.resolved_at = datetime.utcnow()
    challenge.resolved_by_id = current_user.id

    await db.commit()
    await db.refresh(challenge)

    # Notify applicant
    # TODO: Send notification to applicant

    return {"message": "Challenge updated successfully"}
