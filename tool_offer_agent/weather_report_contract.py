"""Pinned report V1 contract and local-only trusted fixture inputs, not authority."""

from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from .concordium_json import digest


PROPOSAL_PATH = Path(__file__).resolve().parents[1] / 'tests/fixtures/report-contract.PUBLIC-FIXTURE.json'
PROPOSAL_SHA256 = '0466b39a87b0e7ae4560988b64ecb07ef6182d4e93d4f8ccc963d28d51facff1'
FIXTURE_SCOPE = 'LOCAL_FORECAST_FIXTURE_ONLY_NOT_LIVE_WEATHER_OR_CONSENT'
SERVICE_SCOPE = 'TESTNET_REPORT_SERVICE_NOT_SETTLEMENT_OR_FORECAST_TRUTH'
DEMO_SCOPE = 'PRIVATE_TESTNET_REPORT_PROTOTYPE_NOT_COMMERCIAL_OR_PROMOTIONAL'
PUBLIC_SCOPE = 'PUBLIC_SYNTHETIC_REPORT_DEMO_NOT_A_WEATHER_FORECAST'
REPORT_SCHEMA = 'TOOL_OFFER_BERLIN_WEATHER_REPORT_V1'
LIMITS = {'report.json': 131072, 'forecast-source.json': 1048576}
CHECK_IDS = tuple(f'A{index:02}' for index in range(1, 12))
ZONE = ZoneInfo('Europe/Berlin')


class ReportError(ValueError):
    def __init__(self, check_id, reason):
        self.check_id = check_id
        self.reason = reason
        super().__init__(f'{check_id}: {reason}')


def require(condition, check_id, reason):
    if not condition:
        raise ReportError(check_id, reason)


def byte_hash(value):
    return sha256(value).hexdigest()


def strict_json(raw):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'A03', 'Duplicate JSON property')
            result[key] = value
        return result

    def invalid_constant(value):
        raise ReportError('A03', 'Nonfinite JSON value')

    def bounded(value, depth=0):
        require(depth <= 32, 'A03', 'JSON nesting exceeds limit')
        if isinstance(value, dict):
            for key, child in value.items():
                bounded(key, depth + 1)
                bounded(child, depth + 1)
        elif isinstance(value, list):
            for child in value:
                bounded(child, depth + 1)
        elif type(value) is float:
            require(math.isfinite(value), 'A03', 'Nonfinite JSON number')
        elif type(value) is int:
            require(abs(value) <= 2**53 - 1, 'A03', 'Unsafe JSON integer')
        elif type(value) is str:
            value.encode('utf-8', errors='strict')

    try:
        require(type(raw) is bytes, 'A03', 'UTF-8 bytes required')
        result = json.loads(raw.decode('utf-8'), object_pairs_hook=object_pairs,
                            parse_constant=invalid_constant)
        bounded(result)
        return result
    except (UnicodeError, json.JSONDecodeError, RecursionError, OverflowError, ValueError) as error:
        if isinstance(error, ReportError):
            raise
        raise ReportError('A03', 'Invalid bounded UTF-8 JSON') from None


def encode_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def proposal_contract():
    raw = PROPOSAL_PATH.read_bytes()
    require(byte_hash(raw) == PROPOSAL_SHA256, 'A01', 'Dated proposal changed')
    return strict_json(raw)['delivery_contract_proposal']


def utc(value, check_id='A08'):
    require(type(value) is str and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value),
            check_id, 'Exact UTC second timestamp required')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ReportError(check_id, 'Invalid UTC timestamp') from None


def utc_text(value):
    return value.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def no_secrets(value):
    if type(value) is dict:
        for key, child in value.items():
            normalized = re.sub(r'[^a-z]', '', key.lower())
            require(normalized not in {'apikey', 'accesstoken', 'authorization', 'cookie',
                    'setcookie', 'password', 'secret', 'privatekey', 'walletsignature'},
                    'A10', 'Secret-bearing field not allowed')
            no_secrets(child)
    elif type(value) in (list, tuple):
        for child in value:
            no_secrets(child)
    elif type(value) is str:
        require(not re.search(r'(?:api[_-]?key|access[_-]?token)=|\bbearer\s+', value, re.I),
                'A10', 'Credential-bearing text not allowed')


@dataclass(frozen=True)
class ReportWindows:
    source_capture_not_before_utc: str
    source_capture_not_after_utc: str
    delivery_deadline_utc: str
    buyer_acceptance_deadline_utc: str
    commercial_expiry_utc: str
    maximum_source_age_at_acceptance_seconds: int = 3600


@dataclass(frozen=True)
class WeatherOrder:
    """Operator-selected immutable terms. Only simulated consent is supported here."""

    proposal_id: str
    buyer_account: str
    seller_account: str
    recipient_account: str
    proposed_agent: str
    mandate_origin: str
    forecast_date: str
    windows: ReportWindows
    upstream_credits: tuple[str, ...]
    network: str = 'concordium:testnet'
    asset: str = 'CCD'
    amount_atomic: str = '1000000'
    sale_type: str = 'REPORT_PREPARATION_SERVICE_NOT_WEATHER_API_ACCESS'
    proposal_sha256: str = PROPOSAL_SHA256
    scope: str = FIXTURE_SCOPE
    simulated_order_accepted: bool = False

    def validate(self):
        require(self.scope == FIXTURE_SCOPE and type(self.proposal_id) is str and self.proposal_id.startswith('LOCAL_FIXTURE_'),
                'A01', 'Only clearly labelled local fixture orders supported')
        require(self.simulated_order_accepted is True, 'A01', 'No simulated accepted order')
        require(self.proposal_sha256 == PROPOSAL_SHA256, 'A01', 'Wrong proposal version')
        proposal_contract()
        require((self.network, self.asset, self.amount_atomic, self.sale_type) == (
            'concordium:testnet', 'CCD', '1000000', 'REPORT_PREPARATION_SERVICE_NOT_WEATHER_API_ACCESS'),
            'A01', 'Order differs from V1 Testnet service terms')
        self._validate_common()

    def _validate_common(self):
        require(self.seller_account == self.recipient_account, 'A01', 'Recipient differs from seller')
        require(all(type(value) is str and 0 < len(value) <= 256 for value in (
            self.proposal_id, self.buyer_account, self.seller_account, self.proposed_agent,
            self.mandate_origin)), 'A01', 'Missing exact parties or origin')
        require(self.mandate_origin == 'https://tooloffer.kinganlogic.com', 'A01', 'Wrong origin')
        require(type(self.upstream_credits) is tuple and all(
            type(value) is str and 0 < len(value) <= 2048 for value in self.upstream_credits),
            'A02', 'Explicit resolved credit tuple required, even if empty')
        require(type(self.windows) is ReportWindows, 'A01', 'Explicit delivery windows required')
        times = [utc(getattr(self.windows, key), 'A01') for key in (
            'source_capture_not_before_utc', 'source_capture_not_after_utc',
            'delivery_deadline_utc', 'buyer_acceptance_deadline_utc', 'commercial_expiry_utc')]
        boundaries = self.boundaries()
        require(times == sorted(times) and times[-1] < boundaries[0], 'A01', 'Invalid order windows')
        previous_date = date.fromisoformat(self.forecast_date) - timedelta(days=1)
        require(all(value.astimezone(ZONE).date() == previous_date for value in times),
                'A01', 'V1 next-day preparation windows must be on the preceding Berlin date')
        require(type(self.windows.maximum_source_age_at_acceptance_seconds) is int and
                self.windows.maximum_source_age_at_acceptance_seconds == 3600,
                'A01', 'V1 maximum retrieval age must be 3600 seconds')
        no_secrets(asdict(self))

    def boundaries(self):
        try:
            selected = date.fromisoformat(self.forecast_date)
            require(selected.isoformat() == self.forecast_date, 'A01', 'ISO forecast date required')
            start = datetime.combine(selected, time(), ZONE).astimezone(timezone.utc)
            end = datetime.combine(selected + timedelta(days=1), time(), ZONE).astimezone(timezone.utc)
        except (ValueError, TypeError):
            raise ReportError('A01', 'Invalid forecast date') from None
        require(end - start == timedelta(hours=24), 'A01', 'V1 requires 24 hours; DST day needs new review')
        boundaries = tuple(start + timedelta(hours=index) for index in range(25))
        require(len({instant.astimezone(ZONE).utcoffset() for instant in boundaries}) == 1,
                'A01', 'V1 does not support an offset transition')
        return boundaries

    def to_dict(self):
        return strict_json(encode_json(asdict(self)))

    @classmethod
    def from_dict(cls, value):
        selected = dict(value)
        selected['windows'] = ReportWindows(**selected['windows'])
        selected['upstream_credits'] = tuple(selected['upstream_credits'])
        return cls(**selected)

    def commitment(self):
        return digest(self.to_dict())

    def request_url(self):
        following = date.fromisoformat(self.forecast_date) + timedelta(days=1)
        return 'https://customer-api.open-meteo.com/v1/forecast?' + urlencode({
            'latitude': '52.52', 'longitude': '13.41',
            'hourly': 'temperature_2m,precipitation_probability',
            'start_date': self.forecast_date, 'end_date': following.isoformat(),
            'timezone': 'Europe/Berlin', 'timeformat': 'unixtime', 'temperature_unit': 'celsius'})


@dataclass(frozen=True)
class WeatherServiceOrder(WeatherOrder):
    scope: str = SERVICE_SCOPE

    def validate(self):
        raise ReportError('A01', 'Public judging contract is fixture-only')


@dataclass(frozen=True)
class WeatherDemoOrder(WeatherServiceOrder):
    scope: str = DEMO_SCOPE

    def validate(self):
        require(self.scope == DEMO_SCOPE and self.proposal_id.startswith('TESTNET_DEMO_'),
                'A01', 'Explicit private Testnet prototype scope required')
        WeatherServiceOrder.validate(replace(self, scope=SERVICE_SCOPE))

    def request_url(self):
        return super().request_url().replace('https://customer-api.open-meteo.com/',
                                             'https://api.open-meteo.com/', 1)


@dataclass(frozen=True)
class PublicReportOrder(WeatherServiceOrder):
    scope: str = PUBLIC_SCOPE

    def validate(self):
        require(self.scope == PUBLIC_SCOPE and self.proposal_id.startswith('TESTNET_PUBLIC_'),
                'A01', 'Fresh explicitly synthetic public order required')
        WeatherServiceOrder.validate(replace(self, scope=SERVICE_SCOPE))

    def request_url(self):
        return 'urn:tool-offer:synthetic-linear-25:v1:' + self.forecast_date


@dataclass(frozen=True)
class SourceUseReview:
    review_id: str
    order_sha256: str
    upstream_credits: tuple[str, ...]
    scope: str = FIXTURE_SCOPE


@dataclass(frozen=True)
class IndependentForecast:
    """Installed by local operator/collector, never taken from a seller upload."""

    body: bytes
    record_id: str
    order_sha256: str
    source_use_review_id: str
    request_url_without_secret: str
    retrieved_at_utc: str
    http_date: str | None = None
    status_code: int = 200
    media_type: str = 'application/json'
    scope: str = FIXTURE_SCOPE

    def metadata(self):
        return {key: value for key, value in asdict(self).items() if key != 'body'} | {
            'body_sha256': byte_hash(self.body)}


def source_projection(source):
    if source.scope == PUBLIC_SCOPE:
        return {'source_id': 'weather-1', 'provider': 'Tool Offer synthetic numeric fixture',
                'documentation_url': 'urn:tool-offer:synthetic-linear-25:v1',
                'request_url_without_secret': source.request_url_without_secret,
                'retrieved_at_utc': source.retrieved_at_utc, 'http_date': None,
                'forecast_issued_at_utc': None, 'forecast_issue_time_status': 'SYNTHETIC_NOT_A_FORECAST',
                'body_sha256': byte_hash(source.body), 'retrieval_record_id': source.record_id}
    return {'source_id': 'weather-1', 'provider': 'Open-Meteo',
            'documentation_url': 'https://open-meteo.com/en/docs',
            'request_url_without_secret': source.request_url_without_secret,
            'retrieved_at_utc': source.retrieved_at_utc, 'http_date': source.http_date,
            'forecast_issued_at_utc': None,
            'forecast_issue_time_status': 'NOT_PROVIDED_BY_SELECTED_CONTRACT',
            'body_sha256': byte_hash(source.body), 'retrieval_record_id': source.record_id}


def attribution(order):
    if order.scope == PUBLIC_SCOPE:
        return {'provider_credit': 'Tool Offer: synthetic numbers, not weather data',
                'provider_url': 'urn:tool-offer:synthetic-linear-25:v1',
                'licence_name': 'Public redistributable synthetic demonstration input',
                'licence_url': 'urn:tool-offer:synthetic-linear-25:v1',
                'modifications': 'Generated integer sequences; report contains 24 hourly intervals.',
                'upstream_credits': list(order.upstream_credits)}
    return {'provider_credit': 'Weather data: Open-Meteo', 'provider_url': 'https://open-meteo.com/',
            'licence_name': 'CC BY 4.0', 'licence_url': 'https://creativecommons.org/licenses/by/4.0/',
            'modifications': 'Selected Berlin hourly intervals, paired start temperatures with preceding-hour '
            'probabilities at interval ends, converted timestamps, and calculated min/max and '
            'lowest-probability summary. Source values are not rounded.',
            'upstream_credits': list(order.upstream_credits)}


def limitations(order):
    if order.scope == PUBLIC_SCOPE:
        return 'Synthetic integer sequences, NOT a forecast or observed weather. Publicly repeatable report-compiler demonstration only; no weather provider supplied these numbers. Signer, settlement and challenge evidence must be assessed separately.'
    return proposal_contract()['limitations_text']


def read_forecast(order, raw):
    require(type(raw) is bytes and len(raw) <= LIMITS['forecast-source.json'], 'A03', 'Source size/type limit')
    source = strict_json(raw)
    no_secrets(source)
    require(type(source) is dict, 'A05', 'Forecast must be an object')
    hourly, units = source.get('hourly'), source.get('hourly_units')
    require(type(hourly) is dict and type(units) is dict, 'A05', 'Missing hourly source structure')
    require(source.get('timezone') == 'Europe/Berlin' and
            type(source.get('utc_offset_seconds')) is int and
            source['utc_offset_seconds'] == int(order.boundaries()[0].astimezone(ZONE).utcoffset().total_seconds()),
            'A05', 'Wrong source timezone or offset')
    require(units.get('temperature_2m') == '°C' and units.get('precipitation_probability') == '%',
            'A05', 'Wrong source units')
    arrays = [hourly.get(key) for key in ('time', 'temperature_2m', 'precipitation_probability')]
    require(all(type(array) is list for array in arrays) and len({len(array) for array in arrays}) == 1,
            'A05', 'Source arrays differ in length or type')
    epochs = hourly['time']
    require(all(type(epoch) is int for epoch in epochs) and
            all(later - earlier == 3600 for earlier, later in zip(epochs, epochs[1:])),
            'A05', 'Source hours must be unique ordered integer epochs')
    require(set(int(instant.timestamp()) for instant in order.boundaries()).issubset(epochs),
            'A05', 'Source missing requested interval boundaries')
    return source
