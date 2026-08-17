# School ERP Ecosystem

Standard multi-repository ecosystem structure for school enterprise systems:

```
School-ERP-Ecosystem/
├── 01-student-repository/student-portal/     (Student Portal Stub)
├── 02-parent-repository/parent-portal/       (Parent Portal Stub)
├── 03-management-repository/management-portal/ (Management Portal Stub)
├── 04-staff-repository/staff-portal/         (Staff Portal Stub)
└── 05-xyz-ai-repository/xyz-ai/              (Core AI Assistant Implementation)
    ├── backend/
    │   ├── src/
    │   │   ├── auth/                        # JWT & Deterministic RBAC Engine
    │   │   ├── conversation_engine/         # Memory, Personas, Disambiguation & LLM Orchestrator
    │   │   ├── tools/                       # Adapter-Pattern Tool Calling Layer
    │   │   ├── escalation/                  # Two-Stage Confirmation State Machine
    │   │   ├── voice/                       # Unified STT, TTS & Lip-sync Visemes
    │   │   ├── i18n/                        # 11 Indian Languages Pipeline
    │   │   ├── security/                    # Prompt Injection & Credential Leak Filters
    │   │   └── audit/                       # Immutable Database Audit Logs
    │   ├── tests/
    │   │   ├── unit/                        # Data model, RBAC, tool, escalation & voice tests
    │   │   ├── integration/                 # End-to-end multi-turn & concurrency gate tests
    │   │   └── security-redteam/            # 15 Automated Adversarial Attack Tests
    │   └── seed/                            # Seed script (25 students, 5 teachers, 23 parents, 1 principal)
    ├── frontend/
    │   ├── src/                             # Canvas Avatar, Voice & Role Dashboards
    │   └── index.html                       # Unified Web Application
    ├── README.md
    └── docker-compose.yml
```

To run the central AI system, navigate to `05-xyz-ai-repository/xyz-ai/README.md`.
