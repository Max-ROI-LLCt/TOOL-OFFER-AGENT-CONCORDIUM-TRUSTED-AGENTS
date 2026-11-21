"""Explicit synthetic sources, clocks and business acceptance, never wallet consent."""

from dataclasses import replace
from datetime import date, datetime, time, timedelta
from pathlib import Path

from tool_offer_agent.weather_report_contract import (
    PROPOSAL_PATH, ZONE, IndependentForecast, ReportWindows, SourceUseReview,
    WeatherOrder, encode_json, strict_json, utc, utc_text,
)


def fixture_order(forecast_date, *, windows=None):
    parties = strict_json(PROPOSAL_PATH.read_bytes())['parties']
    previous = date.fromisoformat(forecast_date) - timedelta(days=1)

    def stamp(hour, minute):
        return utc_text(datetime.combine(previous, time(hour, minute), ZONE))

    return WeatherOrder(
        proposal_id='LOCAL_FIXTURE_BERLIN_' + forecast_date.replace('-', '') + '_V1',
        buyer_account=parties['buyer_account'], seller_account=parties['seller_account'],
        recipient_account=parties['recipient_account'], proposed_agent=parties['proposed_agent'],
        mandate_origin=parties['mandate_origin'], forecast_date=forecast_date,
        windows=windows or ReportWindows(stamp(19, 30), stamp(19, 55), stamp(20, 0), stamp(20, 5), stamp(20, 10)),
        upstream_credits=('LOCAL FIXTURE: simulated source-use review, no actual licence clearance.',),
        simulated_order_accepted=True)


def fixture_source(order):
    fixture = strict_json((Path(__file__).parent / 'fixtures/berlin-weather-v1.LOCAL-FIXTURE.json').read_bytes())
    boundaries = order.boundaries()
    body = encode_json({
        'fixture_notice': fixture['fixture_scope'], 'latitude': 52.519, 'longitude': 13.419,
        'timezone': 'Europe/Berlin',
        'utc_offset_seconds': int(boundaries[0].astimezone(ZONE).utcoffset().total_seconds()),
        'generationtime_ms': 0.125,
        'hourly_units': {'time': 'unixtime', 'temperature_2m': '°C', 'precipitation_probability': '%'},
        'hourly': {'time': [int(instant.timestamp()) for instant in boundaries],
                   'temperature_2m': fixture['temperature_samples_celsius'],
                   'precipitation_probability': fixture['preceding_hour_probability_samples_percent']}})
    review = SourceUseReview('LOCAL_FIXTURE_SOURCE_USE_V1', order.commitment(), order.upstream_credits)
    source = IndependentForecast(
        body=body, record_id='LOCAL_FIXTURE_INDEPENDENT_CAPTURE_V1', order_sha256=order.commitment(),
        source_use_review_id=review.review_id, request_url_without_secret=order.request_url(),
        retrieved_at_utc=utc_text(utc(order.windows.source_capture_not_before_utc) + timedelta(minutes=5)))
    return source, review


def changed_source(source, change):
    body = strict_json(source.body)
    change(body)
    return replace(source, body=encode_json(body))
