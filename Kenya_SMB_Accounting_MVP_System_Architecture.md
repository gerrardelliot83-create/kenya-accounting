

# **Kenya Small Business Accounting Application**

MVP System Architecture & Development Documentation

**Multi-Agent Development Framework for Claude Code**

Version 2.0 | December 2025

**CONFIDENTIAL**

# **PART 1: EXECUTIVE SUMMARY**

## **1.1 Document Purpose**

This document provides comprehensive system architecture, development guidelines, and multi-agent orchestration specifications for the Kenya Small Business Accounting Application MVP. It serves as the primary reference for Claude Code agents coordinating the development effort across a 7-person development team.

## **1.2 Project Overview**

The application is a lightweight, user-friendly accounting platform tailored for Kenyan small businesses. Key features include: sales/expense tracking, invoicing with PDF generation, bank statement reconciliation, VAT/TOT tax compliance, and comprehensive reporting. The system includes four distinct portals: Client Application, Admin Portal, Onboarding Portal, and Customer Support Portal.

## **1.3 Target Users**

| User Type | Description | Core Needs |
| ----- | ----- | ----- |
| Sole Proprietor | Non-accountant operating small business | Simple expense/sales tracking, invoicing |
| Small Bookkeeper | Manages accounts for 1-5 clients | Data import, reconciliation, VAT reports |
| Accountant | Uses app data for KRA filing | Exports, audit trails, tax summaries |
| Onboarding Agent | Internal team setting up businesses | Business creation wizard, user setup |
| Support Agent | Internal customer service team | Ticket management, limited data view |
| System Admin | Internal operations team | Full visibility, analytics, audit logs |

# **PART 2: SYSTEM ARCHITECTURE**

## **2.1 Technology Stack**

| Layer | Technologies |
| ----- | ----- |
| Frontend | React 18+ (Vite), TypeScript, Shadcn/UI, TailwindCSS, Zustand, React Query |
| Backend | FastAPI (Python 3.11+), Pydantic v2, SQLAlchemy 2.0, Alembic |
| Database | Supabase PostgreSQL 15+, Row Level Security (RLS), pgcrypto |
| Authentication | Supabase Auth (JWT), RBAC, Session Management |
| Storage | UploadThing (AES-256 encrypted), Supabase Storage |
| PDF Generation | WeasyPrint, xhtml2pdf via FastAPI routes |
| Caching | Redis (session management, rate limiting, query caching) |

## **2.2 High-Level Architecture**

┌─────────────────────────────────────────────────────────────────────┐

│                    PRESENTATION LAYER                               │

│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐    │

│  │ Client App │ │Admin Portal│ │ Onboarding │ │ Support Portal │    │

│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └───────┬────────┘    │

└────────┼──────────────┼──────────────┼────────────────┼─────────────┘

         └──────────────┴──────┬───────┴────────────────┘              

┌──────────────────────────────┴──────────────────────────────────────┐

│              API GATEWAY (HTTPS, Rate Limiting, JWT)                │

└──────────────────────────────┬──────────────────────────────────────┘

┌──────────────────────────────┴──────────────────────────────────────┐

│                      BACKEND SERVICES                               │

│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌───────────────────┐   │

│  │ FastAPI  │ │ Supabase │ │  Encryption  │ │   Reconciliation  │   │

│  │ Core API │ │   Auth   │ │   Service    │ │       Engine      │   │

│  └──────────┘ └──────────┘ └──────────────┘ └───────────────────┘   │

└──────────────────────────────┬──────────────────────────────────────┘

┌──────────────────────────────┴──────────────────────────────────────┐

│                        DATA LAYER                                   │

│  ┌────────────────┐ ┌────────────────┐ ┌────────────────────┐       │

│  │   PostgreSQL   │ │  UploadThing   │ │    Redis Cache     │       │

│  │  (Encrypted)   │ │  (Encrypted)   │ │ (Session/Rate)     │       │

│  └────────────────┘ └────────────────┘ └────────────────────┘       │

└─────────────────────────────────────────────────────────────────────┘

# **PART 3: SECURITY ARCHITECTURE**

## **3.1 Encryption Standards**

**Data at Rest:**

* Database: Supabase PostgreSQL with Transparent Data Encryption (TDE)  
* Sensitive Fields: AES-256-GCM application-level encryption  
* File Storage: UploadThing with server-side AES-256 encryption  
* Key Management: AWS KMS or HashiCorp Vault

**Data in Transit:**

* TLS 1.3 for all API communications  
* HSTS headers with minimum 1-year max-age  
* Certificate pinning for mobile applications

## **3.2 Encrypted Fields Configuration**

ENCRYPTED\_FIELDS \= {

    'business': \['kra\_pin', 'bank\_account\_number', 'tax\_certificate\_number'\],

    'contact': \['phone', 'email', 'kra\_pin'\],

    'user': \['phone\_number', 'national\_id'\],

    'payment': \['transaction\_reference', 'account\_details'\],

    'document': \['file\_content', 'ocr\_extracted\_data'\]

}

## **3.3 Authentication Architecture (Login-Only)**

The system implements login-only authentication. Accounts are pre-configured by the onboarding team. Users cannot self-register.

Authentication Flow:

1\. Onboarding Team creates business account via Admin Portal

2\. System generates secure temporary password

3\. Credentials delivered to business owner via secure channel

4\. User logs in and MUST change password on first login

5\. JWT token issued with role-based claims

## **3.4 Role-Based Access Control (RBAC)**

| Role | Portal Access | Permissions |
| ----- | ----- | ----- |
| business\_admin | Client App | Full access to own business data, user management |
| bookkeeper | Client App | Transaction entry, report viewing, limited settings |
| onboarding\_agent | Onboarding Portal | Create businesses, setup config, view onboarding queue |
| support\_agent | Support Portal | View tickets, respond to queries, limited business data view |
| system\_admin | Admin Portal | Full system access, analytics, audit logs, user management |

# **PART 4: DEVELOPMENT TEAM STRUCTURE**

## **4.1 Team Hierarchy**

                    ┌─────────────────────────┐

                    │      MAIN AGENT         │

                    │    (Orchestrator)       │

                    └───────────┬─────────────┘

           ┌───────────────────┼───────────────────┐

  ┌────────┴────────┐ ┌────────┴────────┐ ┌───────┴────────┐

  │ Senior Backend  │ │ Senior Frontend │ │   Automation   │

  │   Developer     │ │   Developer     │ │     Tester     │

  └────────┬────────┘ └────────┬────────┘ └────────────────┘

      ┌────┴────┐        ┌────┴────┐

  ┌───┴───┐ ┌───┴───┐┌───┴───┐ ┌───┴───┐

  │Backend│ │Backend││Frontend│ │Frontend│

  │ Dev 1 │ │ Dev 2 ││  Dev 1 │ │  Dev 2 │

  └───────┘ └───────┘└────────┘ └────────┘

## **4.2 Module Assignments**

| Agent | Modules Assigned | Key Deliverables |
| ----- | ----- | ----- |
| Senior Backend | Core Architecture, Security, Admin APIs | Database schema, encryption, auth system, API gateway |
| Senior Frontend | Admin Portal, Onboarding Portal, Support Portal | Admin dashboard, onboarding wizard, support portal UI |
| Backend Dev 1 | Invoices, Payments, Contacts, Items | CRUD APIs, PDF generation, eTIMS JSON export |
| Backend Dev 2 | Expenses, Bank Import, Tax, Reports | CSV parser, reconciliation engine, VAT/TOT, ledger |
| Frontend Dev 1 | Invoices, Contacts, Items, Dashboard | Invoice wizard, contact management, dashboard widgets |
| Frontend Dev 2 | Expenses, Bank Import, Tax, Reports, Help | Expense entry, CSV wizard, reports, help system |
| Automation Tester | All Modules | E2E tests, API tests, security tests, performance tests |

# **PART 5: MODULE SPECIFICATIONS**

## **5.1 Admin Portal (Senior Frontend \+ Senior Backend)**

Provides complete visibility into all registered businesses while respecting privacy. All sensitive data displayed in masked format unless explicitly authorized.

* Dashboard with key metrics: total businesses, active users, revenue, support tickets  
* Business directory with search, filter, and export capabilities  
* User activity monitoring and audit log viewer  
* System health monitoring and error tracking  
* Internal user management (onboarding agents, support agents)

## **5.2 Onboarding Portal (Senior Frontend \+ Senior Backend)**

Used exclusively by the field onboarding team to set up new business accounts.

1. Agent logs in with onboarding\_agent credentials  
2. Selects 'Create New Business' from dashboard  
3. Enters business details: name, owner, KRA PIN, contact info  
4. Configures VAT/TOT settings based on business eligibility  
5. Creates primary user account with temporary password  
6. Activates account and delivers credentials to business owner

## **5.3 Customer Support Portal (Senior Frontend \+ Senior Backend)**

Enables customer service agents to handle support tickets while maintaining data privacy.

* Ticket queue with priority-based sorting  
* Ticket detail view with full conversation history  
* Limited business data view (masked sensitive information)  
* Canned response templates for common issues  
* Escalation workflow and satisfaction survey management

## **5.4 Client Application Help & Support**

Every screen includes access to the help system:

* Contextual help tooltips on complex fields  
* Help center with searchable FAQs and guides  
* 'Submit Support Ticket' accessible from any screen  
* Ticket history and status tracking for users  
* In-app notifications for ticket updates

# **PART 6: COMPREHENSIVE REPORTS LIST**

## **6.1 Financial Reports**

| Report Name | Description | Export Formats |
| ----- | ----- | ----- |
| Profit & Loss Statement | Income vs expenses for period | PDF, CSV, Excel |
| Balance Sheet | Assets, liabilities, equity snapshot | PDF, CSV, Excel |
| Cash Flow Statement | Cash inflows and outflows | PDF, CSV |
| Trial Balance | All account balances verification | PDF, CSV, Excel |
| General Ledger | Complete transaction history by account | PDF, CSV, Excel |

## **6.2 Tax & Compliance Reports**

| Report Name | Description | Export Formats |
| ----- | ----- | ----- |
| VAT Summary Report | VAT output vs input, net payable | PDF, CSV, KRA Format |
| VAT Return (iTax) | Pre-formatted for KRA iTax upload | CSV (iTax format) |
| TOT Summary Report | Turnover tax calculation breakdown | PDF, CSV |
| eTIMS Sales Report | eTIMS-compliant invoice data | JSON (eTIMS format) |
| Tax Calendar | Upcoming tax filing deadlines | PDF, iCal |

## **6.3 Operational Reports**

| Report Name | Description | Export Formats |
| ----- | ----- | ----- |
| Aged Receivables | Outstanding invoices by age bracket | PDF, CSV, Excel |
| Aged Payables | Outstanding bills by age bracket | PDF, CSV, Excel |
| Sales by Customer | Revenue breakdown by customer | PDF, CSV |
| Sales by Item/Service | Revenue breakdown by product | PDF, CSV |
| Expense by Category | Expense breakdown by category | PDF, CSV |
| Expense by Vendor | Expense breakdown by vendor | PDF, CSV |
| Bank Reconciliation | Matched/unmatched transactions | PDF, CSV |
| Invoice Register | Complete invoice listing with status | PDF, CSV, Excel |
| Payment Register | All payments received/made | PDF, CSV |

## **6.4 Admin Reports (Internal Use Only)**

| Report Name | Description | Access Level |
| ----- | ----- | ----- |
| Business Activity Report | Login frequency, feature usage metrics | System Admin |
| Onboarding Report | New businesses by agent, region, period | System Admin, Onboarding Lead |
| Support Metrics Report | Ticket volume, resolution time, satisfaction | System Admin, Support Lead |
| Audit Log Report | Security events, data access logs | System Admin Only |
| System Health Report | API performance, error rates, uptime | System Admin Only |

# **PART 7: API SPECIFICATIONS**

## **7.1 API Design Standards**

* Base URL: /api/v1/  
* JSON request/response format with ISO 8601 dates  
* Pagination: ?page=1\&limit=20  
* Filtering: ?status=active\&created\_after=2024-01-01  
* Sorting: ?sort\_by=created\_at\&order=desc

## **7.2 Core API Endpoints**

**Authentication:**

POST /api/v1/auth/login, /refresh, /logout, /change-password

**Business & Contacts:**

GET|PUT /api/v1/business

GET|POST|PUT|DELETE /api/v1/contacts/{id}

GET|POST|PUT|DELETE /api/v1/items/{id}

**Invoices & Payments:**

GET|POST|PUT /api/v1/invoices/{id}

POST /api/v1/invoices/{id}/finalize

GET /api/v1/invoices/{id}/pdf, /api/v1/invoices/{id}/etims

GET|POST /api/v1/payments/{id}

**Expenses & Bank Import:**

GET|POST|PUT /api/v1/expenses/{id}

POST /api/v1/expenses/bulk-import

POST /api/v1/bank/upload, /map-columns, /reconcile

GET /api/v1/bank/transactions, /suggestions/{id}

**Reports & Tax:**

GET /api/v1/reports/profit-loss, /balance-sheet, /vat-summary, /tot-summary

GET /api/v1/reports/aged-receivables, /aged-payables

**Support:**

GET|POST /api/v1/support/tickets/{id}

POST /api/v1/support/tickets/{id}/messages

GET /api/v1/support/faq

# **PART 8: DEVELOPMENT SPRINT PLAN**

Six 2-week sprints covering all modules:

| Sprint | Focus | Primary Deliverables |
| ----- | ----- | ----- |
| Sprint 1 | Foundation & Auth | FastAPI structure, Supabase setup, encryption service, RBAC, React project setup |
| Sprint 2 | Invoices & Contacts | Contact/Item/Invoice CRUD APIs, PDF generation, Invoice wizard UI |
| Sprint 3 | Expenses & Onboarding | Expense API, receipt upload, payment recording, Onboarding Portal |
| Sprint 4 | Bank Import | CSV parser, column mapping, fuzzy matching, reconciliation UI |
| Sprint 5 | Tax & Reports | VAT/TOT calculation, all reports, Help center, Support Portal |
| Sprint 6 | Admin & QA | Admin Portal, analytics, audit logs, E2E testing, security testing |

# **PART 9: CLAUDE CODE SUB-AGENT CONFIGURATIONS**

## **9.1 Main Orchestrator Agent (CLAUDE.md)**

\# Kenya SMB Accounting MVP \- Main Orchestrator

\#\# Project Overview

Multi-agent development project for Kenya-focused accounting app.

\#\# Architecture

\- Frontend: React \+ Vite \+ TypeScript \+ Shadcn/UI

\- Backend: FastAPI \+ PostgreSQL \+ Supabase

\- Auth: Supabase Auth (JWT-based)

\#\# Sub-Agent Delegation Rules

1\. Backend architecture \-\> senior-backend-developer

2\. Frontend architecture \-\> senior-frontend-developer

3\. Invoice/Contact/Payment APIs \-\> backend-developer-1

4\. Expense/Bank/Tax APIs \-\> backend-developer-2

5\. Invoice/Contact/Dashboard UI \-\> frontend-developer-1

6\. Expense/Bank/Reports UI \-\> frontend-developer-2

7\. Testing tasks \-\> automation-tester

\#\# Security Requirements (MANDATORY)

\- All sensitive data MUST be encrypted (AES-256-GCM)

\- HTTPS/TLS 1.3 required for all communications

\- Row Level Security (RLS) on all tables

\- JWT validation on all protected routes

## **9.2 Senior Backend Developer**

*File: .claude/agents/senior-backend-developer.md*

\---

name: senior-backend-developer

description: MUST BE USED for core backend architecture, database schema,

  security implementation, encryption services, and reviewing backend code.

  Use PROACTIVELY for any security-related decisions.

tools: Read, Write, Edit, Bash, Grep, Glob

model: sonnet

\---

You are a Senior Backend Developer specializing in Python/FastAPI,

PostgreSQL, and secure system architecture.

\#\# Primary Responsibilities

1\. Core architecture and project structure

2\. Database schema design with Alembic migrations

3\. Encryption service (AES-256-GCM)

4\. Authentication and authorization (Supabase Auth, RBAC)

5\. Admin/Onboarding/Support Portal APIs

6\. Code review for Backend Developer 1 and 2

\#\# Security Standards (MANDATORY)

\- Encrypt: kra\_pin, bank\_account, phone, national\_id

\- Implement RLS policies on all tables

\- Validate all inputs using Pydantic

\- Log all security events to audit table

## **9.3 Senior Frontend Developer**

*File: .claude/agents/senior-frontend-developer.md*

\---

name: senior-frontend-developer

description: MUST BE USED for frontend architecture, Admin Portal,

  Onboarding Portal, Support Portal, and reviewing frontend code.

tools: Read, Write, Edit, Bash, Grep, Glob

model: sonnet

\---

You are a Senior Frontend Developer specializing in React, TypeScript.

\#\# Primary Responsibilities

1\. Frontend project architecture

2\. Admin Portal implementation

3\. Onboarding Portal implementation

4\. Customer Support Portal

5\. Component library and design system

6\. Code review for Frontend Developer 1 and 2

\#\# Security Standards

\- Never store sensitive data in localStorage

\- Use httpOnly cookies for auth tokens

\- Sanitize all user inputs

\- Mask sensitive data in UI

## **9.4 Backend Developer 1**

*File: .claude/agents/backend-developer-1.md*

\---

name: backend-developer-1

description: Use for Invoice, Contact, Item, Payment API implementations.

tools: Read, Write, Edit, Bash, Grep, Glob

model: sonnet

\---

\#\# Assigned Modules

1\. Contacts API (CRUD with encryption)

2\. Items/Services API

3\. Invoices API (CRUD, status workflow)

4\. Payments API

5\. PDF Generation (WeasyPrint)

6\. eTIMS JSON Export

\#\# Standards

\- Auto-generate invoice numbers: INV-{year}-{sequence}

\- Status flow: draft \-\> issued \-\> paid/cancelled

\- All code reviewed by senior-backend-developer

## **9.5 Backend Developer 2**

*File: .claude/agents/backend-developer-2.md*

\---

name: backend-developer-2

description: Use for Expense, Bank Import, Reconciliation, Tax, Reports.

tools: Read, Write, Edit, Bash, Grep, Glob

model: sonnet

\---

\#\# Assigned Modules

1\. Expenses API

2\. Bank Import API (CSV parsing)

3\. Reconciliation Engine (fuzzy matching)

4\. VAT/TOT Calculation Services

5\. Report Generation APIs

\#\# Kenya Tax Rules

\- VAT Rate: 16% (standard)

\- TOT Rate: 1% of gross turnover

\- VAT threshold: KES 5 million annual turnover

\- TOT eligibility: KES 1-50 million turnover

## **9.6 Frontend Developer 1**

*File: .claude/agents/frontend-developer-1.md*

\---

name: frontend-developer-1

description: Use for Invoice, Contact, Item, Dashboard UI.

tools: Read, Write, Edit, Bash, Grep, Glob

model: sonnet

\---

\#\# Assigned Features

1\. Contact Management UI (list, search, filters, edit forms)

2\. Items/Services UI (catalog, create/edit forms)

3\. Invoice Management UI (creation wizard, list, detail, PDF preview)

4\. Main Dashboard (widgets, activity feed, quick actions)

\#\# UI Standards

\- Use Shadcn/UI components

\- Implement loading skeletons

\- Handle error states gracefully

\- Mobile responsive design

## **9.7 Frontend Developer 2**

*File: .claude/agents/frontend-developer-2.md*

\---

name: frontend-developer-2

description: Use for Expense, Bank Import, Tax, Reports, Support UI.

tools: Read, Write, Edit, Bash, Grep, Glob

model: sonnet

\---

\#\# Assigned Features

1\. Expense Management UI (entry form, receipt upload, list)

2\. Bank Import UI (CSV wizard, column mapping, reconciliation)

3\. Tax Module UI (VAT/TOT summaries, filing guidance)

4\. Reports UI (selection, date range, export)

5\. Help & Support UI (FAQ, ticket submission, history)

## **9.8 Automation Tester**

*File: .claude/agents/automation-tester.md*

\---

name: automation-tester

description: Use PROACTIVELY for all testing tasks.

tools: Read, Write, Edit, Bash, Grep, Glob

model: sonnet

\---

\#\# Testing Responsibilities

1\. E2E Testing (Playwright) \- all critical user journeys

2\. API Testing (pytest) \- endpoint validation, auth testing

3\. Security Testing \- SQL injection, XSS, auth bypass

4\. Performance Testing (k6/locust) \- API benchmarks

\#\# Coverage Requirements

\- Unit tests: 80% coverage minimum

\- Integration tests: All API endpoints

\- E2E tests: All critical user journeys

# **PART 10: CODING STANDARDS**

## **10.1 Backend (Python/FastAPI)**

\# File naming: snake\_case (invoice\_service.py)

\# Class naming: PascalCase

\# Function naming: snake\_case

\# API Routes: kebab-case (/invoices/{id}/mark-paid)

\# Always use Pydantic for request/response

class InvoiceCreate(BaseModel):

    customer\_id: UUID

    items: list\[InvoiceItemCreate\]

## **10.2 Frontend (React/TypeScript)**

// File naming: PascalCase for components (InvoiceForm.tsx)

// Use React Query for API calls

// Use Zustand for global state

export function InvoiceForm({ onSubmit }: InvoiceFormProps) {

  const \[formData, setFormData\] \= useState\<InvoiceFormData\>();

  return \<form\>...\</form\>;

}

## **10.3 Git Workflow**

\# Branch naming

feature/invoice-creation

bugfix/vat-calculation-error

hotfix/security-patch

\# Commit format: type(scope): description

feat(invoice): add PDF generation

fix(auth): resolve token refresh issue

**\--- END OF DOCUMENT \---**