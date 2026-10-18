export interface Location {
  name: string
  longitude: number
  latitude: number
}

export interface RouteGeometry {
  type: 'LineString'
  coordinates: [number, number][]
}

export interface Checkpoint {
  distance_miles: number
  latitude: number
  longitude: number
  eta: string
  risk_level: number | null
  risk_label: string
  weather_available: boolean
  weather_reason?: string
  weather?: {
    wind_mph: number
    rain_inches: number
    snow_inches: number
    weather_time: string
  }
  forecast?: CheckpointForecast[]
}

export interface CheckpointForecast {
  forecast_hour: number
  forecast_time: string
  risk_level: number | null
  risk_label: string
  weather_available: boolean
  weather_reason?: string | null
  weather?: {
    wind_mph: number
    rain_inches: number
    snow_inches: number
    weather_time: string
  }
}

export interface RiskSegment {
  start_miles: number
  end_miles: number
  risk_level: number | null
}

export interface RouteScore {
  total_distance_miles: number
  severe_miles: number
  high_miles: number
  no_travel_miles: number
  average_risk_score: number
  duration_seconds: number
  risk_segments_count: number
}

export interface RouteSummary {
  checkpoint_count: number
  risk_counts: Record<'Low' | 'Moderate' | 'High' | 'Severe' | 'No Travel', number>
  unknown_weather_count: number
  known_checkpoint_count: number
  average_risk_score: number | null
  highest_risk: string
  has_no_travel: boolean
}

export interface AnalyzedRoute {
  route_id: number | string | null
  distance_miles: number
  duration_seconds: number
  geometry?: RouteGeometry
  checkpoints: Checkpoint[]
  summary: RouteSummary
  comparison?: {
    scoring_available: boolean
    scoring_reason?: string | null
    risk_segments: RiskSegment[]
    score?: RouteScore
  }
  scoring_available: boolean
  scoring_reason?: string | null
  score?: RouteScore | null
  rank?: number | null
  recommended?: boolean
}

export interface TripAnalysisResponse {
  origin: Location
  destination: Location
  departure_utc: string
  routes: AnalyzedRoute[]
  route_count: number
  recommendation_route_id: number | string | null
  recommendation_note?: string
}
