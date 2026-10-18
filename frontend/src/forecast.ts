import type { Checkpoint, CheckpointForecast } from './types'

export function getCheckpointForecast(
  checkpoint: Checkpoint,
  forecastHour: number,
  departureUtc: string,
): CheckpointForecast {
  const forecast = checkpoint.forecast?.find(
    (entry) => entry.forecast_hour === forecastHour,
  )

  if (forecast) {
    if (forecast.weather_available) return forecast

    return {
      ...forecast,
      risk_level: null,
      risk_label: 'Unknown',
    }
  }

  return {
    forecast_hour: forecastHour,
    forecast_time: new Date(
      new Date(departureUtc).getTime() + forecastHour * 60 * 60 * 1000,
    ).toISOString(),
    risk_level: null,
    risk_label: 'Unknown',
    weather_available: false,
    weather_reason: 'Forecast data is unavailable for this hour.',
  }
}
