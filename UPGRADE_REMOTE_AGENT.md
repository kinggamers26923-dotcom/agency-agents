Upgrade notes — Remote agent (summary)

Files to update when building a remote agent:

- app.py — main Flask app (queue/approve/webhooks)
- services/telegram_service.py — Telegram send logic
- services/whatsapp_service.py — Twilio/WhatsApp send logic
- cli.py — local CLI to queue/approve (can be adapted for remote control)
- scripts/start_ngrok.ps1 — local ngrok starter for webhooks
- .env.example / .env — credential storage (do NOT commit secrets)

Suggested remote-agent changes:

1. Replace in-memory `pending`/`sent` lists with a persistent DB (SQLite/Postgres).
2. Add authentication on `app.py` endpoints (JWT or API keys).
3. Add a secure agent runner that polls the DB for approved messages.
4. Implement an SSH or RPC install script; do NOT allow arbitrary remote code execution.
5. Add detailed audit logs and consent records.

When you're ready to let a remote agent edit files via your tool ("antigraty"), point it to the workspace folder `c:/Users/VICTUS/OneDrive/Documents/GitHub/agency-agents` and edit these paths.
