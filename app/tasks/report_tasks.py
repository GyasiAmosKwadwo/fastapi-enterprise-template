from celery import group

from app.tasks.celery_app import celery_app
from app.tasks.integration_tasks import (
    check_credit_history,
    check_ghana_card,
    geocode_addresses,
    verify_education,
    verify_employment,
)


@celery_app.task(bind=True, name="process_background_checks")
def process_background_checks(self, application_id: int):
    """
    Process all background checks for an application
    """
    # Create task group for parallel execution
    job = group(
        check_ghana_card.s(application_id),
        check_credit_history.s(application_id),
        geocode_addresses.s(application_id),
        verify_employment.s(application_id),
        verify_education.s(application_id),
    )

    # Execute tasks
    result = job.apply_async()

    # Update task progress
    self.update_state(
        state="PROGRESS",
        meta={"application_id": application_id, "message": "Running background checks"},
    )

    return {"application_id": application_id, "status": "processing", "task_id": result.id}


@celery_app.task(name="generate_report")
def generate_report(application_id: int):
    """
    Generate final BCCI report
    """
    # TODO: Implement report generation logic
    return {"application_id": application_id, "status": "completed"}
