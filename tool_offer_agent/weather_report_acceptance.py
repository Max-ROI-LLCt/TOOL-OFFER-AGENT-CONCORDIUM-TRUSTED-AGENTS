"""Buyer checks against operator-retained inputs, never against seller assertions.

No renderer dependency, policy installation, wallet verification or payment path.
Fixture and real-service scopes remain distinct; source entitlement is checked upstream.
"""

from dataclasses import asdict

from .concordium_json import digest
from .weather_report_contract import (
    CHECK_IDS, FIXTURE_SCOPE, SERVICE_SCOPE, LIMITS, REPORT_SCHEMA, ZONE, IndependentForecast, WeatherServiceOrder,
    ReportError, SourceUseReview, WeatherOrder, WeatherDemoOrder, PublicReportOrder, attribution, byte_hash, no_secrets,
    encode_json, numeric, proposal_contract, read_forecast, require, source_projection, strict_json, utc, utc_text, limitations,
)


def delivery_hashes(files):
    return {name: byte_hash(raw) for name, raw in files.items() if type(raw) is bytes}


def check_files(files):
    require(type(files) is dict and set(files) == set(LIMITS), 'A03', 'Exactly two named files required')
    for name, raw in files.items():
        require(type(raw) is bytes and len(raw) <= LIMITS[name], 'A03', 'File size/type limit')


class BuyerAcceptanceChecker:
    def __init__(self, order, independent_source, source_use_review):
        require(type(order) in (WeatherOrder, WeatherServiceOrder, WeatherDemoOrder, PublicReportOrder) and type(independent_source) is IndependentForecast,
                'A01', 'Operator-retained order and independent source required')
        self.order = order
        self.source = independent_source
        self.review = source_use_review

    def check(self, files, *, delivered_at_utc, accepted_at_utc):
        failed = []
        try:
            self._validate(files, delivered_at_utc, accepted_at_utc)
        except ReportError as error:
            failed.append({'check_id': error.check_id, 'reason': error.reason})
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
            failed.append({'check_id': 'A03', 'reason': 'Invalid report or retained input structure'})
        return {
            'scope': self.order.scope,
            'state': ('LOCAL_REJECTED' if failed else 'LOCAL_ACCEPTED')
            if type(self.order) is WeatherOrder else ('DELIVERY_REJECTED' if failed else 'DELIVERY_ACCEPTED'),
            'proposal_id': self.order.proposal_id, 'order_sha256': self.order.commitment(),
            'source_record_sha256': digest(self.source.metadata()),
            'source_use_review_sha256': digest(strict_json(encode_json(asdict(self.review)))) if type(self.review) is SourceUseReview else None,
            'delivered_at_utc': delivered_at_utc, 'checked_at_utc': accepted_at_utc,
            'delivery_sha256': delivery_hashes(files) if type(files) is dict else {},
            'failed_checks': failed, 'validated_checks': list(CHECK_IDS[:-1]) if not failed else [],
            'durably_recorded': False, 'consent_established': False,
            'receipt_policy_satisfied': False, 'native_transaction_authorized': False,
            'payment': 'NOT_SUBMITTED', 'live_execution_enabled': False}

    def _validate(self, files, delivered_at, accepted_at):
        order, source, review = self.order, self.source, self.review
        order.validate()
        prefix = 'LOCAL_FIXTURE_' if type(order) is WeatherOrder else 'TESTNET_'
        require(type(review) is SourceUseReview and review.scope == order.scope and
                type(review.review_id) is str and review.review_id.startswith(prefix) and
                review.order_sha256 == order.commitment() and
                type(review.upstream_credits) is tuple and review.upstream_credits == order.upstream_credits,
                'A02', 'Independent source-use review missing or mismatched')
        require(source.scope == order.scope and type(source.record_id) is str and
                source.record_id.startswith(prefix) and source.order_sha256 == order.commitment() and
                source.source_use_review_id == review.review_id,
                'A02', 'Independent collector record missing or mismatched')
        check_files(files)
        report = strict_json(files['report.json'])
        require(type(report) is dict, 'A03', 'Report must be an object')
        contract = proposal_contract()
        require(set(report) == set(contract['report_fields']) and report['schema'] == REPORT_SCHEMA,
                'A03', 'Report properties/schema differ from V1')
        no_secrets(report)
        require(report['proposal_id'] == order.proposal_id and report['buyer_account'] == order.buyer_account and
                report['prepared_by_account'] == order.seller_account, 'A01', 'Report identity differs from order')
        require(report['forecast_date'] == order.forecast_date and report['timezone'] == 'Europe/Berlin',
                'A06', 'Wrong report date or timezone')
        require(report['units'] == {'temperature_2m': 'degC', 'precipitation_probability': 'percent'},
                'A05', 'Wrong report units')
        require(files['forecast-source.json'] == source.body and
                report['source'] == source_projection(source), 'A04', 'Delivery/source metadata differ from independent bytes')
        require(source.request_url_without_secret == order.request_url() and type(source.status_code) is int and
                source.status_code == 200 and source.media_type == 'application/json' and
                (source.http_date is None or type(source.http_date) is str),
                'A04', 'Unapproved query or unsuccessful/non-JSON retrieval')
        forecast = read_forecast(order, source.body)
        rows = report['hourly']
        require(type(rows) is list and len(rows) == 24, 'A06', 'Exactly 24 intervals required')
        hourly = forecast['hourly']
        boundaries = order.boundaries()
        expected_temperatures, expected_probabilities = [], []
        for index, row in enumerate(rows):
            require(type(row) is dict and set(row) == set(contract['hourly_fields']), 'A03', 'Wrong hourly properties')
            start, end = boundaries[index], boundaries[index + 1]
            temperature = hourly['temperature_2m'][hourly['time'].index(int(start.timestamp()))]
            probability = hourly['precipitation_probability'][hourly['time'].index(int(end.timestamp()))]
            require(numeric(temperature) and numeric(probability) and 0 <= probability <= 100,
                    'A06', 'Missing/non-numeric/out-of-range selected source value')
            expected_times = {
                'interval_start_local': start.astimezone(ZONE).isoformat(timespec='seconds'),
                'interval_end_local': end.astimezone(ZONE).isoformat(timespec='seconds'),
                'interval_start_utc': utc_text(start), 'interval_end_utc': utc_text(end),
                'temperature_source_time_utc': utc_text(start), 'precipitation_source_time_utc': utc_text(end)}
            require(all(row[key] == value for key, value in expected_times.items()) and
                    row['source_id'] == 'weather-1', 'A06', 'Wrong interval or source sample boundary')
            require(numeric(row['temperature_2m_celsius']) and numeric(row['precipitation_probability_percent']) and
                    row['temperature_2m_celsius'] == temperature and row['precipitation_probability_percent'] == probability,
                    'A06', 'Report values do not equal independently retained source samples')
            expected_temperatures.append(temperature)
            expected_probabilities.append(probability)
        latitude, longitude = forecast.get('latitude'), forecast.get('longitude')
        require(numeric(latitude) and numeric(longitude) and -90 <= latitude <= 90 and -180 <= longitude <= 180,
                'A07', 'Invalid grid coordinates')
        expected_location = {'city': 'Berlin', 'country': 'DE', 'requested_latitude': 52.52,
                             'requested_longitude': 13.41, 'source_grid_latitude': latitude,
                             'source_grid_longitude': longitude}
        require(report['location'] == expected_location and all(numeric(report['location'][key]) for key in (
            'requested_latitude', 'requested_longitude', 'source_grid_latitude', 'source_grid_longitude')),
            'A07', 'Report point/grid coordinates differ from independent source')
        captured, delivered, accepted = utc(source.retrieved_at_utc), utc(delivered_at), utc(accepted_at)
        generated = utc(report['generated_at_utc'])
        windows = order.windows
        require(utc(windows.source_capture_not_before_utc) <= captured <= utc(windows.source_capture_not_after_utc) and
                captured <= generated <= delivered <= accepted and delivered <= utc(windows.delivery_deadline_utc) and
                accepted <= utc(windows.buyer_acceptance_deadline_utc) and
                0 <= (accepted - captured).total_seconds() <= windows.maximum_source_age_at_acceptance_seconds,
                'A08', 'Source/generation/delivery/acceptance freshness or window failed')
        lowest = expected_probabilities.index(min(expected_probabilities))
        expected_summary = {
            'minimum_temperature_2m_celsius': min(expected_temperatures),
            'maximum_temperature_2m_celsius': max(expected_temperatures),
            'maximum_precipitation_probability_percent': max(expected_probabilities),
            'lowest_precipitation_probability_interval_start_local': boundaries[lowest].astimezone(ZONE).isoformat(timespec='seconds')}
        require(report['summary'] == expected_summary and all(numeric(report['summary'][key]) for key in (
            'minimum_temperature_2m_celsius', 'maximum_temperature_2m_celsius', 'maximum_precipitation_probability_percent')),
            'A09', 'Summary differs from independent recomputation or tie rule')
        require(report['attribution'] == attribution(order) and report['limitations'] == limitations(order),
                'A10', 'Required citations, credits, modifications or limitations differ')
