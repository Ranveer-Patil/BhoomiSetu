# BhoomiSetu

**A GIS-enabled land acquisition and rehabilitation platform · SIH26016**

BhoomiSetu brings citizens, field officers and administrators into one shared
workflow—from acquisition notification to possession. It makes case progress,
compensation records, grievances and project performance easier to track.

**[Live demo](https://bhoomi-setu-steel.vercel.app)** ·
[API documentation](https://bhoomsetu-api.onrender.com/docs) ·
[Demo walkthrough](docs/demo-script.md)

## Key features

- **Five role portals:** Citizen, Field Officer, Project Authority, District Administrator and Senior Administrator, with role-based and case-level access.
- **Case management:** Six-stage acquisition journey, document review, grievance routing and tamper-evident audit history.
- **GIS mapping:** Interactive parcel maps backed by PostgreSQL/PostGIS and OpenStreetMap reference tiles.
- **Compensation and rehabilitation:** Recorded payment status, R&R progress, affected/displaced family counts and due dates.
- **Dashboards and reporting:** Eight KPI groups, project/state comparisons, timeline alerts, customizable CSV reports and print/save-to-PDF.
- **Document and predictive assistance:** Tesseract OCR with officer review, grievance classification, delay-risk estimates and compensation timeline estimates.
- **Accessibility:** Responsive mobile layouts; English, Hindi, Marathi, Gujarati and Kannada labels; citizen read-aloud through browser speech synthesis.

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, CSS |
| State and data fetching | TanStack Query, Zustand |
| Mapping | Leaflet, React Leaflet, OpenStreetMap |
| Backend | Python 3.13, FastAPI, Pydantic, Uvicorn |
| Database | PostgreSQL, PostGIS, SQLAlchemy, GeoAlchemy2, Alembic |
| Machine learning and OCR | scikit-learn Random Forest, pandas, NumPy, Tesseract |
| Authentication | JWT access/refresh tokens, Argon2 password hashing, role-based authorization |
| Testing and CI | pytest, Vitest, React Testing Library, Ruff, ESLint, GitHub Actions |
| Deployment | Docker Compose locally, Vercel frontend, Render API and database |

## Acquisition workflow

**Notification → Verification → Objection → Award → Compensation → Possession**

Citizens follow their cases and raise grievances. Officers review documents and
record progress. Authorities and administrators manage compensation/R&R records,
monitor exceptions and compare project performance.

## Demo and model scope

Demo cases and the **1,800 ML training records are synthetic**. No real government
case data was used to train the models. These are synthetic holdout results,
**not real-world accuracy**:

| Model | MAE | R² |
|---|---:|---:|
| Delay prediction | 12.92 days | 0.951 |
| Compensation timeline | 5.83 days | 0.898 |

Predictions estimate time, not compensation amounts or legal entitlements.
Government adapters are demonstration fixtures. OpenStreetMap is map reference
data, not ML training data; attribution belongs to
[OpenStreetMap contributors](https://www.openstreetmap.org/copyright).

[Model card](apps/backend/scripts/data/model_card.json) ·
[Integration details](docs/integration-matrix.md)

## Try it

Open the **[live demo](https://bhoomi-setu-steel.vercel.app)** and choose a role.
Synthetic demo credentials are prefilled. The free API may take about a minute to
wake after inactivity; open it before presenting. Read-aloud requires an installed
voice matching the selected language.

For local setup, see [Team setup](docs/team-setup.md).

## Project structure

- `apps/frontend` — Next.js application and UI tests
- `apps/backend` — FastAPI services, database migrations, ML pipelines and API tests
- `scripts` — Local setup and verification commands
- `docs` — Architecture, presentation walkthrough and deployment documentation
