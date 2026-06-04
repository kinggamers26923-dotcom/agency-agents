# Jarves Assistant

A small OpenAI-powered assistant app that runs locally and lets you chat with Jarves, manage tasks, and ask for updates.

## Setup

1. Open a terminal in `jarves-app`
2. Run `npm install`
3. Copy `.env.example` to `.env`
4. Set `GEMINI_API_KEY` in `.env`
5. Ensure `USE_GEMINI=true` is set in `.env`

## Run

- `npm start` — launch the app in development
- `npm run dev` — start Vite and Electron together

Then open `http://localhost:5173`

## Gemini setup notes

- Get a Gemini API key from Google AI Studio or the Gemini developer dashboard.
- Put the key value into `.env` as `GEMINI_API_KEY=sk-...`.
- If you want to switch back to OpenAI later, set `USE_GEMINI=false` and add `OPENAI_API_KEY`.

## How it works

- Frontend code lives in `src/`
- The app uses Vite for development and Electron for desktop startup

## Next steps

- Add persistent storage for tasks (SQLite, MongoDB, or JSON file)
- Improve task state management with statuses and deadlines
- Add authentication if you want to secure the app
- Expand Jarves prompts to support project-specific workflows
