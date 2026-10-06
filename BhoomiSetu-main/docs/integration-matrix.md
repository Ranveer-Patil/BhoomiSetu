# Integration matrix

| Capability | Current implementation | Boundary |
|---|---|---|
| Web and API | Next.js on Vercel; FastAPI Docker on Render | Real hosted software; showcase records are synthetic |
| Database and GIS | PostgreSQL/PostGIS on Render; Leaflet/OSM tiles | OSM is reference mapping, not ML training or cadastral proof |
| Authentication | JWT refresh, Argon2, five roles, scoped citizen/officer access | Public registration creates citizens; senior admins provision staff |
| Workflow and audit | Six stages, officer transitions, SHA-256 hash chain | Tamper-evident audit, not blockchain or independent notarization |
| Compensation and R&R | Audited CRUD, family counts, references and due dates | Staff-entered records; no bank transfer, valuation or benefit entitlement engine |
| Dashboard and MIS | Eight KPI groups, project/state/district rollups, equal month-to-date trends, selectable CSV columns and browser print/PDF | Missing money/deadlines remain unrecorded; possession defines acquired area/completion |
| Alerts | Rules for aged reviews, stage delays, recorded deadlines, overdue payments and milestones; per-user read receipts | Generated on inbox refresh; 30-second UI polling. No SMS, email or background push |
| Statutory monitoring | Staff enter a stage deadline with its authority/reference | Operational targets are labelled separately; no automatic legal deadline calculation |
| Master data | Canonical project/document/grievance types, survey-format and required-field checks | Format validation does not authenticate a land record |
| Languages | English, Hindi, Marathi, Gujarati and Kannada labels, stages and categories; saved user locale | Extracted text, rationale and free text are not translated |
| Read aloud | Browser speech synthesis on citizen case status | Requires a matching installed voice; no paid or generative voice API |
| OCR | Tesseract with English/Hindi/Marathi; officer correction/confirmation | PNG/JPEG/TIFF, 10 MB max; extracted metadata retained, original scans not stored |
| Optional vision/classification | OpenAI adapters when an approved API key is configured | Otherwise OCR/rule fallback; model suggestions require human review |
| Predictive models | Two Random Forest pipelines trained on 1,800 synthetic histories | Synthetic holdout metrics only; not real-world accuracy or legal decisions |
| API Setu / NGDRS | Explicitly labelled adapter fixtures | No live government access or approved credentials |
| Updates | TanStack Query polling against Render API | No external realtime subscription or credentials required |
| Keepalive | Manual check plus ten-minute schedule on 12 September 2026 (IST) | GitHub scheduling limits apply; no uptime or database-expiry guarantee |

Live government adapters require institutional onboarding and publisher approval.
Real model validation requires approved, de-identified case histories and independent
holdouts. Neither is claimed by this prototype.
