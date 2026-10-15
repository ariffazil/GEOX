# IDENTITY_BINDING_PLAN.md — GATE A

**Status:** PLAN — not executed. No signing mutation performed this run.
**Actor state:** KEY MATERIAL CONSISTENT / SESSION BINDING UNRESOLVED / ACTOR VERIFICATION FAILED.
**Principle:** do NOT regenerate keys · do NOT print private material · do NOT patch kernel · do NOT restart services · do NOT delete identity.json.

---

## 1. Traced contract (all OBS, 2026-10-14)

### 1.1 Active harness plugin — `arif-core/index.ts`
- `CRYPTO_ACTOR = "333-AGI"` · `IDENTITY_KEY_PEM = "/root/AAA/IDENTITY/keys/333-AGI_private.pem"`
- `bindKernelSession()` sequence (lines ~258–300):
  1. `arifosCall("arif_init", { mode: "challenge", actor_id: CRYPTO_ACTOR })`
  2. expect `nonce` in result — else `receipt({event:"session.created.no_challenge"})` → **falls back to anon**
  3. `signActorMessage(nonce)` → Ed25519 sign of `"<CRYPTO_ACTOR>:<nonce>"` (wire form must match actor_id)
  4. `arifosCall("arif_init", { mode:"init", actor_id, actor_signature, nonce, intent, requested_authority:"MUTATE" })`
- Plugin note (OBS): "`parent_session_id` is NOT an accepted arif_init argument (live schema, 29 args, measured 2026-10-14)".

### 1.2 Retired bridge — `plugins-retired-20261014/arifos-kernel-bridge.ts`
- Same pattern (`ACTOR_ID="333-AGI"`, same key PEM, `arif_init mode="challenge"`).
- Retired today (2026-10-14) — superseded by `arif-core`.

### 1.3 Signing lane — `localhost:18900` (LISTENING, pid 1205088)
- Process: `/usr/bin/python3 /root/AAA/auth/signing_server.py` (cwd `/root/AAA`).
- Role: **sovereign** signing — `load_sovereign_key()` loads the arifos/sovereign key, `_verify_challenge(challenge_id, submitted_canonical)`.
- NOT the agent-signing lane. The agent signs with `333-AGI_private.pem` in the plugin.

### 1.4 Kernel crypto contract — `arifOS/arifosmcp/runtime/crypto_auth.py` (read-only source)
- `canonical_serialize_challenge(fields)` binds actor+session+candidate+plan+action_class.
- `issue_authorization_challenge` (L216), `issue_actor_challenge` (L748), `issue_actor_challenge_b64(actor_id, ttl)` (L764).
- `verify_authorization_challenge` (L425), `verify_actor_signature(actor_id, nonce, sig_b64)` (L801).
- `verify_init_identity` (L860), `classify_actor_band(actor_id, signature_verified)` (L916).
- `resolve_actor_public_key(actor_id)` (L636, reads `/root/AAA/IDENTITY/keys/`), `is_registered_actor(actor_id)` (L744).
- `_find_ed25519_key` (L962), `_auto_sign_nonce` (L1001) — auto-sign for trusted paths.
- Error codes: ACTOR_MISMATCH / SESSION_MISMATCH / CANDIDATE_HASH_MISMATCH / PLAN_HASH_MISMATCH / AUDIENCE_MISMATCH / CHALLENGE_UNKNOWN.
- Challenge nonces single-use, TTL default 120s; Redis-backed durable store (F13 challenges).

### 1.5 LIVE `arif_init` mode enum (probed, OBS)
`init | light | resume | validate | canary | preflight | triage | epoch_open | epoch_seal | opt_out | opt_out_profiling`
→ **"challenge" is ABSENT.**

---

## 2. Root cause of auto-anon (DER — hypothesis, not proven)

The harness plugin calls `arif_init { mode: "challenge" }`, but the LIVE kernel's
`arif_init` schema no longer accepts `mode="challenge"`. The challenge entry point
was refactored OUT of `arif_init` into `crypto_auth` (`issue_actor_challenge_b64` /
`verify_actor_signature`). Result: challenge call → schema rejection (or empty nonce)
→ `session.created.no_challenge` → fallback to auto-anon → OBSERVE_ONLY.

Confidence: DER 0.80. Confirmation requires reading the exact error the plugin's
`arifosCall("arif_init", {mode:"challenge"})` receives at runtime (harness log).

Alternative hypotheses (not excluded):
- H2: `arif_init` still accepts `actor_signature`+`nonce` directly, but the plugin's
  challenge-issuance hop is the only stale part (consistent with §1.5).
- H3: the 1mcp proxy strips/rewrites the challenge call — but the mode enum is
  kernel-level, so this is unlikely to change the rejection.

---

## 3. identity.json classification

- File: `/root/AAA/agents/opencode/identity.json` — `ed25519_pubkey_hex = ad61fe…`,
  `actor_id = "opencode/FI-???"`, `bound_to = "arif-fazil/F13"`.
- Kernel registry (SOT): `333-AGI` (FI-002) = `b4dc…`; `opencode` (FI-018) = `ca96…`.
- `ad61fe…` matches NEITHER registry entry.

**Classification: LEGACY (provisional) — UNKNOWN residual.**
- Evidence for LEGACY: it is a historical AAA agent-card identity (git-committed
  2026-08-12: `ecc4ed1d`, `65668bbe`) superseded by the kernel `agent_registry.json`.
- Residual UNKNOWN: not yet confirmed whether `ad61fe` was ever the registered pubkey.
  Next probe: `git show <commit>:agents/opencode/identity.json` across the two
  commits + `git log -p -- agents/opencode/identity.json` to see the historical pubkey.
- **Do NOT delete.** Do not treat as ORPHAN_CONFIRMED until that git-history check.

---

## 4. Binding plan (not executed)

| Step | Action | Authority | Blocked-by |
|---|---|---|---|
| 1 | Confirm live challenge entry point: read `arif_init` schema source + `crypto_auth` tool exposure (is `issue_actor_challenge_b64` reachable from the harness, or only via signing_server :18900?) | read-only | none |
| 2 | Choose ONE supported path: (a) `arif_init(actor_signature, nonce)` with nonce from `issue_actor_challenge_b64`, or (b) crypto_auth issue→sign→verify via signing_server | design decision → Arif/888 | §2 root-cause confirmation |
| 3 | Patch `arif-core/index.ts` `bindKernelSession()` to use the supported path (replace stale `mode:"challenge"` hop) | T1 code edit, but requires Arif authorization this run (OBSERVE_ONLY) | actor_verified gate |
| 4 | Verify: `classify_actor_band → LIMITED_MUTATE`, `mutation_allowed=True`, receipt carries actor_id "333-AGI" | verification | step 3 |
| 5 | Confirm identity.json is LEGACY via git-history probe | read-only | none |

**Hard constraints honored:** no key regen (keys consistent, `needs_keygen=False`);
no private-key print; no kernel patch; no restart; no identity.json deletion.

---

## 5. Verification of identity chain (Pitfall-10 checklist)

1. identity.key seed exists → **FAIL** (only `.STRIPPED` text note present; but PEM pair is present and consistent)
2. canonical PEM exists → **PASS** (`333-AGI_public.pem`)
3. registry pubkey == derived pubkey → **PASS** (`b4dc…` == `b4dc…`)
4. `is_registered_actor("333-AGI")` → **PASS** (registry has entry, `needs_keygen=False`)
5. challenge issuance → **UNRESOLVED** (stale `arif_init mode:"challenge"` path)
6. init with signature → **UNRESOLVED** (depends on 5)
7. session_token non-null → **UNRESOLVED**
8. `mutation_allowed=True` → **FALSE** (current: OBSERVE_ONLY)
9. `authority_band=LIMITED_MUTATE` → **FALSE** (current: OBSERVE_ONLY)
10. `arif_judge` no HTTP 406 → **PASS** (judge worked this session)

**Net:** keys + registry healthy (1-4). Binding broken at the challenge-issuance hop (5).
The fix is localized to the plugin's challenge call — no key, kernel, or service change.
