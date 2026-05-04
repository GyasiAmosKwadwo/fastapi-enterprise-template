from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    applicant_group_router,
    applications,
    auth,
    invitations,
    notifications,
    password,
    roles,
    service_requests,
    service_types,
    tasks,
    users,
)

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router)

api_router.include_router(password.router)

# Applications
api_router.include_router(applications.router)

# Applicant Groups
api_router.include_router(applicant_group_router.router)

# Roles & Permissions
api_router.include_router(roles.router)

# Invitations
api_router.include_router(invitations.router)

# service_types
api_router.include_router(service_types.router)

api_router.include_router(service_requests.router)

# Tasks
api_router.include_router(tasks.router)

# Notifications
api_router.include_router(notifications.router)

# Admin
api_router.include_router(admin.router)

# Users
api_router.include_router(users.router)
