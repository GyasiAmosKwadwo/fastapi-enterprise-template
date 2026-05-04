import asyncio
import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import AsyncSessionLocal
from app.models.role import Permission, Role
from app.models.user import User


async def seed_permissions(db: AsyncSession) -> list[Permission]:
    permissions_data = [
        {"name": "Create User", "code": "user.create", "module": "users"},
        {"name": "View User", "code": "user.view", "module": "users"},
        {"name": "Update User", "code": "user.update", "module": "users"},
        {"name": "Delete User", "code": "user.delete", "module": "users"},
        {"name": "Create Role", "code": "role.create", "module": "roles"},
        {"name": "View Role", "code": "role.view", "module": "roles"},
        {"name": "Update Role", "code": "role.update", "module": "roles"},
        {"name": "Delete Role", "code": "role.delete", "module": "roles"},
        {"name": "View Notifications", "code": "notification.view", "module": "notifications"},
        {"name": "Manage Notifications", "code": "notification.manage", "module": "notifications"},
        {"name": "View Audit Logs", "code": "audit.view", "module": "audit"},
    ]

    permissions: list[Permission] = []
    for perm_data in permissions_data:
        permission = Permission(**perm_data)
        db.add(permission)
        permissions.append(permission)

    await db.commit()
    logger.info(f"Created {len(permissions)} permissions")
    return permissions


async def seed_roles(db: AsyncSession, permissions: list[Permission]) -> None:
    super_admin_role = Role(
        name="Super Administrator",
        code="super_admin",
        description="Full system access",
        is_system_role=True,
        is_admin_role=True,
        is_active=True,
    )
    super_admin_role.permissions = permissions
    db.add(super_admin_role)
    await db.commit()

    result = await db.execute(select(User).where(User.email == "admin@example.com"))
    admin_user = result.scalar_one_or_none()
    if admin_user:
        admin_user.roles = [super_admin_role]
        await db.commit()
        logger.info("Assigned Super Admin role to admin user")


async def seed_permissions_and_roles() -> None:
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Seeding permissions and roles...")
            permissions = await seed_permissions(db)
            await seed_roles(db, permissions)
            logger.info("Permissions and roles seeded successfully")
        except Exception as e:
            logger.error(f"Error seeding permissions and roles: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_permissions_and_roles())
