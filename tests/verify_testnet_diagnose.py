"""Read-only checks for the published November 22 Concordium Testnet Diagnose purchase."""

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from urllib.request import urlopen

from tool_offer_agent.concordium_json import digest


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence/concordium-testnet-diagnose-2026-11-22.json"
TRACE = EVIDENCE.with_name("concordium-testnet-diagnose-recovery-2026-11-22.json")
SOURCE_SHA256 = "0f701cb7e2bdb1a28830afa38f27db68057091b8c28bfb195e6fb9a3e62acbe8"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def public_settlement(ledger, window):
    url = "https://wallet-proxy.testnet.concordium.com/v0/submissionStatus/" + ledger["transaction_hash"]
    with urlopen(url, timeout=20) as response:
        tx = json.load(response)
    require(tx["status"] == "finalized" and tx["outcome"] == "success", "Transfer did not finalize successfully")
    require(tx["blockHashes"] == [ledger["block_hash"]], "Finalized block mismatch")
    for field, expected in (("transactionHash", ledger["transaction_hash"]), ("amount", str(ledger["amount_microccd"])),
                            ("cost", str(ledger["network_fee_microccd"])), ("memo", ledger["memo_hex"])):
        require(tx[field] == expected, field + " mismatch")
    cursor = window["from_exclusive_id"]
    history = f"https://wallet-proxy.testnet.concordium.com/v1/accTransactions/{tx['sender']}?order=descending&limit=100&from={cursor}"
    with urlopen(history, timeout=20) as response:
        records = [r for r in json.load(response)["transactions"] if r["id"] < cursor]
    start = datetime.fromisoformat(window["invoice_created_utc"]).timestamp()
    require(len(records) == window["account_records"] and min(r["blockTime"] for r in records) < start,
            "Account history does not cover the recorded invoice window")
    matches = [r["transactionHash"] for r in records if r["blockTime"] >= start and
               r["details"].get("transferSource") == tx["sender"] and r["details"].get("transferDestination") == tx["to"] and
               r["details"].get("type") == "transferWithMemo" and r["details"].get("memo") == ledger["memo_hex"]]
    require(matches == [tx["transactionHash"]], "Expected one payment with the invoice memo in the recorded window")
    return {"public_node_service": url, "status": tx["status"], "matching_transfers_in_recorded_window": len(matches)}


def expected_readings(source_bytes):
    require(sha256(source_bytes).hexdigest() == SOURCE_SHA256, "Original source bytes changed")
    series = json.loads(source_bytes, parse_float=Decimal)["hourly"]
    times = series["time"]
    temperatures = series["temperature_2m"]
    rain = series["precipitation_probability"]
    require(len(times) == len(temperatures) == len(rain) == 25, "Expected 25 hourly source samples")
    readings = {}
    for i, (start, end) in enumerate(zip(times, times[1:])):
        require(end - start == 3600, "Source interval differs from one hour")
        a, b = [datetime.fromtimestamp(t, timezone.utc).strftime("%Y%m%dt%H%M%Sz") for t in (start, end)]
        prefix = f"berlin_synthetic_{a}_{b}_"
        readings[prefix + "precipitation_probability_" + b] = (rain[i+1], "percent")
        readings[prefix + "temperature_2m_" + a] = (Decimal(temperatures[i]) + Decimal("273.15"), "ratio")
    return readings


def buyer_acceptance(evidence, request, result, source_bytes):
    ledger, diagnose = evidence["settlement"], evidence["diagnose"]
    expected_input = diagnose["input_sha256"]
    require(digest({"operation": "diagnose", "request": request}) == expected_input, "Paid request changed")
    if "invoice" in result:
        invoice, payment = result["invoice"], result["payment"]
        require("5820" + digest(invoice) == ledger["memo_hex"] and invoice["input_sha256"] == expected_input,
                "Export invoice does not match the on-chain commitment")
        require(invoice["genesis_hash"] == ledger["genesis_hash"] and payment["status"] == "FINALIZED_NATIVE_CCD_TRANSFER_MATCH" and
                payment["transaction_hash"] == ledger["transaction_hash"] and
                payment["invoice_memo_hex"] == ledger["memo_hex"] and
                payment["amount_microccd"] == str(ledger["amount_microccd"]) and
                payment["block_hash"] == ledger["block_hash"] and payment["fee_microccd"] == str(ledger["network_fee_microccd"])
                and payment["payer"] == invoice["payer"] and payment["recipient"] == invoice["recipient"],
                "Export payment differs from the finalized payment")
        result = result["receipt"]
    require(digest(result) == diagnose["signed_response_file_sha256"], "Result differs from the verified signed response")
    require(result["binding"]["idempotency_key"] == "ccd_" + ledger["transaction_hash"] and
            result["attestation"]["binding"]["input_hash"] == expected_input, "Result binding mismatch")
    readings = expected_readings(source_bytes)
    expected = [f"{k} equals {v} {u}." for k, (v, u) in readings.items()]
    evidence_lines = [f"{k}={v}{u}" for k, (v, u) in readings.items()]
    document, = request["evidence"]
    require(Counter(document["text"].splitlines()) == Counter(evidence_lines), "Submitted document differs from source")
    require(Counter(request["candidate_output"].splitlines()) == Counter(expected), "Submitted claims differ from source")
    provenance, = result["evidence_provenance"]
    require(provenance["item_id"] == document["id"] and provenance["sha256"] == sha256(document["text"].encode()).hexdigest(),
            "Signed result refers to a different document")
    diagnosis = result["diagnosis"]
    require(result["billing"]["determination_status"] == "DETERMINATION_COMPLETE" and
            diagnosis["state"] == "CLEAR_WITH_CEILING" and not diagnosis["contradictions"] and not diagnosis["missing_evidence"],
            "Incomplete determination or unresolved claim")
    claims = diagnosis["claims"]
    require(Counter(c["claim"] for c in claims) == Counter(expected), "Signed claim set differs from source")
    require(all(c["support"] == "SUPPORTED" and c["evidence_refs"] == [provenance["id"]] for c in claims),
            "Verdict or evidence reference mismatch")
    return {"independent_source_samples": 25, "hourly_intervals": 24, "supported_claims_checked": len(claims),
            "matched_signed_response_sha256": digest(result), "scope": "Diagnose of caller-supplied synthetic readings"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Original synthetic forecast-source.json bytes")
    parser.add_argument("--request", type=Path, help="Exact Diagnose request")
    parser.add_argument("--result", type=Path, help="Original signed response or the buyer's downloaded receipt export")
    args = parser.parse_args()
    supplied = [args.source, args.request, args.result]
    if any(supplied) and not all(supplied):
        parser.error("Supply source, request, and result together for the off-chain check")
    evidence = json.loads(EVIDENCE.read_bytes())
    trace = json.loads(TRACE.read_bytes())
    recorded = trace["buyer_acceptance"]
    public_source = (EVIDENCE.parent / recorded["source_file"]).read_bytes()
    readings = expected_readings(public_source)
    pairs = sorted([f"{key} equals {value} {unit}.", "SUPPORTED"] for key, (value, unit) in readings.items())
    require(digest(pairs) == recorded["sorted_claim_and_support_pairs_sha256"], "Synthetic readings differ from the signed claim commitment")
    report = {"settlement": public_settlement(evidence["settlement"], trace["account_history"]),
              "expected_claims_matching_maintainer_commitment": len(pairs)}
    if all(supplied):
        report["buyer_acceptance"] = buyer_acceptance(evidence, json.loads(args.request.read_bytes()),
                                                     json.loads(args.result.read_bytes()), args.source.read_bytes())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
