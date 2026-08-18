# XYZ AI — Human-Like School Assistant
### Production-Grade, Full-Stack, Server-Side-Only School ERP Assistant

[![Python](https://img.shields.io/badge/Python-3.11%2B%20%7C%203.13-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red.svg)](https://sqlalchemy.org)
[![Tests](https://img.shields.io/badge/Tests-63%2F63%20Passing-brightgreen.svg)](#-automated-test-suite-63--63-passing)
[![Security](https://img.shields.io/badge/RBAC-Server--Enforced-success.svg)](#-security--rbac-boundary-matrix)
[![Auth](https://img.shields.io/badge/Auth-bcrypt%20Multi--User-blue.svg)](#-authentication--self-service-registration)
[![Database](https://img.shields.io/badge/Postgres-Supabase%20Ready-3ECF8E.svg)](#-database--production-supabase-setup)

---

## 📌 Executive Summary

**XYZ AI School Assistant** is an enterprise AI companion for K-12 school ERP ecosystems. Built with a **defense-in-depth, server-side-only architecture**, every claim, calculation, and action is backed by deterministic SQL database operations and strict application-layer authorization checks.

The system features:
- **Design System ("Warm Academic Humanism")**: Soft cream surfaces, warm navy typography (Quicksand + Inter), role-specific accent identities (Student Warm Orange, Parent Soft Green, Teacher Approachable Blue, Principal Warm Navy), and Chart.js visualizations.
- **Real Multi-User Auth & Registration**: Bcrypt password hashing with per-user dynamic salting, self-service registration (`/register`) with RBAC boundaries (Principal blocked from self-registration, Teachers require approval).
- **Production Postgres (Supabase)**: Serverless-compatible session pooler connection handling, alongside zero-config local SQLite fallback.
- **Natural Language & Intent Understanding**: Context-aware distinction between greetings, academic/homework assistance, missing parameter disambiguation, escalation requests, and attendance queries.
- **Native 11 Indian Language Support**: Seamless real-time localized synthesis across Hindi (`hi`), Tamil (`ta`), Bengali (`bn`), English (`en`), and other major Indian languages.
- **Two-Stage Escalation State Machine**: Creates `PENDING` tickets with a mandatory confirmation gate before dispatching to teachers or management.
- **Application-Layer RBAC**: 100% server-enforced role and scope boundaries (students see only their own data; parents access only linked children; teachers access only assigned classes).
- **Interactive UI with Canvas Avatar & Voice**: Clean, warm, light design system with a 60fps Canvas avatar with viseme lip-sync, browser-native Web Speech STT/TTS, role dashboards, and a dedicated Staff Security Console.

---

## 🏛️ System Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │               Client Layer (Single Page App)            │
                    │   • Warm & Calm 2-Column Responsive Interface          │
                    │   • Web Speech STT / Browser SpeechSynthesis           │
                    │   • 60fps Canvas Avatar (Eyelid Blink + Mouth Visemes) │
                    │   • Real-Time Role Dashboards (Student/Parent/Staff)   │
                    └───────────────────────────┬────────────────────────────┘
                                                │ REST / JSON (Signed Bearer JWT)
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │                 FastAPI Gateway & Security              │
                    │   • Cryptographic JWT Verification & Claim Enforcement │
                    │   • Sliding-Window Rate Limiter (60 RPM)               │
                    │   • Multi-Vector Prompt Injection & Jailbreak Defense  │
                    │   • Sensitive Secret & Credential Redaction Masking    │
                    └───────────────────────────┬────────────────────────────┘
                                                │
         ┌──────────────────────────────────────┼──────────────────────────────────────┐
         │                                      │                                      │
┌────────▼────────┐                 ┌───────────▼───────────┐               ┌──────────▼─────────┐
│   Auth & RBAC   │                 │  Conversation Engine  │               │ Escalation Service │
│   Service       │                 │  • Multi-turn Memory  │               │ • State Machine    │
│  • Signed JWT   │                 │  • 4 Persona Prompts  │               │ • Confirmation Gate│
│  • Role Matrix  │                 │  • Disambiguation     │               │ • Dispatch Queue   │
└────────┬────────┘                 │  • Multilingual Engine│               └──────────┬─────────┘
         │                          └───────────┬───────────┘                          │
         │                                      │                                      │
         │                          ┌───────────▼───────────┐                          │
         │                          │  Tool Execution Layer │                          │
         │                          │ (Application-Layer    │◄─────────────────────────┘
         │                          │  Permission Checks)   │
         │                          └───────────┬───────────┘
         │                                      │
         └──────────────────────┬───────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Mock School ERP API  │
                    │  (Adapter Architecture│
                    │   backed by SQL DB)   │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  SQL System of Record │
                    │  • Users, Students    │
                    │  • Parent-Child Links │
                    │  • Teacher-Class Links│
                    │  • Attendance Records │
                    │  • Escalation Tickets │
                    │  • Immutable Audit Log│
                    └───────────────────────┘
```

---

## 📂 Repository Structure (5-Repo Ecosystem Standard)

```
School-ERP-Ecosystem/
├── 01-student-repository/student-portal/     # Student Portal (Stub)
├── 02-parent-repository/parent-portal/       # Parent Portal (Stub)
├── 03-management-repository/management-portal/ # Management Portal (Stub)
├── 04-staff-repository/staff-portal/         # Staff Portal (Stub)
└── 05-xyz-ai-repository/xyz-ai/              # Central AI Engine Implementation
    ├── backend/
    │   ├── src/
    │   │   ├── auth/                        # JWT & Deterministic RBAC Engine
    │   │   ├── conversation_engine/         # Intent Brain, Personas, Disambiguation & Memory
    │   │   ├── tools/                       # Adapter-Pattern Tool Layer (7 Server Tools)
    │   │   ├── escalation/                  # Two-Stage Confirmation State Machine
    │   │   ├── voice/                       # Unified STT, TTS & Lip-sync Visemes
    │   │   ├── i18n/                        # 11 Indian Languages Translation Pipeline
    │   │   ├── security/                    # Prompt Injection & Leak Filters
    │   │   ├── audit/                       # Immutable Database Audit Logs
    │   │   ├── api/                         # FastAPI Routers (Auth, Chat, Voice, Escalation, Portal, Audit)
    │   │   ├── config.py                    # Environment & Settings
    │   │   ├── database.py                  # SQLAlchemy Session & DB Engine
    │   │   ├── models.py                    # 9 Declarative SQL Models
    │   │   └── main.py                      # FastAPI App Entrypoint & Static Server
    │   ├── tests/
    │   │   ├── unit/                        # Unit tests for all phases & NLU regression tests
    │   │   ├── security-redteam/            # 15 Automated Adversarial Attack Tests
    │   │   └── integration/                 # End-to-End Gate & Concurrency Isolation Tests
    │   ├── seed/
    │   │   └── seed_data.py                 # DB Seed Script (25 Students, 5 Teachers, 23 Parents, 1 Principal)
    │   ├── requirements.txt
    │   └── Dockerfile
    ├── frontend/
    │   ├── src/
    │   │   ├── css/style.css                # Warm, Calm Light Design System
    │   │   └── js/
    │   │       ├── api.js                   # REST Client
    │   │       ├── avatar.js                # Canvas Avatar Lip-Sync Renderer
    │   │       ├── voice.js                 # Web Speech & TTS Controller
    │   │       ├── dashboards.js            # Role-Specific Dashboard Views
    │   │       └── app.js                   # Application Orchestrator
    │   └── index.html                       # Single Page Application
    ├── README.md
    └── docker-compose.yml
```

---

## 👥 Seeded User Accounts & Roles

All seeded accounts share the default password: **`School@123`**

| Role | Name | Email | Persona & Key Use-Case Focus |
| :--- | :--- | :--- | :--- |
| **Student** | Aarav Sharma | `aarav.sharma@xyzschool.edu` | Class 10-A. Attendance lookup, friendly study guidance, teacher help request. |
| **Parent** | Rajesh Sharma | `rajesh.parent@xyzschool.edu` | Parent of **2 children** (Aarav in 10-A & Ananya in 8-A). Multi-child disambiguation testing. |
| **Teacher** | Amit Verma | `amit.verma@xyzschool.edu` | Class 10-A Mathematics Teacher. Scoped attendance marking & class roster review. |
| **Principal**| Dr. Sunita Sharma | `principal@xyzschool.edu` | Executive School-wide attendance overview, escalation audit queue. |

---

## 🔒 Security & RBAC Boundary Matrix

| Action / Capability | Student | Parent | Teacher | Principal | Enforcement Point |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **View Own Attendance** | ✅ | ❌ | ❌ | ✅ (Oversight) | `enforce_permission` (Student Profile ID) |
| **View Child's Attendance** | ❌ | ✅ (Linked only) | ❌ | ✅ (Oversight) | `ParentStudentLink` DB Verification |
| **View Other Students' Data** | ❌ | ❌ | ❌ | ✅ (Oversight) | Application Layer (403 Forbidden) |
| **Mark Class Attendance** | ❌ | ❌ | ✅ (Assigned only)| ❌ (No tampering) | `TeacherClassLink` DB Verification |
| **School-wide Analytics** | ❌ | ❌ | ❌ | ✅ | Role Matrix Policy Check |
| **Class-level Analytics** | ❌ | ❌ | ✅ (Assigned only)| ✅ | Class Link & Scope Check |
| **Create Escalation Ticket** | ✅ | ✅ | ✅ | ✅ | Two-Stage State Machine (`PENDING`) |
| **Confirm Escalation Ticket**| ✅ (Own) | ✅ (Own) | ✅ | ✅ | Ticket Ownership Verification |
| **View Audit Logs** | ❌ (Own only) | ❌ (Own only) | ❌ (Own only) | ✅ (Full trail) | `AuditLog` Table Query Scope |

---

## 🧪 Automated Test Suite (63 / 63 Passing)

The test suite covers every layer of the architecture:

```bash
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1
rootdir: School-ERP-Ecosystem/05-xyz-ai-repository/xyz-ai/backend
collected 63 items

tests/integration/test_phase9_full_integration_gate.py ........... [ 11%] (7 Passed)
tests/security-redteam/test_adversarial_suite.py ................. [ 34%] (15 Passed)
tests/unit/test_natural_language_and_i18n_fixes.py ............... [ 46%] (7 Passed)
tests/unit/test_phase1_data_model.py ............................. [ 52%] (4 Passed)
tests/unit/test_phase2_auth_rbac.py .............................. [ 71%] (12 Passed)
tests/unit/test_phase3_tool_layer.py ............................. [ 79%] (5 Passed)
tests/unit/test_phase4_conversation_engine.py .................... [ 87%] (5 Passed)
tests/unit/test_phase6_escalation.py ............................. [ 92%] (3 Passed)
tests/unit/test_phase7_i18n.py ................................... [ 96%] (3 Passed)
tests/unit/test_phase8_voice.py .................................. [100%] (2 Passed)

============================= 63 passed in 23.32s =============================
```

### Red-Team & RBAC Test Coverage (19 Attack & Boundary Scenarios Blocked):
1. **DAN Jailbreak & System Instruction Override** $\rightarrow$ *Blocked by Prompt Sanitizer*
2. **System Prompt & Developer Directive Extraction** $\rightarrow$ *Blocked by Prompt Sanitizer*
3. **Student Claiming Principal Role in Text** $\rightarrow$ *Blocked by Server-Signed JWT RBAC*
4. **Parent Claiming Teacher Role to Mark Attendance** $\rightarrow$ *Blocked by Server-Signed JWT RBAC*
5. **Sudo / Developer / God Mode Commands** $\rightarrow$ *Blocked by Prompt Sanitizer*
6. **Database Credential & Secret Harvesting** $\rightarrow$ *Blocked by Sanitizer & Masking*
7. **Cross-Student Attendance Peeking** $\rightarrow$ *Blocked by Student Profile Boundary*
8. **Cross-Parent Unlinked Child Access** $\rightarrow$ *Blocked by Link Validator*
9. **Cross-Class Teacher Attendance Tampering** $\rightarrow$ *Blocked by Teacher-Class Scoping*
10. **SQL Injection in Tool Arguments** $\rightarrow$ *Blocked by Parameter Binding*
11. **Sliding-Window Rate Limit Flooding** $\rightarrow$ *Blocked with HTTP 429 / Rate Limit Event*
12. **Secret & Key Leakage Redaction Filter** $\rightarrow$ *Masked with `[REDACTED]`*
13. **Unauthorized Escalation Confirmation** $\rightarrow$ *Blocked by Ownership Gate*
14. **Teacher Attempting School-wide Analytics** $\rightarrow$ *Blocked by Scope Gate*
15. **Audit Trail Verification for All Attacks** $\rightarrow$ *Logged in Immutable `audit_logs` SQL Table*
16. **Bcrypt Per-User Dynamic Salting** $\rightarrow$ *Verified different hashes for identical passwords*
17. **Principal Self-Registration Protection** $\rightarrow$ *Blocked with HTTP 403 Forbidden*
18. **Unverified Teacher Attendance Restriction** $\rightarrow$ *Blocked at RBAC layer pending Principal approval*
19. **Student Self-Registration & Constraint Validation** $\rightarrow$ *Enforces unique (class, section, roll_no)*

---

## 🔐 Authentication & Self-Service Registration

The system supports multi-user authentication with password security:
- **Password Hashing**: `bcrypt` with automatic per-user salting via `passlib`.
- **JWT Tokens**: 24-hour expiration with signed subject and role claims.
- **Registration Endpoints**:
  - `POST /api/v1/auth/register` — Role-validated self-registration for Students, Parents, and Teachers.
  - Principal accounts cannot be self-registered (HTTP 403).
  - Teacher accounts are created with `is_verified = False` and can be approved by the Principal from the Staff Console (`POST /api/v1/portal/admin/teachers/{user_id}/approve`).

---

## 🗄️ Database & Production Supabase Setup

The backend connects seamlessly to PostgreSQL (Supabase) in production and falls back to local SQLite for zero-config development.

### Supabase Connection (Port 6543 Session Pooler)
1. Create a Supabase project at [supabase.com](https://supabase.com).
2. Copy the **Session Pooler** connection string: `Settings → Database → Connection string → Session mode (Port 6543)`.
3. Set the environment variable:
```bash
DATABASE_URL="postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
```
4. Seed the Supabase database:
```bash
python seed/seed_data.py
```

---

## 🚀 Quickstart: How to Run Locally

### Prerequisites
- Python 3.10+ (Tested on Python 3.11 & 3.13)
- `pip`

### Step 1: Navigate to Backend Directory & Install Dependencies
```bash
cd School-ERP-Ecosystem/05-xyz-ai-repository/xyz-ai/backend
pip install -r requirements.txt
```

### Step 2: Seed the Database
```bash
python seed/seed_data.py
```
*(Populates 1 Principal, 5 Teachers, 25 Students, 23 Parents, and 750 attendance records)*

### Step 3: Run the Complete Test Suite
```bash
pytest tests/ -v
```

### Step 4: Start the Server
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5: Open the Application
- **Interactive Web App**: Open **[http://localhost:8000](http://localhost:8000)** in your browser.
- **Interactive OpenAPI/Swagger Docs**: Open **[http://localhost:8000/docs](http://localhost:8000/docs)**.
- **Health Endpoint**: **[http://localhost:8000/health](http://localhost:8000/health)**.

---

## 🐳 Docker Deployment

To run via Docker Compose:

```bash
cd School-ERP-Ecosystem/05-xyz-ai-repository/xyz-ai
docker-compose up --build -d
```

The application will be accessible at `http://localhost:8000`.

---

## 🎯 Verification & Demo Walkthrough

1. **Student Natural Conversation**:
   - Log in as **Aarav Sharma** (`aarav.sharma@xyzschool.edu`).
   - Type *"Hello, how are you today?"* $\rightarrow$ receives a warm, polite student greeting without dumping attendance.
   - Type *"What is my attendance percentage?"* $\rightarrow$ invokes `get_attendance` and reports `96.7%` attendance.
   - Type *"Can you help me with my math homework?"* $\rightarrow$ receives constructive study strategies without false escalation.
   - Type *"I need help connecting with my teacher"* $\rightarrow$ creates ticket and prompts for confirmation.
2. **Parent Multi-Child Disambiguation**:
   - Switch role to **Rajesh Sharma** (`rajesh.parent@xyzschool.edu`).
   - Type *"How is my child doing with attendance?"* $\rightarrow$ Assistant recognizes 2 linked children and asks whether to check for **Aarav Sharma** (10-A) or **Ananya Sharma** (8-A).
   - Reply *"Check for Aarav"* $\rightarrow$ retrieves Aarav's real attendance report.
3. **Escalation Confirmation Gate**:
   - As a Parent or Student, type *"I want to talk to the teacher"*.
   - Assistant creates ticket `PENDING` and renders an interactive **"Confirm Request"** button.
   - Click **"Confirm Request"** $\rightarrow$ dispatches ticket to `CONFIRMED` status.
4. **Teacher Missing Parameter Handling & Marking**:
   - Switch to **Amit Verma** (`amit.verma@xyzschool.edu`).
   - Type *"mark attendance as absent for today"* without naming a student $\rightarrow$ Assistant asks: *"Which student in Class 10-A would you like to mark as absent?"*
   - Type *"Mark Aarav Sharma present today"* $\rightarrow$ marks attendance and updates the live roster.
5. **Multilingual Verification**:
   - Select **Hindi** (`हिन्दी`) or type `"मेरी उपस्थिति क्या है?"` $\rightarrow$ receives native Hindi response with live SQL data.
   - Select **Tamil** (`தமிழ்`) or **Bengali** (`বাংলা`) $\rightarrow$ receives authentic localized synthesis.
6. **Staff Security & Audit Console**:
   - When logged in as Teacher or Principal, click **"Open Staff Security Console"** to run live adversarial test attacks and inspect immutable database audit logs.

---

## 📄 License

This project is licensed under the MIT License. Developed for the XYZ AI School Assistant Architecture Challenge.
