#!/usr/bin/env python3
"""
Create Test User Script

This script creates test users for development and testing purposes.
It properly encrypts sensitive fields and hashes passwords.

Usage:
    python create_test_user.py

Security Note:
    This script is for DEVELOPMENT/TESTING only.
    Never use default passwords in production.
"""

import asyncio
from uuid import UUID

from app.services.user_service import UserService
from app.db.session import get_db_context
from app.models.user import UserRole


async def create_test_users():
    """Create test users for each role."""

    print("Creating test users...")
    print("-" * 60)

    users_to_create = [
        {
            "email": "admin@example.com",
            "password": "AdminPass123",
            "role": UserRole.SYSTEM_ADMIN,
            "first_name": "System",
            "last_name": "Admin",
            "phone": "+254712345001",
            "national_id": "12345001",
            "must_change_password": False,
        },
        {
            "email": "business@example.com",
            "password": "BusinessPass123",
            "role": UserRole.BUSINESS_ADMIN,
            "first_name": "Business",
            "last_name": "Owner",
            "phone": "+254712345002",
            "national_id": "12345002",
            "must_change_password": False,
        },
        {
            "email": "bookkeeper@example.com",
            "password": "BookkeeperPass123",
            "role": UserRole.BOOKKEEPER,
            "first_name": "Book",
            "last_name": "Keeper",
            "phone": "+254712345003",
            "national_id": "12345003",
            "must_change_password": False,
        },
        {
            "email": "onboarding@example.com",
            "password": "OnboardPass123",
            "role": UserRole.ONBOARDING_AGENT,
            "first_name": "Onboarding",
            "last_name": "Agent",
            "phone": "+254712345004",
            "national_id": "12345004",
            "must_change_password": False,
        },
        {
            "email": "support@example.com",
            "password": "SupportPass123",
            "role": UserRole.SUPPORT_AGENT,
            "first_name": "Support",
            "last_name": "Agent",
            "phone": "+254712345005",
            "national_id": "12345005",
            "must_change_password": False,
        },
    ]

    async with get_db_context() as db:
        user_service = UserService(db)

        for user_data in users_to_create:
            try:
                # Check if user already exists
                existing_user = await user_service.get_user_by_email(
                    user_data["email"]
                )

                if existing_user:
                    print(f"✗ User {user_data['email']} already exists (ID: {existing_user.id})")
                    continue

                # Create user
                user = await user_service.create_user(**user_data)

                print(f"✓ Created {user_data['role'].value}: {user_data['email']}")
                print(f"  ID: {user.id}")
                print(f"  Password: {user_data['password']}")
                print(f"  Name: {user_data['first_name']} {user_data['last_name']}")
                print()

            except Exception as e:
                print(f"✗ Error creating {user_data['email']}: {str(e)}")
                print()

    print("-" * 60)
    print("Test user creation completed!")
    print()
    print("You can now login with any of the created users:")
    print("  POST http://localhost:8000/api/v1/auth/login")
    print()
    print("Example:")
    print('  {"email": "admin@example.com", "password": "AdminPass123"}')
    print()


async def create_custom_user(
    email: str,
    password: str,
    role: str = "business_admin",
    first_name: str = "Test",
    last_name: str = "User"
):
    """
    Create a custom test user.

    Args:
        email: User email
        password: User password
        role: User role (default: business_admin)
        first_name: First name
        last_name: Last name
    """
    async with get_db_context() as db:
        user_service = UserService(db)

        # Validate role
        try:
            user_role = UserRole(role)
        except ValueError:
            print(f"Error: Invalid role '{role}'")
            print(f"Valid roles: {[r.value for r in UserRole]}")
            return

        try:
            # Check if user exists
            existing_user = await user_service.get_user_by_email(email)
            if existing_user:
                print(f"Error: User {email} already exists")
                return

            # Create user
            user = await user_service.create_user(
                email=email,
                password=password,
                role=user_role,
                first_name=first_name,
                last_name=last_name,
                must_change_password=False
            )

            print(f"✓ Created user: {email}")
            print(f"  ID: {user.id}")
            print(f"  Role: {role}")
            print(f"  Password: {password}")

        except Exception as e:
            print(f"Error creating user: {str(e)}")


def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        # Custom user creation from command line
        if sys.argv[1] == "--help":
            print("Usage:")
            print("  python create_test_user.py                    # Create default test users")
            print("  python create_test_user.py <email> <password> [role] [first_name] [last_name]")
            print()
            print("Roles:")
            for role in UserRole:
                print(f"  - {role.value}")
            return

        email = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else "TestPass123"
        role = sys.argv[3] if len(sys.argv) > 3 else "business_admin"
        first_name = sys.argv[4] if len(sys.argv) > 4 else "Test"
        last_name = sys.argv[5] if len(sys.argv) > 5 else "User"

        asyncio.run(create_custom_user(email, password, role, first_name, last_name))
    else:
        # Create default test users
        asyncio.run(create_test_users())


if __name__ == "__main__":
    main()
