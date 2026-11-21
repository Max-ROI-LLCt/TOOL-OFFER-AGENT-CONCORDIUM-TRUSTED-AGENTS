"""Seller-side renderer. Its output is untrusted input to the independent buyer."""

from .weather_report_contract import (
    REPORT_SCHEMA, ZONE, WeatherOrder, IndependentForecast, attribution, encode_json,
    limitations, read_forecast, source_projection, utc, utc_text,
)


def render_report(order: WeatherOrder, source: IndependentForecast, *, generated_at_utc: str):
    order.validate()
    utc(generated_at_utc)
    forecast = read_forecast(order, source.body)
    hourly = forecast['hourly']
    positions = {epoch: index for index, epoch in enumerate(hourly['time'])}
    boundaries = order.boundaries()
    rows = []
    for start, end in zip(boundaries, boundaries[1:]):
        rows.append({
            'interval_start_local': start.astimezone(ZONE).isoformat(timespec='seconds'),
            'interval_end_local': end.astimezone(ZONE).isoformat(timespec='seconds'),
            'interval_start_utc': utc_text(start), 'interval_end_utc': utc_text(end),
            'temperature_2m_celsius': hourly['temperature_2m'][positions[int(start.timestamp())]],
            'precipitation_probability_percent': hourly['precipitation_probability'][positions[int(end.timestamp())]],
            'source_id': 'weather-1', 'temperature_source_time_utc': utc_text(start),
            'precipitation_source_time_utc': utc_text(end)})
    temperatures = [row['temperature_2m_celsius'] for row in rows]
    probabilities = [row['precipitation_probability_percent'] for row in rows]
    lowest = min(range(len(rows)), key=lambda index: (probabilities[index], rows[index]['interval_start_utc']))
    report = {
        'schema': REPORT_SCHEMA, 'proposal_id': order.proposal_id,
        'prepared_by_account': order.seller_account, 'buyer_account': order.buyer_account,
        'generated_at_utc': generated_at_utc, 'forecast_date': order.forecast_date,
        'timezone': 'Europe/Berlin',
        'location': {'city': 'Berlin', 'country': 'DE', 'requested_latitude': 52.52,
                     'requested_longitude': 13.41, 'source_grid_latitude': forecast['latitude'],
                     'source_grid_longitude': forecast['longitude']},
        'units': {'temperature_2m': 'degC', 'precipitation_probability': 'percent'},
        'source': source_projection(source), 'hourly': rows,
        'summary': {'minimum_temperature_2m_celsius': min(temperatures),
                    'maximum_temperature_2m_celsius': max(temperatures),
                    'maximum_precipitation_probability_percent': max(probabilities),
                    'lowest_precipitation_probability_interval_start_local': rows[lowest]['interval_start_local']},
        'attribution': attribution(order), 'limitations': limitations(order)}
    return {'report.json': encode_json(report), 'forecast-source.json': source.body}
