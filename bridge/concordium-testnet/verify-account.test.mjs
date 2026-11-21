
import test from 'node:test';
import assert from 'node:assert/strict';
import {randomBytes, createPrivateKey, createPublicKey} from 'node:crypto';
import {
  AccountAddress, buildAccountSigner, signMessage
} from '@concordium/web-sdk';
import {verifyAccountProof} from './verify-account.mjs';

function fixture() {
  const seed = randomBytes(32);
  const privateKey = createPrivateKey({
    key: Buffer.concat([
      Buffer.from('302e020100300506032b657004220420', 'hex'), seed
    ]),
    format: 'der', type: 'pkcs8'
  });
  const publicKey = createPublicKey(privateKey)
    .export({format:'der', type:'spki'}).subarray(-32).toString('hex');
  const address = AccountAddress.fromBuffer(randomBytes(32));
  return {
    address,
    signer: buildAccountSigner(seed.toString('hex')),
    accountInfo: {
      accountAddress: address,
      accountThreshold: 1,
      accountCredentials: {
        0: {value: {contents: {credentialPublicKeys: {
          threshold: 1,
          keys: {0: {schemeId: 'Ed25519', verifyKey: publicKey}}
        }}}}
      }
    }
  };
}

async function proof() {
  const f = fixture();
  const message = 'TOOL_OFFER_SYNTHETIC_ACCOUNT_PROOF_V1:testnet:nonce-1';
  return {
    f,
    args: {
      expectedAccount: AccountAddress.toBase58(f.address),
      message,
      signature: await signMessage(f.address, message, f.signer),
      accountInfo: f.accountInfo
    }
  };
}

test('real SDK signature verifies without granting delegation or dispatch', async()=>{
  const {args} = await proof();
  const result = await verifyAccountProof(args);
  assert.equal(result.account_signature_verified, true);
  for (const field of [
    'network_verified', 'delegation_verified',
    'company_identity_verified', 'dispatch_authorized'
  ]) assert.equal(result[field], false);
});

test('changed message is rejected', async()=>{
  const {args} = await proof();
  await assert.rejects(
    verifyAccountProof({...args, message: args.message + ':changed'}),
    /ACCOUNT_SIGNATURE_INVALID/
  );
});

test('signature from another key is rejected', async()=>{
  const {args, f} = await proof();
  const other = fixture();
  const signature = await signMessage(f.address, args.message, other.signer);
  await assert.rejects(
    verifyAccountProof({...args, signature}), /ACCOUNT_SIGNATURE_INVALID/
  );
});

test('different account is rejected', async()=>{
  const {args} = await proof();
  await assert.rejects(verifyAccountProof({
    ...args, expectedAccount: AccountAddress.toBase58(fixture().address)
  }), /ACCOUNT_MISMATCH/);
});

test('missing credential signatures are rejected', async()=>{
  const {args} = await proof();
  await assert.rejects(
    verifyAccountProof({...args, signature: {}}), /ACCOUNT_SIGNATURE_INVALID/
  );
});

test('insufficient account credential threshold is rejected', async()=>{
  const {args} = await proof();
  args.accountInfo.accountThreshold = 2;
  await assert.rejects(verifyAccountProof(args), /ACCOUNT_SIGNATURE_INVALID/);
});

test('insufficient keys within a credential are rejected', async()=>{
  const {args} = await proof();
  args.accountInfo.accountCredentials[0].value.contents
    .credentialPublicKeys.threshold = 2;
  await assert.rejects(verifyAccountProof(args), /ACCOUNT_SIGNATURE_INVALID/);
});

test('unknown credential or key is rejected', async()=>{
  const {args} = await proof();
  const signature = args.signature[0][0];
  for (const invalid of [{1:{0:signature}}, {0:{1:signature}}]) {
    await assert.rejects(
      verifyAccountProof({...args, signature: invalid}),
      /ACCOUNT_SIGNATURE_INVALID/
    );
  }
});

test('empty or oversized challenge is rejected', async()=>{
  const {args} = await proof();
  for (const message of ['', 'x'.repeat(16385)]) {
    await assert.rejects(
      verifyAccountProof({...args, message}), /INVALID_CHALLENGE/
    );
  }
});
