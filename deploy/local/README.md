# Easy Maid — Local Development (Docker Compose)

The local stack replaces the former in-cluster `easymaid-dev` namespace. The
Kubernetes cluster (`deploy/k8s/easymaid`) is now **production only**.

## What it runs

| Service | Purpose |
| --- | --- |
| `mariadb` | MariaDB 10.11 database |
| `redis-cache` / `redis-queue` / `redis-socketio` | Redis 7.2 instances |
| `configurator` | one-shot: writes global bench config |
| `create-site` | one-shot: creates the site, installs `erpnext` + `easy_maid` |
| `backend` | Gunicorn web (http://easymaid.localhost:8000) |
| `websocket` | Frappe socket.io (port 9000) |
| `scheduler` | background scheduler |
| `queue-default` / `queue-short-long` | background workers |

The `easy_maid` app is bind-mounted from `../../apps/easy_maid`, so local edits
are reflected in the containers.

## Quick start

```bash
cd deploy/local
cp .env.example .env          # optional — defaults are baked in
docker compose up -d
docker compose logs -f create-site   # watch the one-time seed finish
```

Then open <http://easymaid.localhost:8000> and log in as
`Administrator` / `admin` (or your `ADMIN_PASSWORD`).

> `*.localhost` resolves to 127.0.0.1 in all modern browsers, so no `/etc/hosts`
> edit is needed. Always use the `easymaid.localhost` host (not `localhost`) so
> Frappe resolves the correct site.

## Common tasks

```bash
# Run a bench command against the site
docker compose exec backend bench --site easymaid.localhost <command>

# Migrate after schema changes
docker compose exec backend bench --site easymaid.localhost migrate

# Build assets
docker compose exec backend bench build

# Open a bash shell
docker compose exec backend bash

# Stop (keep data)
docker compose down

# Reset everything (DESTROYS local data)
docker compose down -v
```

## Notes

- `developer_mode` and `server_script_enabled` are on for local convenience.
- This stack is intentionally not hardened; do not expose it publicly.
- Production lives in `deploy/k8s/easymaid` and uses `easymaid.trector.com`.
