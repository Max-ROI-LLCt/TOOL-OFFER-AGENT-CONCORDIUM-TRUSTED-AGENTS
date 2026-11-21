"""Generate or independently recheck a public synthetic delivery, without a wallet."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from tests.weather_report_fixtures import fixture_order, fixture_source
from tool_offer_agent.weather_report_acceptance import BuyerAcceptanceChecker
from tool_offer_agent.weather_report_contract import LIMITS, encode_json, strict_json
from tool_offer_agent.weather_report_renderer import render_report


REGISTRY = Path(__file__).resolve().parents[1] / 'integrations/concordium/tool-offer-registration-card'
PIN = 'd7d2d146be8ae2b768117d8ea6b7880269e952c9cee02b2a51df2520e4a02b99'
GENERATED = '2026-11-15T18:45:00Z'
DELIVERED = '2026-11-15T19:00:00Z'
ACCEPTED = '2026-11-15T19:03:00Z'


def verify_card():
    raw = (REGISTRY / 'agent-card-tooloffer-testnet-1206-v1.json').read_bytes()
    record = strict_json((REGISTRY / 'testnet-1206-verification.json').read_bytes())
    if not (sha256(raw).hexdigest() == PIN == record['on_chain']['metadata_hash_hex']
            and record['network'] == 'testnet' and record['on_chain']['status'] == 'Active'
            and strict_json(raw)['registrations'] == [{'agentId': 1206, 'agentRegistry':
                 'ccd:4221332d34e1694168c2a0c0b3fd0f27:12802.0'}]):
        raise ValueError('Testnet card differs from the retained registry observation')
    return PIN


def check_delivery(files):
    order = fixture_order('2026-11-16')
    source, review = fixture_source(order)
    return BuyerAcceptanceChecker(order, source, review).check(
        files, delivered_at_utc=DELIVERED, accepted_at_utc=ACCEPTED)


def make_delivery():
    order = fixture_order('2026-11-16')
    source, _ = fixture_source(order)
    return render_report(order, source, generated_at_utc=GENERATED)


def verify_bundle(path):
    with path.open('rb') as stream:
        raw = stream.read(2 * sum(LIMITS.values()) + 1)
    if len(raw) > 2 * sum(LIMITS.values()):
        raise ValueError('Oversized fixture bundle')
    bundle = strict_json(raw)
    if not isinstance(bundle, dict) or set(bundle) != set(LIMITS) or not all(isinstance(value, str) for value in bundle.values()):
        raise ValueError('Expected exactly the two UTF-8 delivery files')
    return check_delivery({name: value.encode() for name, value in bundle.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--emit', action='store_true', help='Write the two synthetic delivery files as one JSON bundle to stdout')
    modes.add_argument('--verify', type=Path, help='Check a saved bundle against independently reconstructed fixture inputs')
    args = parser.parse_args()
    card = verify_card()
    if args.verify:
        checked = verify_bundle(args.verify)
        print(json.dumps(checked, indent=2))
        return int(checked['state'] != 'LOCAL_ACCEPTED')
    files = make_delivery()
    if args.emit:
        print(json.dumps({name: value.decode() for name, value in files.items()}))
        return 0
    valid = check_delivery(files)
    report = strict_json(files['report.json'])
    report['summary']['maximum_temperature_2m_celsius'] += 1
    changed = check_delivery({**files, 'report.json': encode_json(report)})
    print(json.dumps({'testnet_card_1206_sha256': card, 'valid_delivery': valid['state'],
                      'changed_summary': changed['state'], 'failed_checks': changed['failed_checks'],
                      'payment': valid['payment'], 'wallet_or_network_required': False}, indent=2))
    return int(not (valid['state'] == 'LOCAL_ACCEPTED' and changed['state'] == 'LOCAL_REJECTED'
                    and changed['failed_checks'][0]['check_id'] == 'A09' and valid['payment'] == 'NOT_SUBMITTED'))


if __name__ == '__main__':
    raise SystemExit(main())
