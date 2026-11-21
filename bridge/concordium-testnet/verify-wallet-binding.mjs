
import {createHash} from 'node:crypto';
import {verifyAccountProof} from './verify-account.mjs';
import {TESTNET_GENESIS} from './network.mjs';

const actionFields = [
  'buyer', 'seller', 'operation', 'offer_hash', 'source_hash', 'input_hash',
  'acceptance_hash', 'network', 'asset', 'recipient', 'amount_atomic'
];
const bindingFields = [
  'schema', 'purpose', 'account', 'agent', 'origin', 'network', 'genesis',
  'mandate_hash', 'mandate_nonce', 'issued_at', 'expires_at', 'action',
  'native_transaction_signing'
];

function exactFields(value, fields) {
  return value && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).sort().join() === [...fields].sort().join();
}

function mandateHash(binding) {
  const mandate = {...binding.action, schema:'TOOL_OFFER_CONCORDIUM_MANDATE_V1',
    nonce:binding.mandate_nonce, issued_at:binding.issued_at, expires_at:binding.expires_at};
  const sorted = Object.fromEntries(Object.keys(mandate).sort().map(key => [key, mandate[key]]));
  return createHash('sha256').update(JSON.stringify(sorted), 'utf8').digest('hex');
}

// All expected* values and accountInfo must come from trusted server context.
// expectedMessage must be regenerated from the retained mandate by Python.
// Never take these expectations from the submitted wallet envelope.
export async function verifyWalletBinding({
  expectedMessage, expectedAccount, expectedAgent, expectedOrigin,
  expectedMandateHash, signature, accountInfo, now
}) {
  if (!Number.isSafeInteger(now) || now < 0 ||
      typeof expectedMessage !== 'string' ||
      Buffer.byteLength(expectedMessage, 'utf8') > 16384) {
    throw Error('INVALID_BINDING_CONTEXT');
  }
  let binding;
  try { binding = JSON.parse(expectedMessage); }
  catch { throw Error('INVALID_BINDING_MESSAGE'); }
  if (!exactFields(binding, bindingFields) || !exactFields(binding.action, actionFields) ||
      binding.purpose !== 'Authorize the named agent to request this exact action only' ||
      !actionFields.every(field => typeof binding.action[field] === 'string' &&
        [...binding.action[field]].length > 0 && [...binding.action[field]].length <= 512 &&
        binding.action[field].isWellFormed()) ||
      !['offer_hash', 'source_hash', 'input_hash', 'acceptance_hash'].every(field =>
        /^[0-9a-f]{64}$/.test(binding.action[field])) ||
      !/^[1-9][0-9]{0,19}$/.test(binding.action.amount_atomic) ||
      BigInt(binding.action.amount_atomic) >= 2n ** 64n ||
      binding.schema !== 'TOOL_OFFER_ACCOUNT_AGENT_MANDATE_BINDING_V1' ||
      binding.account !== expectedAccount ||
      binding.agent !== expectedAgent ||
      binding.action?.buyer !== expectedAgent ||
      binding.origin !== expectedOrigin ||
      binding.network !== 'concordium:testnet' ||
      binding.action?.network !== 'concordium:testnet' ||
      binding.action?.asset !== 'CCD' ||
      binding.genesis !== TESTNET_GENESIS ||
      !/^[0-9a-f]{64}$/.test(expectedMandateHash) ||
      binding.mandate_hash !== expectedMandateHash ||
      !/^[0-9a-f]{64}$/.test(binding.mandate_nonce) ||
      !Number.isSafeInteger(binding.issued_at) ||
      !Number.isSafeInteger(binding.expires_at) ||
      !(0 <= binding.issued_at && binding.issued_at <= now &&
        now < binding.expires_at) ||
      binding.native_transaction_signing !== 'NOT_GRANTED') {
    throw Error('WALLET_BINDING_MISMATCH_OR_EXPIRED');
  }
  if (mandateHash(binding) !== expectedMandateHash) {
    throw Error('WALLET_BINDING_MANDATE_HASH_MISMATCH');
  }
  await verifyAccountProof({
    expectedAccount, message:expectedMessage, signature, accountInfo
  });
  return {
    wallet_request_authorization_verified:true,
    account:expectedAccount,
    agent:expectedAgent,
    mandate_hash:expectedMandateHash,
    signed_message_sha256:createHash('sha256')
      .update(expectedMessage, 'utf8').digest('hex'),
    native_transaction_signing_authorized:false,
    dispatch_authorized:false
  };
}
