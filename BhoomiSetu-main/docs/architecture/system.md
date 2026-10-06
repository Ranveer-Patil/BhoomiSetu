# System architecture

```text
Next.js / React on Vercel
        │ REST + JWT; 30-second refresh while open
FastAPI on Render ── OCR, grievance classification, synthetic-trained models
        │ SQLAlchemy / Alembic
PostgreSQL + PostGIS on Render
```

One frontend serves five roles. The API enforces citizen ownership and officer
assignment; authorized managers review the showcase across projects. PostgreSQL
stores cases, extracted document fields, grievances, compensation/R&R records,
deadlines, preferences and audit history. Original document scans are not retained.

Routes validate input and call services. External adapters separate optional
OpenAI integration and government-shaped fixtures from the workflow. Leaflet uses
OpenStreetMap reference tiles; all showcase parcel boundaries are synthetic.

## Invariants

- Stage changes use the workflow service and write history in the same transaction.
- Server-side roles and case scope apply regardless of visible frontend controls.
- Document extraction and grievance suggestions require human confirmation.
- Compensation amounts come from entered records, never predictions. Missing
  historic amounts and dates remain unrecorded.
- Alerts are generated from stored data on refresh. Operational stage targets are
  distinct from staff-recorded statutory deadlines and their source references.
- Audit writes use a serialized SHA-256 hash chain; this is not a blockchain.

The path is notification → verification → objection → award → compensation →
possession. Objection may return to verification with a recorded reason.

See [integration boundaries](../integration-matrix.md) and
[deployment requirements](../deployment.md). The ML model card describes the
1,800 synthetic training histories and their limited holdout metrics.
