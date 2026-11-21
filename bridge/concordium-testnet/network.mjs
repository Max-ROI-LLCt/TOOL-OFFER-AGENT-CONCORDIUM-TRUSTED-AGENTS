
export const TESTNET_GENESIS =
  '4221332d34e1694168c2a0c0b3fd0f273809612cb13d000d5c2e00e85f50f796';

export async function readTestnetContext(client, now = Date.now()) {
  const status = await client.getConsensusStatus();
  const genesis = JSON.parse(JSON.stringify(status.genesisBlock));
  if (genesis !== TESTNET_GENESIS) throw new Error('WRONG_NETWORK_GENESIS');
  const finalizedAt = new Date(status.lastFinalizedTime).getTime();
  if (!Number.isFinite(finalizedAt) ||
      finalizedAt > now + 30000 ||
      now - finalizedAt > 180000) {
    throw new Error('STALE_OR_INVALID_FINALIZED_TIME');
  }
  return {
    network: 'concordium:testnet',
    genesis,
    observed_at: new Date(now).toISOString(),
    finalized_at: new Date(finalizedAt).toISOString(),
    finalized_block: JSON.parse(JSON.stringify(status.lastFinalizedBlock)),
    finalized_height: String(status.lastFinalizedBlockHeight),
    verification_scope: 'TLS node observation checked against published genesis',
    independent_consensus_verification: false
  };
}
