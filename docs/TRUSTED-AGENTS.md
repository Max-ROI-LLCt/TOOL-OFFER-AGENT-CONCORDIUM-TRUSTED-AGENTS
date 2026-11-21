# Trusted Agents: what judges can verify

**November 21, 2026 · Checkpoint 1: project, team and idea.** Kingan Logic is extending Tool Offer Agent into a walletless buyer’s agent. A badge answers *who is accountable?* A mandate answers *what may this agent request?* A buyer’s wallet approval answers *may this transfer be made?* A delivery check answers *did the buyer get what was agreed?* None substitutes for another.

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

## From checkpoint to production

1. Verify both parties’ Testnet registry entries and the deployed FAHCE release against independently reviewed trust pins. Obtain a fresh authenticated CCD invoice for the actual request. Do not substitute Base USDC, a fixture price or a previous buyer’s invoice.
2. Bind service, supplier, recipient, amount, network, scope and expiry to the buyer’s exact mandate. Enforce revocation and the FAHCE decision before execution. For the intended x402 flow, prove which component issued the challenge and which verified settlement. The wallet owner separately approves the exact transfer; Tool Offer never takes their key.
3. Record finalized Testnet transaction evidence and check the delivery independently. On failure preserve the original; allow only bounded, authorized repair and revalidation. Recovery must return the recorded outcome rather than pay or dispatch twice. Changes to policy or acceptance rules require explicit approval and a rollback path.
4. Before Mainnet, verify Mainnet-specific registry identities, recipient, genesis, tariff and fee limits; review replay protection, monitoring, custody boundaries and recovery on that network. Neither a Testnet payment nor a Mainnet badge alone enables spending.

**Submission:** [Organizer brief](https://www.concordium.com/article/concordium-trusted-agents-hackathon-encode-club) · [Encode programme](https://www.encodeclub.com/programmes/concordium-trusted-agents-hackathon). Checkpoint 1 is **November 22, 2026 at 23:59 UTC**; final submission is **December 9, 2026 at 23:59 UTC**. Before final submission add the ≤3-minute video, the reproducible end-to-end Testnet instructions and CCDExplorer transaction evidence. This page is a build log, not a claim that those deliverables are finished. Future public milestones will be linked here; private checkout URLs, buyer records and credentials are not published.
