"""
Backend Setup Verification Script

Run this script to verify the backend setup is correct.
Usage: python verify_setup.py
"""

import sys
import os
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists."""
    if Path(file_path).exists():
        print(f"✓ {description}")
        return True
    else:
        print(f"✗ {description} - NOT FOUND")
        return False


def check_env_var(var_name: str) -> bool:
    """Check if environment variable is set."""
    if os.getenv(var_name):
        print(f"✓ Environment variable: {var_name}")
        return True
    else:
        print(f"✗ Environment variable: {var_name} - NOT SET")
        return False


def main():
    """Run verification checks."""
    print("=" * 60)
    print("Kenya SMB Accounting MVP - Backend Setup Verification")
    print("=" * 60)
    print()

    checks_passed = 0
    checks_failed = 0

    # Check Python version
    print("Checking Python version...")
    if sys.version_info >= (3, 11):
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
        checks_passed += 1
    else:
        print(f"✗ Python version too old. Required: 3.11+, Found: {sys.version}")
        checks_failed += 1
    print()

    # Check critical files
    print("Checking critical files...")
    critical_files = [
        ("app/main.py", "FastAPI application"),
        ("app/config.py", "Configuration module"),
        ("app/core/encryption.py", "Encryption service"),
        ("app/core/security.py", "Security module"),
        ("app/db/session.py", "Database session"),
        ("app/models/user.py", "User model"),
        ("app/models/business.py", "Business model"),
        ("app/models/audit_log.py", "Audit log model"),
        ("requirements.txt", "Dependencies file"),
        ("alembic.ini", "Alembic configuration"),
        (".env", "Environment file"),
    ]

    for file_path, description in critical_files:
        if check_file_exists(file_path, description):
            checks_passed += 1
        else:
            checks_failed += 1
    print()

    # Check if .env file has required variables
    print("Checking environment variables...")
    try:
        from dotenv import load_dotenv
        load_dotenv()

        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "DATABASE_URL",
            "JWT_SECRET_KEY",
            "ENCRYPTION_KEY",
        ]

        for var in required_vars:
            if check_env_var(var):
                checks_passed += 1
            else:
                checks_failed += 1
    except ImportError:
        print("✗ python-dotenv not installed. Run: pip install -r requirements.txt")
        checks_failed += len(required_vars)
    print()

    # Check if dependencies are installed
    print("Checking Python packages...")
    packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "pydantic",
        "pydantic_settings",
        "cryptography",
        "jose",
        "passlib",
    ]

    for package in packages:
        try:
            __import__(package)
            print(f"✓ Package installed: {package}")
            checks_passed += 1
        except ImportError:
            print(f"✗ Package missing: {package}")
            checks_failed += 1
    print()

    # Check encryption key strength
    print("Checking encryption key strength...")
    encryption_key = os.getenv("ENCRYPTION_KEY", "")
    if len(encryption_key) >= 32:
        print(f"✓ Encryption key is strong ({len(encryption_key)} characters)")
        checks_passed += 1
    else:
        print(f"✗ Encryption key is too short ({len(encryption_key)} characters). Required: 32+")
        checks_failed += 1
    print()

    # Summary
    print("=" * 60)
    print("Verification Summary")
    print("=" * 60)
    print(f"Checks passed: {checks_passed}")
    print(f"Checks failed: {checks_failed}")
    print()

    if checks_failed == 0:
        print("✓ All checks passed! Backend setup is complete.")
        print()
        print("Next steps:")
        print("1. Update DATABASE_URL in .env with your Supabase password")
        print("2. Run migrations: alembic upgrade head")
        print("3. Start server: uvicorn app.main:app --reload")
        return 0
    else:
        print("✗ Some checks failed. Please review the errors above.")
        print()
        print("Common fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Copy .env.example to .env and fill in values")
        print("3. Generate encryption key: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        return 1


if __name__ == "__main__":
    sys.exit(main())
