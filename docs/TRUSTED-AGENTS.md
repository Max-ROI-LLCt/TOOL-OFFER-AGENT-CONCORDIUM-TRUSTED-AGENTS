# Trusted Agents: what judges can verify

**November 21, 2026 · Checkpoint 1: project, team and idea.** Kingan Logic is extending Tool Offer Agent into a walletless buyer’s agent. A badge answers *who is accountable?* A mandate answers *what may this agent request?* A buyer’s wallet approval answers *may this transfer be made?* A delivery check answers *did the buyer get what was agreed?* None substitutes for another.

## Verify the November 26 sponsored purchase

Tool Offer bought FAHCE’s Diagnose assessment of the synthetic Berlin report. Invoice `03b352b4-d915-4b45-91ac-1be894100b1a` identifies both the purchase and the signed Diagnose run.

| Charge | Paid by | Amount |
| --- | --- | ---: |
| Diagnose assessment paid to FAHCE account `…TqXpTY` | Buyer `…Pbgt6n` | 52 CCD |
| Concordium network fee | Facilitator `…FGGrS1` | 5.214944 CCD |

**Settlement.** The sponsored V1 transfer finalized in Testnet block **51,310,007**, with block time **07:37:20.495 UTC**. Compare the transaction hash and block in the purchase record with the public explorer. [Testnet transaction](https://ccdexplorer.io/testnet/transaction/44b51cfb0aa49ca5ecdb751e19f092b970a5bd630301994b3b6c6dfbf0f61068) · [Purchase evidence](../evidence/concordium-testnet-diagnose-2026-11-26.json)

**Delivery.** At **08:29:33 UTC**, the authenticated `POST /testnet/buy/result` returned **HTTP 200**. FAHCE recorded the payment admission as `VERIFIED` and the Diagnose result as **`CLEAR_WITH_CEILING`**. The assessment covers the claims in the submitted report against the supplied synthetic evidence.

**Receipt verification.** The live bridge reported **`RECEIPT_VERIFICATION_FAILED`** on that HTTP 200 read. The maintainer later verified the saved receipt’s attestation offline using the pinned FAHCE policy and Microsoft Azure Attestation public keys. The signed input digest matched the submitted report, and the returned payment details matched the finalized transaction.

The receipt SHA-256 below covers the full signed response encoded as compact, sorted-key UTF-8 JSON with no trailing newline.

```text
9b21161e5372adeef7b870df8db2843f832e68e13e2b533f3aa1aa8c9af9f564
```

## Verify the November 22 Testnet purchase

Tool Offer sent FAHCE 48 claims from a saved synthetic Berlin report and one supporting document through its machine checkout. The buyer approved the native CCD transfer in Concordium Wallet. The service purchased was **Diagnose**, an assessment of those claims against the supplied evidence.

1. **Check settlement on CCDExplorer.** Open the transaction and compare the block hash and height with the evidence record. The transfer paid **52 Testnet CCD** with a **4.141099 CCD** network fee. The official Testnet node reported the transaction finalized in block **51,129,761**, with block time **03:28:34.623 UTC** on November 22. The transfer memo contains the canonical invoice’s SHA-256 digest encoded as a CBOR byte string. [CCDExplorer transaction](https://ccdexplorer.io/testnet/transaction/9ccfb5f42aba74003a0caefb1b90387cc5a4dfad32870a68d5e6c5ee8a7bbbc9) · [Settlement fields and memo](../evidence/concordium-testnet-diagnose-2026-11-22.json)
2. **Read the Diagnose outcome.** FAHCE issued its signed response at **03:33:28.172 UTC**. The maintainers retrieved the original response from the seller’s invoice record, verified its attestation against the pinned policy and issuer keys, and matched its transaction binding and input digest to the paid request. All 48 submitted claims appeared in the result. FAHCE returned `DETERMINATION_COMPLETE` and `CLEAR_WITH_CEILING`, with **48 supported, zero contradictions**. Its deterministic pilot assessed agreement with the supplied synthetic document. [Result summary, input digest and signed-response file digest](../evidence/concordium-testnet-diagnose-2026-11-22.json)

3. **Reproduce the buyer’s check.** From the public checkout, run `python3.12 -m tests.verify_testnet_diagnose`. It reads Concordium’s public Testnet service, checks the finalized transfer and finds one payment with the original invoice memo in the recorded account-history window. It also derives 48 expected claims from the 25 redistributable synthetic samples and compares their digest with the maintainer’s digest of the signed claims and support labels. [Redacted trace](../evidence/concordium-testnet-diagnose-recovery-2026-11-22.json) · [Verification code](../tests/verify_testnet_diagnose.py) · [Synthetic source](../evidence/berlin-synthetic-source-2026-11-17.json)

The maintainers checked the original signed response, each evidence reference and the paid input privately. Two invoice-specific reads of FAHCE’s records, before and after a buyer bridge restart, each found one admission, one recorded dispatch and the same signed response digest. The dispatch run ID matched the signed result. The authenticated buyer-side receipt export after restart is still pending. Reviewers who hold the original request and response can add `--source evidence/berlin-synthetic-source-2026-11-17.json --request request.json --result receipt.json` to repeat the full comparison.

## Run the checkpoint

From a clone of this public repository, with Python 3.12 and a system timezone database:

```sh
python3.12 -m tests.trusted_agents_demo
python3.12 -m tests.trusted_agents_demo --emit > report-bundle.json
python3.12 -m tests.trusted_agents_demo --verify report-bundle.json
```

These commands need neither credentials nor dependencies from FAHCE. The first rehashes the retained Testnet agent card and runs a valid and a deliberately altered delivery. Expect `LOCAL_ACCEPTED`, then `LOCAL_REJECTED` with `A09` (incorrect summary). The separate verifier reconstructs the buyer’s order and independent synthetic input from this checkout rather than trusting the seller’s totals or any verdict in the bundle. It returns nonzero on rejection. All dates, parties and forecast values in the rehearsal are fixtures. The separately pinned public report contract cannot authorize a live order.

To exercise agent and wallet proof separately, use Python 3.12 and Node 24. Installation needs internet; the tests use generated local keys, no funded accounts, RPC or Agentverse login:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -c constraints-validated.txt -e '.[test]'
python -m unittest tests.test_concordium_mandate tests.test_concordium_mandate_auth
npm --prefix bridge/concordium-testnet ci --ignore-scripts
node --test --test-isolation=none bridge/concordium-testnet/verify-account.test.mjs
```

The Python suite rejects changed actions, wrong signers, expired mandates and replay after restart. The Node suite checks real Concordium SDK message signatures, including wrong account, wrong key and insufficient credential thresholds. This proves account control in the fixture, not transaction signing, sponsorship or settlement.

## Build log and evidence

| Date / boundary | Evidence and limits |
| --- | --- |
| Reused from Stranger Builds | [Tool Offer Agent](../START-HERE.md) already drafts, revises and exports source-attributed offers through ASI:One. The [Base USDC bridge](BRIDGE.md) and prior evaluation are historical, not new Concordium work. |
| Reused external service | FAHCE runs its own evaluation engine. [Public attestation](https://fahce.kinganlogic.com/attestation) describes how to verify a release. An engine attestation is not a purchase receipt or authorization to change trust pins. Judges do not need its private source. |
| Testnet identity | Compare [the published Agent Card](https://tooloffer.kinganlogic.com/.well-known/agent-card-tooloffer-testnet-1206-v1.json) with the [retained registry readback](../integrations/concordium/tool-offer-registration-card/testnet-1206-verification.json). Tool Offer is #1206 in [Testnet CIS-8004 contract 12802,0](https://ccdexplorer.io/testnet/contract/12802/0). The local comparison is not a fresh on-chain query. |
| November 21 public build | [Mandate binding](../tool_offer_agent/concordium_mandate.py), [agent signature verification](../tool_offer_agent/concordium_mandate_auth.py), [wallet binding](../bridge/concordium-testnet/verify-wallet-binding.mjs), [independent checker](../tool_offer_agent/weather_report_acceptance.py) and [portable fixture demo](../tests/trusted_agents_demo.py) are available here. The 1 CCD synthetic report is a separate scenario, **not** a live quote for FAHCE Diagnose. |
| November 22 live purchase | Tool Offer bought a FAHCE Diagnose assessment with a wallet-approved native CCD transfer on Testnet. [Check the transfer and read the result](#verify-the-november-22-testnet-purchase) |
| November 26 sponsored x402 purchase | A facilitator paid the fee on the buyer’s finalized 52 CCD transfer. [Result and receipt verification](#verify-the-november-26-sponsored-purchase) |

## From checkpoint to production

1. **Identity and authority.** Demonstrate both registry identities and the exact buyer mandate in one live trace. Bind the service, supplier, recipient, amount, network, scope and expiry, and show enforcement of revocation and the pre-execution FAHCE decision. The November 22 wallet approval and the local mandate tests cover different steps.
2. **Concordium x402.** The November 26 evidence ties a sponsored Testnet transfer to the paid invoice and signed Diagnose result. To complete the protocol trace, publish the original challenge and show how the facilitator checked settlement against its terms.
3. **Delivery, repair and recovery.** Give a judge a portable record tying finality to independent buyer acceptance. Show that recovery after a restart returns the same delivery with one payment and one dispatch. For a rejected delivery, preserve the original, bind one authorized repair to the failed claims, and rerun the same buyer acceptance checks against both versions. Keep the evidence portable. Version any proposed acceptance-rule change, obtain owner approval before applying it, and demonstrate rollback to the approved baseline.
4. **Mainnet.** Tool Offer’s Mainnet registry entry is #5135. Before a Mainnet purchase, verify both Mainnet identities, the recipient, genesis, tariff and fee limits, and review replay protection, monitoring, custody and recovery on that network. Mainnet settlement requires its own transaction evidence.

**Submission.** Checkpoint 1 is **November 22, 2026 at 23:59 UTC**. Final submission is **December 9, 2026 at 23:59 UTC**. The November 22 transaction is available on CCDExplorer. Remaining submission material includes the ≤3-minute video and instructions for reproducing the end-to-end Testnet flow. [Organizer brief](https://www.concordium.com/article/concordium-trusted-agents-hackathon-encode-club) · [Encode programme](https://www.encodeclub.com/programmes/concordium-trusted-agents-hackathon)
