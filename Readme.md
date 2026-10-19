# WeAware

WeAware is a weather-aware truck trip planner. It compares provider-supplied
driving alternatives using forecast conditions, estimated checkpoint arrival
times, and truck load, then presents route recommendations and checkpoint
details.

## Features

- Geocode an origin and destination and request alternative driving routes.
- Generate checkpoints along each route at a selectable 10, 25, or 50 mile
  interval.
- Retrieve wind, rain, and snowfall forecasts and classify checkpoint risk.
- Compare route distance, duration, checkpoint risk, and scoring results.
- Explore forecast hours 0–48 with a slider and playback controls.
- Show a map heatmap and checkpoint markers when a Mapbox token and browser
  WebGL are available.
- Display missing weather as **Unknown**, not as safe weather.

## Architecture and request flow

```text
React trip form
  -> POST /api/analyze
  -> validate trip inputs
  -> geocode with Mapbox
  -> fetch alternative routes from Mapbox Directions
  -> interpolate checkpoints and estimated arrival times
  -> fetch Open-Meteo hourly weather for each checkpoint
  -> classify risk using weather and truck load
  -> score/rank routes and return JSON
  -> display route alternatives, forecast timeline, checkpoint details, and map
```

The backend is Django and Django REST Framework. The frontend is React,
TypeScript, and Vite, with Mapbox GL for the map. Weather is provided by
Open-Meteo. Mapbox is required for geocoding and route generation; its browser
map token is separately configurable from the backend token.

## Risk model and limitations

The worst of wind, rain, and snow risk is used for each checkpoint.

| Condition | Low | Moderate | High | Severe | No Travel |
|---|---:|---:|---:|---:|---:|
| Wind (mph) | <25 | 25–<35 | 35–<45 | 45–<55 | >=55 |
| Rain (in/hr) | <0.10 | 0.10–<0.25 | 0.25–<0.50 | 0.50–1.00 | >1.00 |
| Snow (in/hr) | <0.5 | 0.5–<1.0 | 1.0–<2.0 | 2.0–3.0 | >3.0 |

Truck-load overrides:

- Wind >=55 mph is No Travel for any load.
- Wind >=45 mph with load >30,000 lb is No Travel.
- Wind >=35 mph with load >40,000 lb is at least Severe.

Weather coverage depends on provider availability and checkpoint location/time.
Missing or incomplete weather is **Unknown** and is excluded from a safe-risk
assumption. Risk coloring between checkpoints is an estimate assigned from
nearby checkpoint data; it is not a precise road-level measurement. Route
durations come from the routing provider and do not include weather delays.
Forecasts are limited to the provider's available horizon; hours without usable
data remain Unknown.

## Requirements

- Python 3.12 or newer
- Node.js compatible with the Vite version in `frontend/package.json`
- A Mapbox access token for geocoding and directions
- A public, URL-restricted Mapbox token for map rendering (optional)
- PostgreSQL for a production deployment; SQLite is used by default locally
- Open-Meteo access (no API key required for the configured forecast endpoint)

## Environment variables

Create `backend/.env` from `backend/.env.example` only if you don't already
have a local environment file, then configure:

| Variable | Purpose |
|---|---|
| `DEBUG` | Django debug mode. Use `True` only locally; set `False` in production. |
| `SECRET_KEY` | Django secret. Required in all environments; use a strong non-placeholder value. |
| `ALLOWED_HOSTS` | Comma-separated backend hostnames (hostnames only, no scheme). |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins, including scheme. |
| `CSRF_TRUSTED_ORIGINS` | Optional comma-separated trusted origins including scheme. |
| `DATABASE_URL` | Database URL; defaults to the local SQLite database. |
| `MAPBOX_ACCESS_TOKEN` | Private backend token for Mapbox geocoding and directions. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | Optional production SMTP settings. |

In production, configure `DEBUG=False`, a strong secret, explicit allowed hosts
and CORS origins, and a managed PostgreSQL `DATABASE_URL` in the hosting
provider's secret/environment settings. Do not commit `.env` files or tokens.
Production TLS settings assume the hosting proxy sets
`X-Forwarded-Proto: https`.

Copy `frontend/.env.example` or create `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_MAPBOX_ACCESS_TOKEN=replace-with-a-public-url-restricted-token
```

`VITE_` values are compiled into the browser bundle. Only put a public,
URL-restricted Mapbox token there; never put the backend Mapbox token or Django
secret in frontend variables.

## Local installation and run

### Backend (PowerShell)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Put the generated value in backend/.env as SECRET_KEY.
python manage.py migrate
python manage.py runserver
```

### Backend (macOS/Linux)

```sh
cd backend
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
test -e .env || cp .env.example .env
# Replace SECRET_KEY in .env with a value from Django's get_random_secret_key().
python manage.py migrate
python manage.py runserver
```

### Frontend

```sh
cd frontend
npm ci
npm run dev
```

Vite defaults to `http://localhost:5173`; the backend defaults to
`http://127.0.0.1:8000`.

## API

### `GET /api/health`

Returns a basic API health response.

### `POST /api/analyze`

Example request:

```json
{
  "origin": "New York, NY",
  "destination": "Boston, MA",
  "departure_utc": "2030-01-01T12:00:00Z",
  "load_lb": 24000,
  "interval_miles": 25
}
```

`departure_utc` must be a future timezone-aware timestamp. `load_lb` must be
positive. `interval_miles` must be 10, 25, or 50. A successful response includes
the resolved endpoints, departure time, analyzed route geometries, checkpoint
weather and forecasts, route scores/ranks, and recommendation. Invalid input is
returned as a validation error; geocoding and routing provider failures return
an upstream gateway error.

## Tests and workflow verification

Run the backend suite and frontend checks:

```sh
cd backend
python manage.py test

cd ../frontend
npm run lint
npm run build
```

### Trip workflow smoke-test checklist

These checks describe the current local verification. Browser workflow checks
used deterministic mocked API responses; they do not replace a real provider
request.

| Check | Result | Evidence/notes |
|---|---|---|
| Full backend suite | Pass | 93 Django tests passed, including risk thresholds, load overrides, checkpoint generation, weather matching, scoring, serializers, API errors, and malformed forecast handling. |
| Invalid API input | Pass | Invalid zero truck load returns HTTP 400 before trip analysis starts. |
| Empty required fields | Pass | Browser smoke check displayed the required origin/destination validation message without calling the API. |
| Identical locations | Pass | Browser smoke check and serializer test rejected case-insensitive identical origin and destination. |
| Valid trip submission and result rendering | Pass with fixture | Browser smoke check submitted a valid form against a deterministic mock response and displayed route/checkpoint results. |
| Route selection | Pass with fixture | Selecting an alternative synchronized the selected route card and checkpoint panel. |
| Forecast range and playback | Pass with fixture | Slider reached hour 48; playback advanced and stopped at 48; pause was responsive. |
| Missing forecast | Pass with fixture | Unavailable weather displayed Unknown and an availability warning. |
| API failure handling | Pass | Browser smoke check displayed the API's 502 detail message; backend API tests cover geocoding and routing failures. |
| Weather-provider failure/empty/malformed response | Pass in backend tests | Provider errors, empty forecasts, malformed JSON structures, and non-finite measurements do not produce safe-risk values; missing weather remains Unknown. |
| Frontend lint and production build | Pass | `npm run lint` and `npm run build` passed; Vite reports the existing Mapbox chunk-size advisory. |
| Map canvas rendering | Not verified in this browser | WebGL was unavailable; the UI displayed its fallback. Verify the colored route layer in a WebGL-enabled browser with a valid public Mapbox token. |
| Live provider trip request | Not verified | Requires valid Mapbox credentials and provider network access. |

There is currently no dedicated automated frontend test runner; the browser
checks above are a repeatable manual/mock checklist.

## Production and deployment status

Settings support environment-driven secrets, hosts, CORS, database URLs, and
production static files. Production deployment has **not** yet been completed
or verified. No live API URL, frontend URL, screenshot, hosting provider, or
deployment credentials are currently configured. Choose a backend and frontend
host, configure their environment variables, then run migrations, static-file
collection, health checks, and a real trip request before treating the service
as deployed.

For production checks, use:

```sh
cd backend
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
```

Set `DATABASE_URL` to a managed PostgreSQL service and confirm the deployment
platform provides the HTTPS proxy header expected by Django's secure redirect
configuration.
