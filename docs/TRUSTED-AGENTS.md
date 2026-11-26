# Trusted Agents: what judges can verify

**November 21, 2026 · Checkpoint 1: project, team and idea.** Kingan Logic is extending Tool Offer Agent into a walletless buyer’s agent. A badge answers *who is accountable?* A mandate answers *what may this agent request?* A buyer’s wallet approval answers *may this transfer be made?* A delivery check answers *did the buyer get what was agreed?* None substitutes for another.

## November 26 Mainnet Diagnose purchase

One private checkout completed a FAHCE Diagnose on Concordium Mainnet. The checkout operator reports that FAHCE served an HTTP 402 challenge for invoice `5addf462-cd58-4c6c-8988-38418197046f` with a verified sponsor signature. That invoice expired. The buyer’s wallet then submitted the transfer for replacement invoice `e78b972e-ba60-44ea-8e23-8d5610d5e870`. The **1 CCD** amount applies to that checkout. [Purchase record with both invoice IDs](../evidence/concordium-mainnet-diagnose-2026-11-26.json)

| Charge | Paid by | Amount |
| --- | --- | ---: |
| Diagnose assessment paid to merchant `…QXEc` | Buyer `…VtGCu` | 1 CCD |
| Concordium network fee | Sponsor `…NprXf` | 5.205281 CCD |

**On-chain transfer.** Concordium’s Mainnet node confirmed finalization in block **54,794,219** at **10:11:51.785 UTC**. The buyer paid zero network fee. [98b0274318f0e71c9e722a1b650d29ca877f194d98e9741846a6ed1a68b51b72 on CCDExplorer](https://ccdexplorer.io/mainnet/transaction/98b0274318f0e71c9e722a1b650d29ca877f194d98e9741846a6ed1a68b51b72)

**Seller receipt.** FAHCE returned **`CLEAR_WITH_CEILING`** for the supplied evidence. The receipt’s own payment status remains **`AUTHORIZED_PENDING_GATEWAY_SETTLEMENT`**. FAHCE’s published card confirms the receipt SHA-256 supplied by the purchase owner, `16299d534398a7fdf2714a5a79c26b1488b3af66c1e1f678423c4159beb4faf8`, and ties it to the replacement invoice and finalized transfer. [FAHCE Mainnet card](https://fahce.kinganlogic.com/.well-known/agent-card-5134-v1.json)

## Verify the November 26 sponsored purchase

Tool Offer bought FAHCE’s Diagnose assessment of the synthetic Berlin report. Invoice `03b352b4-d915-4b45-91ac-1be894100b1a` identifies both the purchase and the signed Diagnose run.

| Charge | Paid by | Amount |
| --- | --- | ---: |
| Diagnose assessment paid to FAHCE account `…TqXpTY` | Buyer `…Pbgt6n` | 52 CCD |
| Concordium network fee | Facilitator `…FGGrS1` | 5.214944 CCD |

**Settlement.** The sponsored V1 transfer finalized in Testnet block **51,310,007**, with block time **07:37:20.495 UTC**. Compare the transaction hash and block in the purchase record with CCDExplorer. [44b51cfb0aa49ca5ecdb751e19f092b970a5bd630301994b3b6c6dfbf0f61068](https://ccdexplorer.io/testnet/transaction/44b51cfb0aa49ca5ecdb751e19f092b970a5bd630301994b3b6c6dfbf0f61068) · [Purchase evidence](../evidence/concordium-testnet-diagnose-2026-11-26.json)

**Delivery.** At **08:29:33 UTC**, the authenticated `POST /testnet/buy/result` returned **HTTP 200**. FAHCE recorded the payment admission as `VERIFIED` and the Diagnose result as **`CLEAR_WITH_CEILING`**. The assessment covers the claims in the submitted report against the supplied synthetic evidence.

**Receipt verification.** The live bridge reported **`RECEIPT_VERIFICATION_FAILED`** on that HTTP 200 read. The maintainer later verified the saved receipt’s attestation offline using the pinned FAHCE policy and Microsoft Azure Attestation public keys. The signed input digest matched the submitted report, and the returned payment details matched the finalized transaction.

The receipt SHA-256 below covers the full signed response encoded as compact, sorted-key UTF-8 JSON with no trailing newline.

```text
9b21161e5372adeef7b870df8db2843f832e68e13e2b533f3aa1aa8c9af9f564
```

## Account activity on CCDExplorer

The counts below cover each account’s full Transactions tab as read on November 26, 2026, including its creation. Several accounts appear in the same transaction. The linked purchase records above identify the transfers that have corresponding Diagnose results.

### Mainnet

| Account and role | Activity visible on CCDExplorer |
| --- | --- |
| [104916 · buyer](https://ccdexplorer.io/mainnet/account/104916/alias/11ddJvKPkFEGd572VtGCu) · 13 entries | Received 2,680 CCD from the account labeled KuCoin #2. Sent 2, 200 and 500 CCD to the seller, then three transfers of 53.118593 CCD each. Sent 300 and 75 CCD to account 104964. On November 22 it reserved 136.285487 CCD in the bundle contract and received 83.867992 CCD back on capture. On November 26 it sent the seller 1 CCD for Diagnose. |
| [104920 · seller and registered owner](https://ccdexplorer.io/mainnet/account/104920/alias/cFb6Jdx4D73bBTCfiQXEc) · 22 entries | Received the buyer’s seven direct transfers, including the 1 CCD purchase, plus 52.417495 CCD from the November 22 bundle capture. Six CIS-8004 registrations and seven card updates cover FAHCE #5134, Tool Offer #5135, Kingan Logic Systems, NPL, Torivane and Partizan. After settlement the owner updated FAHCE’s card hash in block 54,795,089. [FAHCE card update](https://ccdexplorer.io/mainnet/transaction/c7dd599cce89988c62b37b99c352eb3d31faa8730866cafe59111eeeeed54ae7) |
| [104964 · November 26 fee sponsor](https://ccdexplorer.io/mainnet/account/104964/alias/M7tqcWj3cfJtAM53NprXf) · 8 entries | Received the buyer’s 300 and 75 CCD transfers. On November 22 it deployed the module, initialized `fahce_bundle` at `10111,0`, updated its credential keys and called `capture`. The contract paid the seller 52.417495 CCD and returned 83.867992 CCD to the buyer. On November 26 this account paid the 5.205281 CCD network fee. [November 22 capture](https://ccdexplorer.io/mainnet/transaction/6c76e046bcb0072bc11c063b099d0c4af059e47da1448db1bcb92751ba839db3) |

### Testnet

| Account and role | Activity visible on CCDExplorer |
| --- | --- |
| [19433 · buyer](https://ccdexplorer.io/testnet/account/19433/alias/ynTdQSDLkg63Mo8Pbgt6n) · 14 entries | Received 20,000 CCD from account 12. Sent the seller 110.116999 and 17.205781 CCD, then six transfers of 52 CCD each (four on November 21, one on November 22 and one on November 26). Deployed the bundle module and made two 135.2 CCD reservations at `13113,0`. It called `expire` on the first and received 135.2 CCD back. [Expiry and refund](https://ccdexplorer.io/testnet/transaction/41b047ae42db2537e2e409e7165c2928ffc6b983af21e866ddbc31015dfa1a6d) |
| [19470 · seller and registered owner](https://ccdexplorer.io/testnet/account/19470/alias/TomNBePZ25YQ2oJTqXpTY) · 26 entries | Received 20,000 CCD from account 12, the buyer’s eight direct transfers and 135.2 CCD from the second bundle reservation. Its history shows six registrations, eight card updates and one rejected contract call. On November 26 the owner updated the cards for FAHCE #1207 and Tool Offer #1206. [FAHCE update](https://ccdexplorer.io/testnet/transaction/e27819d77c3561dcf5e899f22baf3f317bce0e0abfd08a5a0fe7606f9f95e526) · [Tool Offer update](https://ccdexplorer.io/testnet/transaction/2a5a38e5094b37a943f122034722bf112e4300e86000ca00c7b800c7fb429995) |
| [19709 · verifier](https://ccdexplorer.io/testnet/account/19709/alias/EiJHV6iG2ArHU4knzQE3B) · 5 entries | Received 20,000 CCD from account 12, initialized `fahce_bundle` at `13113,0` and updated its credential keys. On November 22 its `capture` call released 135.2 CCD to the seller. The November 26 purchase lists a separate facilitator, account **19003** (`…FGGrS1`), as payer of the **5.214944 CCD** fee. [Verifier’s capture](https://ccdexplorer.io/testnet/transaction/4091f253f762328bf7274ba985b59b362dc99c24b6a5f65125330802bd751523) · [Sponsored purchase](https://ccdexplorer.io/testnet/transaction/44b51cfb0aa49ca5ecdb751e19f092b970a5bd630301994b3b6c6dfbf0f61068) |

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
| November 26 registry readback | At **09:20 UTC**, Concordium reported both Testnet agents **Active** and matched each published card to its on-chain metadata hash. [Tool Offer #1206 badge](https://agent-registry-mcp.concordium.com/v1/badge-check/JyP9XKcq6jVeeKxnfj2Rk) · [FAHCE #1207 badge](https://agent-registry-mcp.concordium.com/v1/badge-check/JyP9XLiK2kzaUTCXVCeWL) |
| November 21 public build | [Mandate binding](../tool_offer_agent/concordium_mandate.py), [agent signature verification](../tool_offer_agent/concordium_mandate_auth.py), [wallet binding](../bridge/concordium-testnet/verify-wallet-binding.mjs), [independent checker](../tool_offer_agent/weather_report_acceptance.py) and [portable fixture demo](../tests/trusted_agents_demo.py) are available here. The 1 CCD synthetic report is a separate scenario, **not** a live quote for FAHCE Diagnose. |
| November 22 live purchase | Tool Offer bought a FAHCE Diagnose assessment with a wallet-approved native CCD transfer on Testnet. [Check the transfer and read the result](#verify-the-november-22-testnet-purchase) |
| November 26 sponsored x402 purchase | A facilitator paid the fee on the buyer’s finalized 52 CCD transfer. [Result and receipt verification](#verify-the-november-26-sponsored-purchase) |
| November 26 purchase-page badge check | At **09:29:46.925 UTC**, a request to the existing Diagnose page on port 8767 triggered a live Testnet check for FAHCE #1207. The registry returned **HTTP 200**, on-chain status **Active**, and `badge_valid: true`. Tool Offer then served the page in paid-invoice, read-only mode. The page requires a fresh valid, active badge on each opening and refuses access if the check fails. [Page access record](../evidence/concordium-testnet-fahce-badge-check-2026-11-26.json) · [FAHCE badge check](https://agent-registry-mcp.concordium.com/v1/badge-check/JyP9XLiK2kzaUTCXVCeWL) |
| November 26 Mainnet registry update after settlement | FAHCE agent **#5134** now records the settled Diagnose purchase on its published card. The update changed only the metadata hash and finalized in block **54,795,089** with **0 CCD attached**. The card’s SHA-256 matches the on-chain value `b73d4629f22cf94734acb4061a55650fd5e2496e597983392265af05ede0c639`. The badge check passed. [Registry update transaction](https://ccdexplorer.io/mainnet/transaction/c7dd599cce89988c62b37b99c352eb3d31faa8730866cafe59111eeeeed54ae7) · [Published card](https://fahce.kinganlogic.com/.well-known/agent-card-5134-v1.json) · [Mainnet badge check](https://agent-registry-mcp.concordium.com/v1/badge-check/Mf22omCLwQueg3uzDoucr) |

## From checkpoint to production

1. **Identity and authority.** Demonstrate both registry identities and the exact buyer mandate in one live trace. Bind the service, supplier, recipient, amount, network, scope and expiry, and show enforcement of revocation and the pre-execution FAHCE decision. The November 22 wallet approval and the local mandate tests cover different steps.
2. **Concordium x402.** The November 26 Testnet record ties the sponsored transfer to the paid invoice and signed Diagnose result. The Mainnet checkout served a sponsor-signed challenge before the wallet paid the replacement invoice. Publishing a redacted challenge and the facilitator’s settlement checks would let judges independently reproduce that part of the trace.
3. **Delivery, repair and recovery.** Give a judge a portable record tying finality to independent buyer acceptance. Show that recovery after a restart returns the same delivery with one payment and one dispatch. For a rejected delivery, preserve the original, bind one authorized repair to the failed claims, and rerun the same buyer acceptance checks against both versions. Keep the evidence portable. Version any proposed acceptance-rule change, obtain owner approval before applying it, and demonstrate rollback to the approved baseline.
4. **Mainnet operations.** Tool Offer is registered as Mainnet agent #5135 and completed the private Diagnose checkout described above. FAHCE’s card records that this purchase did not consult the registry. Remaining production checks include verifying both identities at checkout, enforcing recipient, genesis, tariff and fee limits, and testing replay protection, monitoring, custody and recovery. [Tool Offer Mainnet badge](https://agent-registry-mcp.concordium.com/v1/check-badge/Mf22onHpsSQaWB9iCEdWR?network=mainnet)

**Submission.** Checkpoint 1 is **November 22, 2026 at 23:59 UTC**. Final submission is **December 9, 2026 at 23:59 UTC**. The November 22 transaction is available on CCDExplorer. Remaining submission material includes the ≤3-minute video and instructions for reproducing the end-to-end Testnet flow. [Organizer brief](https://www.concordium.com/article/concordium-trusted-agents-hackathon-encode-club) · [Encode programme](https://www.encodeclub.com/programmes/concordium-trusted-agents-hackathon)
