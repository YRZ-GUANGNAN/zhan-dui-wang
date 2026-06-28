# Zhandui Online

This repository tracks the source currently deployed at `zhanduiwang.top`.

## Verify

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
Set-Location frontend
npm ci
Set-Location ..
.\scripts\test.ps1
```

Production secrets belong in `/etc/zhandui/zhandui.env` and must never be committed.

## Database migrations

Production migrations use a dedicated DDL account from
`/etc/zhandui/migration.env`.

```bash
set -a
. /etc/zhandui/migration.env
set +a
cd /opt/zhandui/releases/<release>
/opt/zhandui/venv/bin/python3 -m alembic -c alembic.ini current
/opt/zhandui/venv/bin/python3 -m alembic -c alembic.ini upgrade head
```

Always run `/opt/zhandui/backup.sh` and verify the resulting archive before an
upgrade.

## Realtime chat

The browser opens one authenticated WebSocket at `wss://zhanduiwang.top/ws`.
The first frame must contain the JWT:

```json
{"type": "auth", "token": "<jwt>"}
```

Text messages use a client-generated `clientId`. The database unique constraint
on `(sender_id, client_id)` makes WebSocket retry and REST fallback idempotent.
