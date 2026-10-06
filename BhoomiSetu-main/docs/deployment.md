# Deployment

Current hosts: [Vercel frontend](https://bhoomi-setu-steel.vercel.app),
[Render API](https://bhoomsetu-api.onrender.com) and Render PostgreSQL/PostGIS.
The repository is public. Secrets belong in provider settings, never Git.

## Render

The root `render.yaml` defines the Docker API and Render database. Startup runs
Alembic and seeds the 20-case synthetic showcase **only if absent**; redeploys do
not reset saved interactions. The operations migration adds fields/tables without
inventing historic payment amounts, document dates or statutory deadlines.

Required environment settings:

- `DATABASE_URL`: Render supplies its database connection string. Configuration
  normalizes `postgres://` / `postgresql://` to the async SQLAlchemy driver.
- `APP_ENVIRONMENT=production`
- Different, strong `JWT_SECRET` and `JWT_REFRESH_SECRET` values
- `FRONTEND_ORIGIN=https://bhoomi-setu-steel.vercel.app`

The migration enables PostGIS. `/health` checks the API process; `/ready` also
checks the database, PostGIS and current migration revision. Use `/ready` as the
Render health-check path (existing services may require updating this setting).

## Vercel

Import `Punit1787/BhoomiSetu`, root directory `apps/frontend`, production branch
`main`. Set `NEXT_PUBLIC_API_BASE_URL=https://bhoomsetu-api.onrender.com` before
building. The UI refreshes database-backed queries every 30 seconds while open.

## Keepalive and free hosting

`.github/workflows/keepalive.yml` sends a request every ten minutes on **12 September
2026, India time**, for judging (00:07–23:57 IST). It also supports manual runs.
The date guard prevents pings in later years or if GitHub delivers a job late.
There is no continuous daily schedule, paid plan or spending-limit change.

The judging-day schedule has 144 jobs, plus any manual runs and ordinary CI.
GitHub schedules can be delayed or dropped, so this cannot guarantee uptime.
Open the portal before presenting.

[Render Free](https://render.com/docs/free) sleeps after 15 idle minutes, shares
750 running hours per workspace/month, and its free Postgres database expires
30 days after creation. Pings do not prevent database expiry, maintenance or quota
suspension. Check the database expiry in Render before a presentation; arrange a
backup/authorized database plan separately. No paid upgrade is part of this change.

## Release checks

1. Run backend tests against a separate migrated PostGIS test database, plus
   frontend lint, tests and a production build.
2. Review the diff and push the tested revision to the connected deployment branch.
3. Verify GitHub CI, Render and Vercel show the expected revision.
4. Check `/ready`, `/openapi.json`, CORS and real seeded-account login.
5. Check the mobile menu, case documents/grievances, manager reports and inbox.

Do not run `reset_demo.sh` against hosted data unless an intentional reset has
been authorized.
