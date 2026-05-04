import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import asyncio

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.role import Permission, Role, user_roles
from app.models.user import User


async def seed_permissions(db: AsyncSession):
    """Seed default permissions"""
    permissions_data = [
        # User permissions
        {"name": "Create User", "code": "user.create", "module": "users"},
        {"name": "View User", "code": "user.view", "module": "users"},
        {"name": "Update User", "code": "user.update", "module": "users"},
        {"name": "Delete User", "code": "user.delete", "module": "users"},
        {"name": "Invite User", "code": "user.invite", "module": "users"},
        # Role permissions
        {"name": "Create Role", "code": "role.create", "module": "roles"},
        {"name": "View Role", "code": "role.view", "module": "roles"},
        {"name": "Update Role", "code": "role.update", "module": "roles"},
        {"name": "Delete Role", "code": "role.delete", "module": "roles"},
        # Application permissions
        {"name": "Create Application", "code": "application.create", "module": "applications"},
        {"name": "View Application", "code": "application.view", "module": "applications"},
        {"name": "Update Application", "code": "application.update", "module": "applications"},
        {"name": "Delete Application", "code": "application.delete", "module": "applications"},
        {"name": "Submit Application", "code": "application.submit", "module": "applications"},
        # Task permissions
        {"name": "Create Task", "code": "task.create", "module": "tasks"},
        {"name": "View Task", "code": "task.view", "module": "tasks"},
        {"name": "Update Task", "code": "task.update", "module": "tasks"},
        {"name": "Assign Task", "code": "task.assign", "module": "tasks"},
        {"name": "Complete Task", "code": "task.complete", "module": "tasks"},
        # Report permissions
        {"name": "View Report", "code": "report.view", "module": "reports"},
        {"name": "Generate Report", "code": "report.generate", "module": "reports"},
        {"name": "Download Report", "code": "report.download", "module": "reports"},
        # Audit permissions
        {"name": "View Audit Logs", "code": "audit.view", "module": "audit"},
    ]

    permissions = []
    for perm_data in permissions_data:
        permission = Permission(**perm_data)
        db.add(permission)
        permissions.append(permission)

    await db.commit()
    logger.info(f"Created {len(permissions)} permissions")
    return permissions


async def seed_roles(db: AsyncSession, permissions: list):
    """Seed default roles"""
    from sqlalchemy import select

    # Super Admin Role
    super_admin_role = Role(
        name="Super Administrator",
        code="super_admin",
        description="Full system access",
        is_system_role=True,
        is_admin_role=True,
        is_active=True,
    )
    super_admin_role.permissions = permissions  # All permissions
    db.add(super_admin_role)

    # Financial Investigator Role
    financial_perms = [p for p in permissions if p.module in ["applications", "tasks", "reports"]]
    financial_role = Role(
        name="Financial Investigator",
        code="financial_investigator",
        description="Handles financial background checks",
        is_system_role=True,
        is_admin_role=True,
        is_active=True,
    )
    financial_role.permissions = financial_perms
    db.add(financial_role)

    # Employment Verifier Role
    employment_perms = [
        p
        for p in permissions
        if p.code in ["application.view", "task.view", "task.update", "task.complete"]
    ]
    employment_role = Role(
        name="Employment Verifier",
        code="employment_verifier",
        description="Verifies employment history",
        is_system_role=True,
        is_admin_role=True,
        is_active=True,
    )
    employment_role.permissions = employment_perms
    db.add(employment_role)

    # Client Role
    client_perms = [
        p
        for p in permissions
        if p.code
        in [
            "application.create",
            "application.view",
            "application.submit",
            "report.view",
            "report.download",
        ]
    ]
    client_role = Role(
        name="Client User",
        code="client_user",
        description="Client company user",
        is_system_role=True,
        is_client_role=True,
        is_active=True,
    )
    client_role.permissions = client_perms
    db.add(client_role)

    await db.commit()
    logger.info("Created default roles")

    # Assign super admin role to admin user
    result = await db.execute(select(User).where(User.email == "admin@bcci-system.com"))
    admin_user = result.scalar_one_or_none()

    if admin_user:
        admin_user.roles = [super_admin_role]
        await db.commit()
        logger.info("Assigned Super Admin role to admin user")


async def seed_permissions_and_roles():
    """Main seeding function"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Seeding permissions and roles...")

            permissions = await seed_permissions(db)
            await seed_roles(db, permissions)

            logger.info("Permissions and roles seeded successfully!")

        except Exception as e:
            logger.error(f"Error seeding permissions and roles: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_permissions_and_roles())
