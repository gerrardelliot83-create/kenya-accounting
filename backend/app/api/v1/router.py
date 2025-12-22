"""
API v1 Router

Main router for API version 1.
Includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.contacts import router as contacts_router
from app.api.v1.endpoints.items import router as items_router
from app.api.v1.endpoints.invoices import router as invoices_router
from app.api.v1.endpoints.payments import router as payments_router
from app.api.v1.endpoints.expenses import router as expenses_router
from app.api.v1.endpoints.bank_imports import router as bank_imports_router
from app.api.v1.endpoints.tax import router as tax_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.support import router as support_router
from app.api.v1.endpoints.admin_support import router as admin_support_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.onboarding import router as onboarding_router


# Create main v1 router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health_router,
    tags=["System"]
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

# Sprint 2 - Business Operations
api_router.include_router(
    contacts_router,
    prefix="/contacts",
    tags=["Contacts"]
)

api_router.include_router(
    items_router,
    prefix="/items",
    tags=["Items/Services"]
)

api_router.include_router(
    invoices_router,
    prefix="/invoices",
    tags=["Invoices"]
)

# Sprint 3 - Payment Recording
api_router.include_router(
    payments_router,
    prefix="/payments",
    tags=["Payments"]
)

api_router.include_router(
    expenses_router,
    prefix="/expenses",
    tags=["Expenses"]
)

# Sprint 4 - Bank Import & Reconciliation
api_router.include_router(
    bank_imports_router,
    prefix="/bank-imports",
    tags=["Bank Imports"]
)

# Sprint 5 - Tax & Reports
api_router.include_router(
    tax_router,
    prefix="/tax",
    tags=["Tax Compliance"]
)

api_router.include_router(
    reports_router,
    prefix="/reports",
    tags=["Financial Reports"]
)

# Sprint 5 - Support & Help Centre
api_router.include_router(
    support_router,
    prefix="/support",
    tags=["Support & Help"]
)

api_router.include_router(
    admin_support_router,
    prefix="/admin/support",
    tags=["Admin Support"]
)

# Sprint 6 - Admin Portal
api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Admin Portal"]
)

# Sprint 6 - Onboarding Portal
api_router.include_router(
    onboarding_router,
    prefix="/onboarding",
    tags=["Onboarding Portal"]
)
