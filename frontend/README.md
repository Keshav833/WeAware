# WeAware frontend

The React app plans a truck trip, submits it to the Django analysis API, and
compares the routes returned by the routing provider.

## Run locally

Install dependencies and start Vite:

```sh
npm install
npm run dev
```

The frontend calls `http://127.0.0.1:8000/api` by default. To use another API
origin, set `VITE_API_BASE_URL` in a local `.env.local` file.

## Mapbox map

Set `VITE_MAPBOX_ACCESS_TOKEN` in `.env.local` to a public Mapbox access token
with map rendering enabled. Without this setting, route analysis and results
remain available, but the map displays a configuration notice instead of
rendering route geometry.

Vite environment variables are included in the browser bundle. Only use a
public Mapbox token with suitable URL restrictions; never put provider secrets
in frontend environment variables.
