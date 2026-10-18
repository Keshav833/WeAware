import { useState, type FormEvent } from 'react'
import axios from 'axios'
import apiClient from './api/clients'
import RouteMap from './components/RouteMap'
import type { AnalyzedRoute, TripAnalysisResponse } from './types'
import './App.css'

interface TripFormValues {
  origin: string
  destination: string
  departure: string
  loadLb: string
  intervalMiles: '10' | '25' | '50'
}

function toLocalDateTimeValue(date: Date) {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return localDate.toISOString().slice(0, 16)
}

function getInitialFormValues(): TripFormValues {
  const departure = new Date()
  departure.setHours(departure.getHours() + 1)

  return {
    origin: '',
    destination: '',
    departure: toLocalDateTimeValue(departure),
    loadLb: '',
    intervalMiles: '25',
  }
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const responseData: unknown = error.response?.data
    if (responseData && typeof responseData === 'object') {
      const data = responseData as Record<string, unknown>
      if (typeof data.detail === 'string') return data.detail

      const messages = Object.entries(data).flatMap(([field, value]) => {
        const entries = Array.isArray(value) ? value : [value]
        return entries
          .filter((entry): entry is string => typeof entry === 'string')
          .map((entry) => `${field}: ${entry}`)
      })
      if (messages.length) return messages.join(' ')
    }
    return error.message || 'The analysis request failed. Please try again.'
  }

  return 'Something went wrong while analyzing this trip. Please try again.'
}

function formatDuration(seconds: number) {
  const totalMinutes = Math.round(seconds / 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return hours > 0 ? `${hours} hr ${minutes} min` : `${minutes} min`
}

function formatMiles(miles: number) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 }).format(miles)
}

function RouteCard({
  route,
  isSelected,
  onSelect,
}: {
  route: AnalyzedRoute
  isSelected: boolean
  onSelect: () => void
}) {
  const unknownMiles = route.comparison?.risk_segments
    .filter((segment) => segment.risk_level === null)
    .reduce((total, segment) => total + segment.end_miles - segment.start_miles, 0) ?? 0

  return (
    <button
      className={`route-card${isSelected ? ' route-card-selected' : ''}`}
      type="button"
      onClick={onSelect}
      aria-pressed={isSelected}
    >
      <span className="route-card-heading">
        <span className="route-name">Route {route.route_id ?? 'alternative'}</span>
        {route.recommended && <span className="recommended-pill">Recommended</span>}
        {!route.recommended && route.rank !== null && route.rank !== undefined && (
          <span className="rank-pill">Rank #{route.rank}</span>
        )}
      </span>
      <span className="route-facts">
        <span>{formatMiles(route.distance_miles)} mi</span>
        <span>{formatDuration(route.duration_seconds)}</span>
        <span>{route.checkpoints.length} checkpoints</span>
      </span>

      {route.scoring_available && route.score ? (
        <span className="route-risk-summary">
          <span><i className="risk-dot severe" />{formatMiles(route.score.severe_miles)} severe mi</span>
          <span><i className="risk-dot high" />{formatMiles(route.score.high_miles)} high mi</span>
          <span><i className="risk-dot unknown" />{formatMiles(unknownMiles)} unknown mi</span>
        </span>
      ) : (
        <span className="incomplete-notice">
          Risk scoring unavailable: {route.scoring_reason ?? route.comparison?.scoring_reason ?? 'weather coverage is incomplete.'}
          {unknownMiles > 0 && ` ${formatMiles(unknownMiles)} mi have unknown weather.`}
        </span>
      )}
    </button>
  )
}

function App() {
  const [formValues, setFormValues] = useState(getInitialFormValues)
  const [analysis, setAnalysis] = useState<TripAnalysisResponse | null>(null)
  const [selectedRouteId, setSelectedRouteId] = useState<number | string | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [formError, setFormError] = useState('')

  const selectedRoute = analysis?.routes.find(
    (route) => route.route_id === selectedRouteId,
  ) ?? null

  function updateField<Key extends keyof TripFormValues>(
    field: Key,
    value: TripFormValues[Key],
  ) {
    setFormValues((current) => ({ ...current, [field]: value }))
    setFormError('')
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage('')
    setFormError('')

    const departure = new Date(formValues.departure)
    const loadLb = Number(formValues.loadLb)

    if (!formValues.origin.trim() || !formValues.destination.trim()) {
      setFormError('Enter both an origin and a destination.')
      return
    }
    if (formValues.origin.trim().toLocaleLowerCase() === formValues.destination.trim().toLocaleLowerCase()) {
      setFormError('Origin and destination must be different.')
      return
    }
    if (!formValues.departure || Number.isNaN(departure.getTime()) || departure <= new Date()) {
      setFormError('Choose a departure time in the future.')
      return
    }
    if (!Number.isFinite(loadLb) || loadLb <= 0) {
      setFormError('Enter a truck load greater than zero pounds.')
      return
    }

    setLoading(true)
    setAnalysis(null)
    setSelectedRouteId(null)

    try {
      const response = await apiClient.post<TripAnalysisResponse>('/analyze', {
        origin: formValues.origin.trim(),
        destination: formValues.destination.trim(),
        departure_utc: departure.toISOString(),
        load_lb: loadLb,
        interval_miles: Number(formValues.intervalMiles),
      })
      setAnalysis(response.data)
      const recommendationId = response.data.recommendation_route_id
      setSelectedRouteId(
        recommendationId
        ?? response.data.routes[0]?.route_id
        ?? null,
      )
    } catch (error) {
      setErrorMessage(getErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="WeAware home">
          <span className="brand-mark" aria-hidden="true">W</span>
          <span>WeAware</span>
        </a>
        <span className="header-caption">Weather-aware truck routing</span>
        <span className="header-status"><i /> Route safety planner</span>
      </header>

      <main className="main-content">
        <section className="intro">
          <div>
            <p className="eyebrow">PLAN WITH CONFIDENCE</p>
            <h1>Find a safer way forward.</h1>
            <p className="intro-copy">
              Compare weather risk across real driving routes before your truck rolls.
            </p>
          </div>
          <div className="intro-note">
            <span aria-hidden="true">↗</span>
            <p>Forecast coverage can vary by checkpoint. Incomplete routes are never recommended.</p>
          </div>
        </section>

        <div className="workspace">
          <aside className="trip-panel">
            <div className="panel-heading">
              <span className="step-number">01</span>
              <div>
                <h2>Plan your trip</h2>
                <p>Enter your route and truck details.</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} noValidate>
              <label className="field">
                <span>Origin</span>
                <input
                  autoComplete="address-level2"
                  name="origin"
                  placeholder="City, state or address"
                  required
                  value={formValues.origin}
                  onChange={(event) => updateField('origin', event.target.value)}
                />
              </label>
              <label className="field">
                <span>Destination</span>
                <input
                  autoComplete="address-level2"
                  name="destination"
                  placeholder="Where are you headed?"
                  required
                  value={formValues.destination}
                  onChange={(event) => updateField('destination', event.target.value)}
                />
              </label>
              <label className="field">
                <span>Departure date &amp; time <small>Local time</small></span>
                <input
                  name="departure"
                  type="datetime-local"
                  required
                  min={toLocalDateTimeValue(new Date())}
                  value={formValues.departure}
                  onChange={(event) => updateField('departure', event.target.value)}
                />
              </label>

              <div className="field-row">
                <label className="field">
                  <span>Truck load <small>lb</small></span>
                  <input
                    name="loadLb"
                    type="number"
                    min="0.01"
                    step="0.01"
                    inputMode="decimal"
                    placeholder="e.g. 24000"
                    required
                    value={formValues.loadLb}
                    onChange={(event) => updateField('loadLb', event.target.value)}
                  />
                </label>
                <label className="field">
                  <span>Checkpoints <small>miles</small></span>
                  <select
                    name="intervalMiles"
                    value={formValues.intervalMiles}
                    onChange={(event) => updateField('intervalMiles', event.target.value as TripFormValues['intervalMiles'])}
                  >
                    <option value="10">Every 10 mi</option>
                    <option value="25">Every 25 mi</option>
                    <option value="50">Every 50 mi</option>
                  </select>
                </label>
              </div>

              {formError && <p className="form-error" role="alert">{formError}</p>}
              {errorMessage && <p className="form-error api-error" role="alert">{errorMessage}</p>}

              <button className="submit-button" type="submit" disabled={loading}>
                {loading ? (
                  <><span className="spinner" aria-hidden="true" /> Analyzing routes…</>
                ) : (
                  <>Analyze trip <span aria-hidden="true">→</span></>
                )}
              </button>
              <p className="form-footnote">Route analysis uses live provider data. Weather gaps are shown as unknown.</p>
            </form>
          </aside>

          <section className="map-panel" aria-label="Route map">
            <div className="map-heading">
              <div>
                <span className="step-number">02</span>
                <h2>Route map</h2>
              </div>
              {analysis && <span className="map-route-count">{analysis.route_count} {analysis.route_count === 1 ? 'route' : 'routes'} found</span>}
            </div>
            {analysis ? (
              <RouteMap
                origin={analysis.origin}
                destination={analysis.destination}
                routes={analysis.routes}
                selectedRouteId={selectedRouteId}
              />
            ) : (
              <div className="map-placeholder">
                <div className="map-placeholder-art" aria-hidden="true">
                  <span className="map-road map-road-one" />
                  <span className="map-road map-road-two" />
                  <span className="map-pin map-pin-start">A</span>
                  <span className="map-pin map-pin-end">B</span>
                </div>
                <div className="map-placeholder-copy">
                  <strong>Your routes will appear here</strong>
                  <span>Submit a trip to see provider-supplied routes and checkpoint weather.</span>
                </div>
              </div>
            )}
            {analysis && analysis.routes.length > 0 && (
              <div className="map-legend" aria-label="Map route legend">
                {analysis.routes.map((route, index) => (
                  <button
                    className={route.route_id === selectedRouteId ? 'legend-item legend-active' : 'legend-item'}
                    key={`${route.route_id ?? 'route'}-${index}`}
                    onClick={() => setSelectedRouteId(route.route_id)}
                    type="button"
                  >
                    <i className={`legend-line route-color-${index % 4}`} />
                    Route {route.route_id ?? index + 1}
                  </button>
                ))}
                <span className="legend-marker"><i /> Checkpoint</span>
              </div>
            )}
          </section>
        </div>

        <section className="results-section" aria-live="polite">
          <div className="results-heading">
            <div>
              <span className="step-number">03</span>
              <h2>Route alternatives</h2>
            </div>
            {analysis && <span className="results-count">{analysis.route_count} returned by routing provider</span>}
          </div>

          {analysis ? (
            analysis.routes.length > 0 ? (
              <>
                {analysis.recommendation_note && (
                  <p className="estimate-note"><span aria-hidden="true">ⓘ</span>{analysis.recommendation_note}</p>
                )}
                <div className="route-list">
                  {analysis.routes.map((route) => (
                    <RouteCard
                      key={route.route_id ?? 'route'}
                      route={route}
                      isSelected={route.route_id === selectedRouteId}
                      onSelect={() => setSelectedRouteId(route.route_id)}
                    />
                  ))}
                </div>
              </>
            ) : (
              <div className="empty-results">
                <strong>No routes were returned.</strong>
                <span>Try a nearby origin or destination and submit again.</span>
              </div>
            )
          ) : (
            <div className="empty-results empty-results-muted">
              <strong>Alternatives will show up after analysis.</strong>
              <span>Risk estimates, route rankings, and forecast coverage are compared here.</span>
            </div>
          )}
        </section>

        {selectedRoute && (
          <section className="checkpoint-section">
            <div className="results-heading">
              <div>
                <span className="step-number">04</span>
                <h2>Checkpoint forecast</h2>
              </div>
              <span className="results-count">Route {selectedRoute.route_id ?? ''}</span>
            </div>
            {selectedRoute.checkpoints.length ? (
              <div className="checkpoint-table-wrap">
                <table className="checkpoint-table">
                  <thead>
                    <tr>
                      <th>Checkpoint</th>
                      <th>Estimated arrival</th>
                      <th>Weather risk</th>
                      <th>Forecast</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedRoute.checkpoints.map((checkpoint, index) => (
                      <tr key={`${selectedRoute.route_id}-${checkpoint.distance_miles}-${index}`}>
                        <td>{formatMiles(checkpoint.distance_miles)} mi</td>
                        <td>{new Date(checkpoint.eta).toLocaleString()}</td>
                        <td>
                          <span className={`risk-label ${checkpoint.weather_available ? `risk-${checkpoint.risk_label.toLowerCase().replaceAll(' ', '-')}` : 'risk-unknown'}`}>
                            {checkpoint.risk_label}
                          </span>
                        </td>
                        <td>{checkpoint.weather_available ? 'Available' : checkpoint.weather_reason ?? 'Unavailable'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-results">
                <strong>No intermediate checkpoints on this route.</strong>
                <span>The selected route may be shorter than the chosen checkpoint interval.</span>
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="site-footer">
        <span>WeAware <span aria-hidden="true">·</span> Safer decisions, mile by mile.</span>
        <span>Risk miles are estimates based on checkpoint weather.</span>
      </footer>
    </div>
  )
}

export default App
