import asyncio

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import SecurityService
from app.models.client import Client
from app.models.user import User, UserRole


async def create_admin_user(db: AsyncSession) -> User:
    """Create default admin user"""
    security = SecurityService()

    admin = User(
        email="admin@bcci-system.com",
        hashed_password=security.get_password_hash("Admin@123"),
        first_name="System",
        last_name="Administrator",
        role=UserRole.ADMINISTRATOR,
        is_active=True,
        is_verified=True,
        two_factor_enabled=False,
    )

    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    logger.info(f"Created admin user: {admin.email}")
    return admin


async def create_demo_client(db: AsyncSession) -> Client:
    """Create demo client company"""
    client = Client(
        company_name="Demo Company Ltd",
        company_registration_number="REG-123456",
        email="contact@democompany.com",
        phone_number="+233244000000",
        address="123 Business District, Accra, Ghana",
        contact_person_name="John Doe",
        contact_person_email="john.doe@democompany.com",
        contact_person_phone="+233244000001",
        is_active=True,
        subscription_tier="premium",
    )

    db.add(client)
    await db.commit()
    await db.refresh(client)

    logger.info(f"Created demo client: {client.company_name}")
    return client


async def create_demo_users(db: AsyncSession, client: Client) -> None:
    """Create demo users"""
    security = SecurityService()

    # Client user
    client_user = User(
        email="client@democompany.com",
        hashed_password=security.get_password_hash("Client@123"),
        first_name="Jane",
        last_name="Smith",
        phone_number="+233244000002",
        role=UserRole.CLIENT,
        client_id=client.id,
        is_active=True,
        is_verified=True,
    )

    # Applicant user
    applicant_user = User(
        email="applicant@example.com",
        hashed_password=security.get_password_hash("Applicant@123"),
        first_name="Alice",
        last_name="Johnson",
        phone_number="+233244000003",
        role=UserRole.APPLICANT,
        client_id=client.id,
        is_active=True,
        is_verified=True,
    )

    db.add_all([client_user, applicant_user])
    await db.commit()

    logger.info("Created demo users")


async def seed_database():
    """Main seeding function"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if data already exists
            result = await db.execute("SELECT COUNT(*) FROM users WHERE role = 'administrator'")
            count = result.scalar()

            if count > 0:
                logger.info("Database already seeded. Skipping...")
                return

            # Create data
            logger.info("Starting database seeding...")

            admin = await create_admin_user(db)
            client = await create_demo_client(db)
            await create_demo_users(db, client)

            logger.info("Database seeded successfully!")
            logger.info("=" * 50)
            logger.info("Default Admin Credentials:")
            logger.info("Email: admin@bcci-system.com")
            logger.info("Password: Admin@123")
            logger.info("=" * 50)
            logger.info("Demo Client Credentials:")
            logger.info("Email: client@democompany.com")
            logger.info("Password: Client@123")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
