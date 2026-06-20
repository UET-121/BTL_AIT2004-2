# Frontend

React/Vite SPA for the license plate recognition admin flow.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173` and proxies API requests to `http://localhost:8000` by default.

## Environment

- `VITE_API_URL=` uses the Vite proxy in development.
- `VITE_USE_DEMO_DATA=true` forces demo fallback data when you want to test UI without a backend.

## Scripts

- `npm run dev`
- `npm run build`
- `npm run preview`
- `npm run typecheck`

## Docker

The root `docker-compose.yml` includes a `frontend` service that exposes port `5173`.
