#!/usr/bin/env python3
"""
Sprint 4 Migration Runner

This script runs the Sprint 4 database migration to create the bank_imports
and bank_transactions tables required for the bank import functionality.

Usage:
    python run_sprint4_migration.py

Prerequisites:
    - Database connection configured in .env
    - PostgreSQL database accessible
    - asyncpg and sqlalchemy installed
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings


async def run_migration():
    """Run the Sprint 4 database migration."""
    print("=" * 80)
    print("Sprint 4 Database Migration")
    print("=" * 80)
    print()

    # Check if migration file exists
    migration_file = Path(__file__).parent / "migrations" / "sprint4_create_tables.sql"
    if not migration_file.exists():
        print(f"❌ ERROR: Migration file not found: {migration_file}")
        sys.exit(1)

    print(f"✓ Migration file found: {migration_file}")
    print()

    # Read migration SQL
    with open(migration_file, 'r') as f:
        sql_content = f.read()

    print(f"✓ Migration SQL loaded ({len(sql_content)} characters)")
    print()

    # Connect to database
    print(f"→ Connecting to database...")
    print(f"  Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")

    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True
        )
        print("✓ Database connection established")
        print()
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to database")
        print(f"  {str(e)}")
        sys.exit(1)

    # Execute migration
    print("→ Running migration...")
    print()

    try:
        async with engine.begin() as conn:
            # Execute the entire SQL script
            await conn.execute(sql_content)
            await conn.commit()

        print("✓ Migration executed successfully")
        print()

    except Exception as e:
        print(f"❌ ERROR: Migration failed")
        print(f"  {str(e)}")
        print()
        print("This error may occur if:")
        print("  - Tables already exist (migration already run)")
        print("  - Database permissions are insufficient")
        print("  - SQL syntax error in migration file")
        print()
        await engine.dispose()
        sys.exit(1)

    # Verify migration
    print("→ Verifying migration...")
    print()

    try:
        async with engine.begin() as conn:
            # Check if bank_imports table exists
            result = await conn.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bank_imports')"
            )
            bank_imports_exists = result.scalar()

            # Check if bank_transactions table exists
            result = await conn.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bank_transactions')"
            )
            bank_transactions_exists = result.scalar()

            if bank_imports_exists and bank_transactions_exists:
                print("✓ Table 'bank_imports' created successfully")
                print("✓ Table 'bank_transactions' created successfully")
                print()

                # Check enum types
                result = await conn.execute(
                    "SELECT COUNT(*) FROM pg_type WHERE typname IN ('file_type_enum', 'import_status_enum', 'reconciliation_status_enum')"
                )
                enum_count = result.scalar()

                if enum_count == 3:
                    print("✓ All enum types created successfully")
                    print()

                # Check indexes
                result = await conn.execute(
                    "SELECT COUNT(*) FROM pg_indexes WHERE tablename IN ('bank_imports', 'bank_transactions')"
                )
                index_count = result.scalar()

                print(f"✓ Created {index_count} indexes for performance")
                print()

                # Check RLS policies
                result = await conn.execute(
                    "SELECT COUNT(*) FROM pg_policies WHERE tablename IN ('bank_imports', 'bank_transactions')"
                )
                policy_count = result.scalar()

                if policy_count >= 2:
                    print(f"✓ Row-level security policies enabled ({policy_count} policies)")
                    print()

                print("=" * 80)
                print("✅ MIGRATION COMPLETED SUCCESSFULLY")
                print("=" * 80)
                print()
                print("Next Steps:")
                print("  1. Start the backend server: uvicorn app.main:app --reload")
                print("  2. Run Sprint 4 tests: pytest tests/test_sprint4_api.py -v")
                print()

            else:
                print("❌ ERROR: Tables were not created properly")
                if not bank_imports_exists:
                    print("  - Missing: bank_imports table")
                if not bank_transactions_exists:
                    print("  - Missing: bank_transactions table")
                print()
                await engine.dispose()
                sys.exit(1)

    except Exception as e:
        print(f"❌ ERROR: Failed to verify migration")
        print(f"  {str(e)}")
        print()
        await engine.dispose()
        sys.exit(1)

    # Cleanup
    await engine.dispose()
    print("✓ Database connection closed")
    print()


def main():
    """Main entry point."""
    try:
        asyncio.run(run_migration())
    except KeyboardInterrupt:
        print()
        print("❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
