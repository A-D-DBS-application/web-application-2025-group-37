[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DxqGQVx4)

# OpWielekes – web app

## Home page images (customize)

## Run locally with the shared Supabase database

To ensure everyone sees the same data (and not a local SQLite file), use the provided `.env.example`.

1) Create a `.env` next to `app.py`:

```
cp .env.example .env
```

2) Install deps and run (PowerShell):

```
python -m pip install -r requirements.txt
python .\app.py
```

At startup, the console prints a safe summary of the active DB connection. It should show `driver=postgresql+psycopg2` and host `aws-1-eu-west-3.pooler.supabase.com`.

Notes:
- If `.env` is missing, the app falls back to a local SQLite DB in `instance/app.db`.
- `.gitignore` prevents committing any local SQLite files and `.env` secrets, so teammates won’t pull your local data by accident.
