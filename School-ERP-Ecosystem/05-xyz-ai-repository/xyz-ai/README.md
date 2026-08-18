# XYZ AI — Human-Like School Assistant
### Production-Ready, Backend-First, Hardened Multi-Role School ERP Intelligence

---

## 1. System Overview & Architecture

XYZ AI Assistant is an enterprise-grade AI school assistant built on **defense-in-depth security principles**. Every claim made by the assistant is backed by real, deterministic database queries and application-layer authorization checks.

```
                    ┌────────────────────────────────────────────────────────┐
                    │               Client Layer (Single Page App)            │
                    │  Chat Stream UI  |  Voice Controller  |  Canvas Avatar │
                    └───────────────────────────┬────────────────────────────┘
                                                │ HTTPS / REST
                    ┌───────────────────────────▼────────────────────────────┐
                    │                  FastAPI Gateway / BFF                  │
                    │   - JWT Verification & Role-Claim Signature            │
                    │   - Sliding-Window Rate Limiter                        │
                    │   - Input Prompt Injection & Jailbreak Defense         │
                    │   - Output Secret & Credential Leakage Filter          │
                    └───────────────────────────┬────────────────────────────┘
                                                │
         ┌──────────────────────────────────────┼──────────────────────────────────────┐
         │                                      │                                      │
┌────────▼────────┐                 ┌───────────▼───────────┐               ┌──────────▼─────────┐
│   Auth & RBAC   │                 │  Conversation Engine  │               │ Escalation Service │
│   Service       │                 │  - Multi-turn Memory  │               │ - State Machine    │
│  - Signed JWT   │                 │  - 4 Persona Prompts  │               │ - Confirmation Gate│
│  - Matrix Policy│                 │  - Disambiguation     │               │ - Real Dispatch Log│
└────────┬────────┘                 │  - Tool Orchestrator  │               └──────────┬─────────┘
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
                    │  (Users, Links, Att,  │
                    │   Escalations, Audit) │
                    └───────────────────────┘
```

---

## 2. Seed Accounts & Credentials

All users share the default password: **`School@123`**

| Role | Name | Email | Persona & Key Use-Case Focus |
| :--- | :--- | :--- | :--- |
| **Student** | Aarav Sharma | `aarav.sharma@xyzschool.edu` | Class 10-A. Attendance lookup, teacher help request. Friendly, simple tone. |
| **Parent** | Rajesh Sharma | `rajesh.parent@xyzschool.edu` | Parent of **2 children** (Aarav [10-A] & Ananya [8-A]). Disambiguation testing. |
| **Teacher** | Amit Verma | `amit.verma@xyzschool.edu` | Class 10-A Math Teacher. Scoped marking & roster analytics. |
| **Principal**| Dr. Sunita Sharma | `principal@xyzschool.edu` | Executive School-wide attendance overview, escalation audit queue. |

---

## 3. Security & Application-Layer Permission Matrix

| Role | View Own Attendance | View Child Attendance | View Other Student Attendance | Mark Attendance | School Analytics | Class Analytics | Create Escalation | Confirm Escalation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Student** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ (Own ticket) |
| **Parent** | ❌ | ✅ (Linked only) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ (Own ticket) |
| **Teacher** | ❌ | ❌ | ✅ (Assigned only) | ✅ (Assigned only) | ❌ | ✅ (Assigned only) | ✅ | ✅ |
| **Principal**| ✅ | ✅ | ✅ (Oversight) | ❌ (No tampering) | ✅ | ✅ | ✅ | ✅ |

---

## 4. Test Suites & Verification Results (63 / 63 Passed)

### Test Coverage Summary:
- **Unit Tests (21 tests)**: Database schema, foreign key cascade, bcrypt salting, student/parent/teacher self-registration, principal self-registration blocking, auth JWT tamper/expiration, RBAC policy boundaries, ERP adapter tools, escalation state machine.
- **Security Red-Team Suite (15 tests)**: Adversarial attacks covering jailbreaks, prompt injection, role impersonation, system prompt extraction, credential fishing, cross-student peeking, cross-class teacher tampering, SQL injection, and rate limiting.
- **Integration Gate Suite (7 tests)**: Full 4-persona conversational flows, parent multi-child disambiguation, HTTP escalation lifecycle, voice turn processing, and 20+ concurrent session isolation.
- **Multi-Language & Voice Suites (13 tests)**: 11-language catalog, 4 deep-tested languages (English, Hindi, Tamil, Bengali), noisy voice rejection, and viseme TTS sync.
- **NLU & Intent Regression Suite (7 tests)**: Disambiguation, greeting isolation, implicit attendance query recognition, proactive escalation offer.

```bash
============================= 63 passed in 23.32s =============================
```

---

## 5. How to Run Locally

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Seed Database
```bash
python seed/seed_data.py
```

### Step 3: Run All Tests
```bash
pytest tests/ -v
```

### Step 4: Start Application Server
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at **`http://localhost:8000`** to access the interactive web application, AI Canvas Avatar, Voice recorder, and Role Dashboards.
Interactive API documentation is available at **`http://localhost:8000/docs`**.
