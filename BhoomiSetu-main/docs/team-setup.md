# Team setup and secrets

## Share the project

The GitHub repository is public; add teammates as collaborators if they need push
access. Clone the repository normally; do not send `node_modules`, `.venv`, `.next`, generated model
binaries or local `.env` files.

```bash
git clone https://github.com/Punit1787/BhoomiSetu.git
cd BhoomiSetu
./scripts/bootstrap.sh
./scripts/start_demo.sh
```

The bootstrap requires Git, Docker Desktop, Python 3.13 and Node.js 22. It starts
PostgreSQL/PostGIS, creates local environment files from safe templates, installs
dependencies, migrates the database, trains the synthetic models and creates the
showcase data.

## Environment files

- Commit `.env.example` files only.
- Every teammate keeps their own `.env`/`.env.local`; Git ignores them.
- Share production secrets through the hosting provider's encrypted environment
  settings or a password manager, never chat, email or Git.
- `NEXT_PUBLIC_*` values are browser-visible. Never put a service-role key or secret
  API key in one.
- Rotate a credential immediately if it is ever committed, even if the commit is
  later deleted.

## Team workflow

```bash
git switch -c feature/short-description
./scripts/check.sh
git add <specific-files>
git commit -m "Describe the change"
git push -u origin feature/short-description
```

Open a pull request into `main`; do not have everyone commit directly to `main`.
The repository runs backend and frontend checks automatically on pull requests.
