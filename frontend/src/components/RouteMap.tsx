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

interface RouteMapProps {
  origin: Location
  destination: Location
  routes: AnalyzedRoute[]
  selectedRouteId: number | string | null
}

const ROUTE_COLORS = ['#2563eb', '#e07b36', '#8b5cf6', '#0d9488']
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN

function checkpointColor(checkpoint: Checkpoint) {
  if (!checkpoint.weather_available) return '#737c8b'
  if (checkpoint.risk_label === 'No Travel' || checkpoint.risk_label === 'Severe') return '#dc4545'
  if (checkpoint.risk_label === 'High') return '#e07b36'
  if (checkpoint.risk_label === 'Moderate') return '#d1a328'
  return '#278669'
}

export default function RouteMap({
  origin,
  destination,
  routes,
  selectedRouteId,
}: RouteMapProps) {
  const mapRef = useRef<MapRef>(null)
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<{
    checkpoint: Checkpoint
    index: number
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
  }, [coordinates])

  useEffect(() => {
    fitSelectedRoute()
  }, [fitSelectedRoute])

  if (!MAPBOX_TOKEN) {
    return (
      <div className="map-unavailable">
        <span className="map-unavailable-icon" aria-hidden="true">⌖</span>
        <strong>Map preview needs a Mapbox token</strong>
        <span>Set <code>VITE_MAPBOX_ACCESS_TOKEN</code> in the frontend environment to render returned route geometry.</span>
      </div>
    )
  }

  return (
    <div className="route-map-container">
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: (origin.longitude + destination.longitude) / 2,
          latitude: (origin.latitude + destination.latitude) / 2,
          zoom: 7,
        }}
        onLoad={fitSelectedRoute}
        mapboxAccessToken={MAPBOX_TOKEN}
        mapStyle="mapbox://styles/mapbox/streets-v12"
        attributionControl
        reuseMaps
      >
        <NavigationControl position="top-right" />
        {routes.map((route, index) => {
          if (!route.geometry?.coordinates?.length) return null
          const isSelected = route.route_id === selectedRouteId
          const color = ROUTE_COLORS[index % ROUTE_COLORS.length]

          return (
            <Source
              id={`route-source-${index}`}
              key={`route-source-${route.route_id ?? index}`}
              type="geojson"
              data={{
                type: 'Feature',
                properties: {},
                geometry: route.geometry,
              }}
            >
              <Layer
                id={`route-line-${index}`}
                type="line"
                layout={{ 'line-cap': 'round', 'line-join': 'round' }}
                paint={{
                  'line-color': color,
                  'line-width': isSelected ? 6 : 3,
                  'line-opacity': isSelected ? 0.95 : 0.55,
                  ...(isSelected ? {} : { 'line-dasharray': [2, 1.5] }),
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
              style={{ '--checkpoint-color': checkpointColor(checkpoint) } as CSSProperties}
              type="button"
              aria-label={`Checkpoint at ${checkpoint.distance_miles} miles: ${checkpoint.risk_label}`}
              onClick={() => setSelectedCheckpoint({ checkpoint, index })}
            >
              {index + 1}
            </button>
          </Marker>
        ))}

        <Marker longitude={origin.longitude} latitude={origin.latitude} anchor="bottom">
          <div className="endpoint-marker endpoint-origin"><span>A</span><b>Origin</b></div>
        </Marker>
        <Marker longitude={destination.longitude} latitude={destination.latitude} anchor="bottom">
          <div className="endpoint-marker endpoint-destination"><span>B</span><b>Destination</b></div>
        </Marker>

        {selectedCheckpoint && (
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
              <span>{new Date(selectedCheckpoint.checkpoint.eta).toLocaleString()}</span>
              <b>{selectedCheckpoint.checkpoint.risk_label}</b>
              {!selectedCheckpoint.checkpoint.weather_available && (
                <span>{selectedCheckpoint.checkpoint.weather_reason ?? 'Weather unavailable'}</span>
              )}
            </div>
          </Popup>
        )}
      </Map>
    </div>
  )
}
