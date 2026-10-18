# WeAware - Truck Routing

A React + Django web app that helps a truck driver choose the safest route based on weather, load weight and travel time.

## What it does

The user enters an origin, destination, departure date/time and load weight. The app then:

1. Generates 3 route options using a routing API.
2. Samples weather every 10, 25 or 50 miles along each route, using the truck's estimated arrival time at each checkpoint.
3. Classifies weather risk at each checkpoint using the risk and load rules below.
4. Recommends the best route, balancing weather risk and travel time.
5. Shows all routes, checkpoints, risk levels, ETAs and route summaries on a map.
6. Shows a weather heatmap along the trip corridor with a 0-48 hour forecast slider.

## Tech stack

- **Frontend:** React, Map library for the map and heatmap
- **Backend:** Django, Django REST Framework
- **Routing and geocoding:** third-party API
- **Weather:** Open-Meteo (hourly forecast, no API key needed)

## How it works

```
form input -> geocode -> 3 routes -> checkpoints -> ETA at each checkpoint
-> forecast at that ETA -> risk level -> route stats -> recommendation -> map + heatmap
```

## Risk rules

The worst of wind, rain and snow at a checkpoint sets its risk level.

| Condition | Low | Moderate | High | Severe | No Travel |
|---|---|---|---|---|---|
| Wind (mph) | <25 | 25-34 | 35-44 | 45-54 | >=55 |
| Rain (in/hr) | <0.10 | 0.10-0.25 | 0.25-0.50 | 0.50-1.00 | >1.00 |
| Snow (in/hr) | <0.5 | 0.5-1.0 | 1.0-2.0 | 2.0-3.0 | >3.0 |

Load rules override the base level:

- Wind >= 55 mph: No Travel for any load
- Wind 45-54 mph and load > 30,000 lb: No Travel
- Wind 35-44 mph and load > 40,000 lb: Severe

## Route recommendation

Routes are compared in this order, and the first difference decides:

1. Fewest Severe miles
2. Fewest High miles
3. Lowest average risk
4. Shortest travel time

Routes containing No Travel conditions are ranked below routes without them. If every route has No Travel conditions, the least bad one is recommended with a warning to consider delaying departure.

## Assumptions

- Each checkpoint represents the stretch of road around it, and miles are totaled per risk level.
- Average risk is weighted by miles (Low = 0, Moderate = 1, High = 2, Severe = 3, No Travel = 4).
- The forecast hour nearest to the truck's ETA is used at each checkpoint.
- All times are handled in UTC internally and converted for display.
- Route durations come from the routing API and do not include weather slowdowns.

## Running locally

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

API keys are read from environment variables. Copy `.env.example` to `.env` in each folder and fill in your keys.

## Tests

```bash
cd backend
python manage.py test
```