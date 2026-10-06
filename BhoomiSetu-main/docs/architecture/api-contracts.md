# API contracts

The generated [API documentation](https://bhoomsetu-api.onrender.com/docs) is the
authoritative request/response contract. Locally it is at `http://localhost:8000/docs`.
Protected requests use `Authorization: Bearer <access_token>`.

| Area | Main routes and access |
|---|---|
| System | `GET /health`, `GET /ready` (database/PostGIS/migration), `GET /master-data` |
| Authentication | `POST /auth/register` creates citizens only; `/auth/login`, `/auth/refresh`; senior admins provision accounts with `POST /auth/users` |
| Projects and parcels | `/projects`, `/projects/{id}/parcels`, `/parcels/{id}`, `/parcels/{id}/landowners`; citizen/officer reads are scoped |
| Cases | `GET /cases` supports filters and pagination; `GET /cases/{id}` includes history; staff use `POST /cases/{id}/transition` |
| Case records | `GET /cases/{id}/operations`; managers write `/cases/{id}/compensation`, `/cases/{id}/rr`, `/cases/{id}/families`, `/cases/{id}/deadlines`; audited compensation/R&R removal via `/cases/{id}/records/{kind}` |
| Documents | `POST /cases/{id}/documents`; authorized staff re-extract or confirm via `/documents/{id}/extract` and `/documents/{id}/confirm` |
| Grievances | `POST /cases/{id}/grievances`; staff confirm suggestions and respond via `/grievances/{id}/confirm` and `PATCH /grievances/{id}` |
| GIS | `GET /gis/parcels` returns accessible parcel geometry and stage |
| Dashboard | `GET /dashboard/summary` with optional state, district and project filters |
| MIS | Managers use `GET /reports/{project,state,district,compensation}` with `format=json` or `csv`, selected `columns` and filters; the frontend supports print/save PDF |
| Inbox | `GET /alerts`; `PUT /alerts/read?key=...` stores the current user's read receipt |
| Preferences | `GET/PUT /me/preferences`; locale body or `Accept-Language` header |
| Audit | Authorized administrators inspect `/audit-log` and `/audit-log/verify` |

Predictions and government adapter fixtures remain separately labelled in the API
schema. Survey/required-field checks validate format, not the legal truth of a record.
