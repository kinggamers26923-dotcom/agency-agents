# Jarves Assistant

A small OpenAI-powered assistant app that runs locally and lets you chat with Jarves, manage tasks, and ask for updates.

## Setup

1. Open a terminal in `jarves-app`
2. Run `npm install`
3. Copy `.env.example` to `.env`
4. Set `GEMINI_API_KEY` in `.env`
5. Ensure `USE_GEMINI=true` is set in `.env`

## Run

- `npm start` — run the app
- `npm run dev` — run with `nodemon` for live reload

Then open `http://localhost:3000`

## Gemini setup notes

- Get a Gemini API key from Google AI Studio or the Gemini developer dashboard.
- Put the key value into `.env` as `GEMINI_API_KEY=sk-...`.
- If you want to switch back to OpenAI later, set `USE_GEMINI=false` and add `OPENAI_API_KEY`.

## How it works

- `server.js` hosts a simple Express backend and serves the UI
- `/api/jarves` forwards user chat messages to OpenAI
- `/api/tasks` stores task items in memory
- Frontend code lives in `public/app.js`

## Next steps

- Add persistent storage for tasks (SQLite, MongoDB, or JSON file)
- Improve task state management with statuses and deadlines
- Add authentication if you want to secure the app
- Expand Jarves prompts to support project-specific workflows
