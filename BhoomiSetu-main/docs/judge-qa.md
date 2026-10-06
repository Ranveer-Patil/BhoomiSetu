# BhoomiSetu judge Q&A

- **Why not DILRMP or BhoomiRashi?** BhoomiSetu is an orchestration layer alongside them. It connects citizen, officer, acquiring authority, district/state and central views without claiming to replace the systems of record.
- **Is API Setu live?** No. Production access requires consumer registration, subscription and publisher approval. The prototype uses honestly labelled fixtures matching the integration shape.
- **Why not predict land price or compensation amount?** Compensation amount is a statutory RFCTLARR calculation. We predict procedural delay and disbursal time, never a citizen’s legal entitlement.
- **How accurate is the model?** Prototype models use 1,800 reproducible synthetic histories, so their purpose is pipeline validation—not a production accuracy claim. Production validation and retraining require authority-owned historical cases.
- **Blockchain?** No. It is a concurrency-safe SHA-256 hash chain: tamper-evident and verifiable, but not a blockchain.
- **Authentication?** Short-lived JWT access tokens, separately signed refresh tokens, Argon2id password hashing and server-side RBAC on every protected route.
- **Privacy?** No real citizen data is in the prototype. Production design applies data minimisation, role separation, auditability and purpose limitation consistent with the DPDP framework.
- **Sustainability model?** Government-hosted state deployments with implementation, integration and support contracts; reusable open standards keep states from being locked into one vendor.
- **Why PostgreSQL/PostGIS?** Acquisition is relational and spatial. Transactions preserve workflow integrity; PostGIS performs real geometry storage and intersection queries in the same database.
- **What fails safely offline?** The complete local stack, deterministic fixtures, OCR, trained models and demo data run without hosted services; external map tiles need connectivity. The hosted portal also needs its API connection.
