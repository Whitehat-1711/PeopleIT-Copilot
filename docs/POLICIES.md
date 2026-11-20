# 📚 WorkPulse AI — Policy Knowledge Base

This directory contains the verified corporate policy documentation powering the **ChromaDB vector store** in **WorkPulse AI**. All documents are structured with explicit section headers, department ownership, and verification timestamps.

---

## 📑 Document Directory

| Document | Primary Topics Covered | Department Owner | Version Date |
| :--- | :--- | :--- | :--- |
| **`hr_policy.md`** | Annual leave (20 days), sick leave (10 days), parental leave, remote work guidelines, ₹40k L&D stipend, 60-day notice period. | People Operations (`hr@company.com`) | `2026-01-15` |
| **`it_policy.md`** | Password complexity, WireGuard VPN configuration, hardware refresh lifecycle (3 years), approved software, endpoint encryption (BitLocker/FileVault). | IT Operations (`it-support@company.com`) | `2026-01-10` |
| **`expenses_travel_policy.md`** | Domestic per diem meal limits (₹1,500/day), international hotel allowance (\$200/night), flight booking rules, non-reimbursable expenses, 30-day submission deadline. | Finance & Travel (`expenses@company.com`) | `2026-01-20` |
| **`onboarding_offboarding_policy.md`** | 3-day new hire orientation, credential provisioning timeline, 6-month probation review, equipment clearance, final settlement (F&F) SLA. | People Operations & IT | `2026-01-15` |
| **`code_of_conduct.md`** | Workplace anti-harassment & POSH standards, dual employment / moonlighting restrictions, gift acceptance threshold (₹2,000), whistleblower protections. | Legal & Compliance (`compliance@company.com`) | `2026-01-18` |
| **`data_handling_policy.md`** | Data classification tiers (Public, Internal, Confidential, Restricted), customer PII handling under GDPR/DPDP, least privilege access, 1-hour breach notification SLA. | Data Security Office (`security@company.com`) | `2026-01-22` |

---

## 🔍 Intentional Knowledge Gaps (Escalation Triggers)

To test and verify the agent's out-of-corpus detection and automated escalation engine, certain topics are **intentionally omitted** from this knowledge base:
- **Sabbatical Leave**: Not defined in any policy.
- **Pet Bereavement Leave**: Not defined in any policy.
- **Executive Relocation Stipend**: Handled exclusively on a case-by-case basis.

When employees inquire about these topics, the similarity score drops below the tuned cutoff (`0.60`), triggering the agent to:
1. Refuse to hallucinate.
2. Automatically invoke the `create_support_ticket()` tool.
3. Return the generated support ticket ID (e.g. `HR-1042`) and department contact info to the employee.

---

## ⚙️ Ingestion & Chunking Pipeline

Policies are parsed and indexed into ChromaDB via `backend/src/backend/ingest.py`:

```powershell
# Run the ingestion script
.\run.ps1 ingest
```

### Pipeline Workflow:
1. **Markdown Header Splitting**: Chunks are split on `#` and `##` markdown headings to preserve complete clause boundaries.
2. **Metadata Tagging**: Each chunk is indexed with:
   - `document`: Filename
   - `section`: Heading title
   - `owner`: Department contact
   - `last_updated`: Timestamp
3. **Embedding Vectorization**: Vectors are generated and loaded into the `hr_it_policies` collection on ChromaDB (port 8000).
