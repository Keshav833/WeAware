import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import Map, {
  Layer,
  Marker,
  NavigationControl,
  Popup,
  Source,
  type MapRef,
} from 'react-map-gl/mapbox'
import 'mapbox-gl/dist/mapbox-gl.css'
import type { AnalyzedRoute, Checkpoint, Location } from '../types'
import { getCheckpointForecast } from '../forecast'

type RiskLabel = 'Low' | 'Moderate' | 'High' | 'Severe' | 'No Travel' | 'Unknown'
type HeatmapFeature = {
  type: 'Feature'
  properties: { riskLabel: RiskLabel; color: string }
  geometry: { type: 'LineString'; coordinates: [number, number][] }
}

interface RouteMapProps {
  origin: Location
  destination: Location
  routes: AnalyzedRoute[]
  selectedRouteId: number | string | null
  onSelectRoute: (routeId: number | string | null) => void
  forecastHour: number
  departureUtc: string
  preview?: boolean
}

const RISK_COLORS: Record<RiskLabel, string> = {
  Low: '#278669',
  Moderate: '#d1a328',
  High: '#e07b36',
  Severe: '#dc4545',
  'No Travel': '#9f2638',
  Unknown: '#737c8b',
}
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN

function browserSupportsWebGL() {
  if (typeof document === 'undefined' || typeof WebGLRenderingContext === 'undefined') {
    return false
  }
  return document.createElement('canvas').getContext('webgl') !== null
}

function getCheckpointRiskLabel(
  checkpoint: Checkpoint,
  forecastHour: number,
  departureUtc: string,
): RiskLabel {
  const forecast = getCheckpointForecast(checkpoint, forecastHour, departureUtc)
  if (!forecast.weather_available) return 'Unknown'
  return Object.hasOwn(RISK_COLORS, forecast.risk_label)
    ? forecast.risk_label as RiskLabel
    : 'Unknown'
}

function distanceMiles(start: [number, number], end: [number, number]) {
  const radians = Math.PI / 180
  const latitudeDelta = (end[1] - start[1]) * radians
  const longitudeDelta = (end[0] - start[0]) * radians
  const startLatitude = start[1] * radians
  const endLatitude = end[1] * radians
  const haversine = Math.sin(latitudeDelta / 2) ** 2
    + Math.cos(startLatitude) * Math.cos(endLatitude)
    * Math.sin(longitudeDelta / 2) ** 2
  return 3958.7613 * 2 * Math.asin(Math.sqrt(Math.min(1, haversine)))
}

function routeHeatmapFeatures(
  route: AnalyzedRoute,
  forecastHour: number,
  departureUtc: string,
): HeatmapFeature[] {
  const coordinates = route.geometry?.coordinates
  if (!coordinates || coordinates.length < 2) return []

  const cumulativeMiles = [0]
  for (let index = 1; index < coordinates.length; index += 1) {
    cumulativeMiles.push(
      cumulativeMiles[index - 1]
      + distanceMiles(coordinates[index - 1], coordinates[index]),
    )
  }
  const routeLength = cumulativeMiles[cumulativeMiles.length - 1]
  if (routeLength <= 0) return []

  const pointAtDistance = (distance: number): [number, number] => {
    const clampedDistance = Math.max(0, Math.min(routeLength, distance))
    for (let index = 1; index < cumulativeMiles.length; index += 1) {
      if (clampedDistance > cumulativeMiles[index]) continue
      const segmentLength = cumulativeMiles[index] - cumulativeMiles[index - 1]
      const fraction = segmentLength === 0
        ? 0
        : (clampedDistance - cumulativeMiles[index - 1]) / segmentLength
      return [
        coordinates[index - 1][0] + (coordinates[index][0] - coordinates[index - 1][0]) * fraction,
        coordinates[index - 1][1] + (coordinates[index][1] - coordinates[index - 1][1]) * fraction,
      ]
    }
    return coordinates[coordinates.length - 1]
  }

  const sortedCheckpoints = route.checkpoints
    .map((checkpoint) => ({
      distance: Math.max(0, Math.min(routeLength, checkpoint.distance_miles)),
      riskLabel: getCheckpointRiskLabel(checkpoint, forecastHour, departureUtc),
    }))
    .sort((left, right) => left.distance - right.distance)

  if (!sortedCheckpoints.length) {
    return [{
      type: 'Feature',
      properties: { riskLabel: 'Unknown', color: RISK_COLORS.Unknown },
      geometry: { type: 'LineString', coordinates },
    }]
  }

  return sortedCheckpoints.flatMap((checkpoint, index) => {
    const previous = sortedCheckpoints[index - 1]
    const next = sortedCheckpoints[index + 1]
    const startDistance = previous
      ? (previous.distance + checkpoint.distance) / 2
      : 0
    const endDistance = next
      ? (checkpoint.distance + next.distance) / 2
      : routeLength
    if (endDistance <= startDistance) return []

    const sectionCoordinates: [number, number][] = [
      pointAtDistance(startDistance),
      ...coordinates.filter((_, coordinateIndex) =>
        cumulativeMiles[coordinateIndex] > startDistance
        && cumulativeMiles[coordinateIndex] < endDistance,
      ),
      pointAtDistance(endDistance),
    ]

    return [{
      type: 'Feature' as const,
      properties: {
        riskLabel: checkpoint.riskLabel,
        color: RISK_COLORS[checkpoint.riskLabel],
      },
      geometry: { type: 'LineString' as const, coordinates: sectionCoordinates },
    }]
  })
}

export default function RouteMap({
  origin,
  destination,
  routes,
  selectedRouteId,
  onSelectRoute,
  forecastHour,
  departureUtc,
  preview = false,
}: RouteMapProps) {
  const mapRef = useRef<MapRef>(null)
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<{
    checkpoint: Checkpoint
    index: number
    routeId: number | string | null
  } | null>(null)

  const selectedRoute = routes.find((route) => route.route_id === selectedRouteId)
    ?? routes[0]
    ?? null

  const coordinates = useMemo(
    () => selectedRoute?.geometry?.coordinates ?? [
      [origin.longitude, origin.latitude],
      [destination.longitude, destination.latitude],
    ],
    [destination.latitude, destination.longitude, origin.latitude, origin.longitude, selectedRoute],
  )

  const fitSelectedRoute = useCallback(() => {
    if (preview) return
    if (!coordinates.length) return
    const longitudes = coordinates.map(([longitude]) => longitude)
    const latitudes = coordinates.map(([, latitude]) => latitude)
    mapRef.current?.fitBounds(
      [
        [Math.min(...longitudes), Math.min(...latitudes)],
        [Math.max(...longitudes), Math.max(...latitudes)],
      ],
      {
        padding: { top: 58, bottom: 58, left: 58, right: 58 },
        duration: 700,
        maxZoom: 14,
      },
    )
  }, [coordinates, preview])

  useEffect(() => {
    fitSelectedRoute()
  }, [fitSelectedRoute])

  if (!MAPBOX_TOKEN || !browserSupportsWebGL()) {
    return (
      <div className={`map-unavailable${preview ? ' map-preview-unavailable' : ''}`}>
        <span className="map-unavailable-icon" aria-hidden="true">⌖</span>
        {preview ? (
          <>
            <div className="map-preview-labels" aria-hidden="true">
              <span>Canada</span><span>United States</span><span>Mexico</span>
              <span>Pacific Ocean</span><span>Atlantic Ocean</span>
            </div>
            <div className="map-preview-message">
              <strong>Map preview</strong>
              <span>{!MAPBOX_TOKEN
                ? 'Add a Mapbox token to explore the live map and trip routes.'
                : 'Enable WebGL to explore the live map and trip routes.'}</span>
            </div>
          </>
        ) : !MAPBOX_TOKEN ? (
          <>
            <strong>Map preview needs a Mapbox token</strong>
            <span>Set <code>VITE_MAPBOX_ACCESS_TOKEN</code> in the frontend environment to render returned route geometry.</span>
          </>
        ) : (
          <>
            <strong>Interactive map unavailable in this browser</strong>
            <span>Enable WebGL to inspect the route heatmap. Forecast details remain available below.</span>
          </>
        )}
      </div>
    )
  }

  return (
    <div className={`route-map-container${preview ? ' route-map-preview' : ''}`}>
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: preview ? -98 : (origin.longitude + destination.longitude) / 2,
          latitude: preview ? 39 : (origin.latitude + destination.latitude) / 2,
          zoom: preview ? 3.5 : 7,
        }}
        onLoad={fitSelectedRoute}
        interactiveLayerIds={routes.flatMap((route, index) =>
          route.geometry?.coordinates.length ? [`route-line-${index}`] : [],
        )}
        onClick={(event) => {
          const layerId = event.features?.[0]?.layer?.id
          if (!layerId?.startsWith('route-line-')) return

          const routeIndex = Number(layerId.slice('route-line-'.length))
          const route = routes[routeIndex]
          if (route) onSelectRoute(route.route_id)
        }}
        mapboxAccessToken={MAPBOX_TOKEN}
        mapStyle="mapbox://styles/mapbox/satellite-streets-v12"
        attributionControl
        reuseMaps
      >
        <NavigationControl position="top-right" />
        {routes
          .map((route, index) => ({ route, index }))
          .sort((left, right) =>
            Number(left.route.route_id === selectedRouteId)
            - Number(right.route.route_id === selectedRouteId),
          )
          .map(({ route, index }) => {
          if (!route.geometry?.coordinates?.length) return null
          const isSelected = route.route_id === selectedRouteId
          const heatmapFeatures = routeHeatmapFeatures(route, forecastHour, departureUtc)

          return (
            <Source
              id={`route-source-${index}`}
              key={`route-source-${route.route_id ?? index}`}
              type="geojson"
              data={{
                type: 'FeatureCollection',
                features: heatmapFeatures,
              }}
            >
              <Layer
                id={`route-line-${index}`}
                type="line"
                layout={{ 'line-cap': 'round', 'line-join': 'round' }}
                paint={{
                  'line-color': ['get', 'color'],
                  'line-width': isSelected ? 7 : 4,
                  'line-opacity': isSelected ? 0.95 : 0.3,
                }}
              />
            </Source>
          )
        })}

        {selectedRoute?.checkpoints.map((checkpoint, index) => (
          <Marker
            key={`checkpoint-${selectedRoute.route_id}-${index}`}
            longitude={checkpoint.longitude}
            latitude={checkpoint.latitude}
            anchor="center"
          >
            <button
              className="checkpoint-map-marker"
              style={{ '--checkpoint-color': RISK_COLORS[getCheckpointRiskLabel(checkpoint, forecastHour, departureUtc)] } as CSSProperties}
              type="button"
              aria-label={`Checkpoint at ${checkpoint.distance_miles} miles: ${getCheckpointRiskLabel(checkpoint, forecastHour, departureUtc)}`}
              onClick={() => setSelectedCheckpoint({
                checkpoint,
                index,
                routeId: selectedRoute.route_id,
              })}
            >
              {index + 1}
            </button>
          </Marker>
        ))}

        {!preview && (
          <>
            <Marker longitude={origin.longitude} latitude={origin.latitude} anchor="bottom">
              <div className="endpoint-marker endpoint-origin"><span>A</span><b>Origin</b></div>
            </Marker>
            <Marker longitude={destination.longitude} latitude={destination.latitude} anchor="bottom">
              <div className="endpoint-marker endpoint-destination"><span>B</span><b>Destination</b></div>
            </Marker>
          </>
        )}

        {selectedCheckpoint && selectedCheckpoint.routeId === selectedRoute?.route_id && (
          <Popup
            longitude={selectedCheckpoint.checkpoint.longitude}
            latitude={selectedCheckpoint.checkpoint.latitude}
            anchor="bottom"
            closeOnClick={false}
            onClose={() => setSelectedCheckpoint(null)}
          >
            <div className="checkpoint-popup">
              <strong>Checkpoint {selectedCheckpoint.index + 1}</strong>
              <span>{selectedCheckpoint.checkpoint.distance_miles.toFixed(1)} route miles</span>
              <span>Arrival: {new Date(selectedCheckpoint.checkpoint.eta).toLocaleString()}</span>
              {(() => {
                const forecast = getCheckpointForecast(
                  selectedCheckpoint.checkpoint,
                  forecastHour,
                  departureUtc,
                )
                return (
                  <>
                    <span>Forecast: {new Date(forecast.forecast_time).toLocaleString()}</span>
                    <span className={`risk-label risk-${getCheckpointRiskLabel(selectedCheckpoint.checkpoint, forecastHour, departureUtc).toLowerCase().replaceAll(' ', '-')}`}>
                      {getCheckpointRiskLabel(selectedCheckpoint.checkpoint, forecastHour, departureUtc)}
                    </span>
                    {forecast.weather_available ? (
                      <>
                        <span>Wind: {forecast.weather?.wind_mph.toFixed(1) ?? '—'} mph</span>
                        <span>Rain: {forecast.weather?.rain_inches.toFixed(2) ?? '—'} in/hr</span>
                        <span>Snow: {forecast.weather?.snow_inches.toFixed(2) ?? '—'} in/hr</span>
                      </>
                    ) : (
                      <span>{forecast.weather_reason ?? 'Weather unavailable for this hour.'}</span>
                    )}
                  </>
                )
              })()}
            </div>
          </Popup>
        )}
      </Map>
    </div>
  )
}
