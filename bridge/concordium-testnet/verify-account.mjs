import {
  AccountAddress, verifyMessageSignature
} from '@concordium/web-sdk';

function indexMap(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const indexes = Object.keys(value);
  return indexes.length > 0 && indexes.length <= 256 && indexes.every(index =>
    /^(0|[1-9][0-9]{0,2})$/.test(index) && Number(index) <= 255);
}

function validThreshold(threshold, keys) {
  return Number.isInteger(threshold) && threshold >= 1 && threshold <= 255 &&
    threshold <= Object.keys(keys).length;
}

function validateCredentials(signature, accountInfo) {
  const credentials = accountInfo.accountCredentials;
  if (!indexMap(signature) || !indexMap(credentials) ||
      !validThreshold(accountInfo.accountThreshold, credentials) ||
      Object.keys(signature).length < accountInfo.accountThreshold) {
    throw Error('ACCOUNT_SIGNATURE_INVALID');
  }
  for (const [credentialIndex, signatures] of Object.entries(signature)) {
    const publicKeys = credentials[credentialIndex]?.value?.contents?.credentialPublicKeys;
    if (!indexMap(signatures) || !publicKeys || !indexMap(publicKeys.keys) ||
        !validThreshold(publicKeys.threshold, publicKeys.keys) ||
        Object.keys(signatures).length < publicKeys.threshold) {
      throw Error('ACCOUNT_SIGNATURE_INVALID');
    }
    for (const [keyIndex, signatureValue] of Object.entries(signatures)) {
      const key = publicKeys.keys[keyIndex];
      if (!key || key.schemeId !== 'Ed25519' ||
          typeof key.verifyKey !== 'string' || !/^[0-9a-fA-F]{64}$/.test(key.verifyKey) ||
          typeof signatureValue !== 'string' || !/^[0-9a-fA-F]{128}$/.test(signatureValue)) {
        throw Error('ACCOUNT_SIGNATURE_INVALID');
      }
    }
  }
}

// accountInfo must be freshly obtained by the trusted Testnet reader.
// message must be the exact server-retained challenge, never a client replacement.
export async function verifyAccountProof({
  expectedAccount, message, signature, accountInfo
}) {
  AccountAddress.fromBase58(expectedAccount);
  if (typeof message !== 'string' ||
      message.length === 0 ||
      Buffer.byteLength(message, 'utf8') > 16384) {
    throw new Error('INVALID_CHALLENGE');
  }
  if (!accountInfo?.accountAddress ||
      AccountAddress.toBase58(accountInfo.accountAddress) !== expectedAccount) {
    throw new Error('ACCOUNT_MISMATCH');
  }
  let valid;
  try {
    validateCredentials(signature, accountInfo);
    valid = await verifyMessageSignature(message, signature, accountInfo);
  } catch {
    throw new Error('ACCOUNT_SIGNATURE_INVALID');
  }
  if (valid !== true) throw new Error('ACCOUNT_SIGNATURE_INVALID');
  return {
    account_signature_verified: true,
    account: expectedAccount,
    network_verified: false,
    delegation_verified: false,
    company_identity_verified: false,
    dispatch_authorized: false
  };
}
