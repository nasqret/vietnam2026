# Peano read-only PHP delivery

The owner authorized implementation and preview testing on 2026-09-05, then
separately approved production promotion after the preview result and browser
limitation were reported. This file describes the transport; actual publication
results belong in the separate deployment receipts. A future production release
is not authorized merely by creating a stage or passing isolated tests.

**Preview publication verified (2026-09-05):** the unchanged HTTPS release
gate passes. See the
[deployment receipt](PEANO_PHP_DELIVERY_DEPLOYMENT_2026-09-05.md) for exact
source/stage identities, the initial rollback and remaining browser checks.

**Production promotion verified (2026-09-05):** the identical preview stage is
now live on `/peano-lab/` under separate owner approval. The full original HTTP
gate, 4,003 current/retained file hashes and 62 additional live responses pass.
The [production receipt](PEANO_PHP_PRODUCTION_2026-09-05.md) records the retained
rollback and explicitly unperformed browser acceptance checks.

## Why this exists

Both Peano `.htaccess` files already contain the intended static header rules.
Fresh live requests still lack `Cache-Control`, including on the HTML,
immutable application manifest, worker, and 404. A request to the existing
PHP endpoint does return `Cache-Control: no-store, max-age=0`. Thus there is
an account-level PHP route for supplying response headers; the observation
does not identify all modules or proxy rules in the central hosting stack.

The handler targets PHP 7.0 and later. WMI's command-line interpreter is PHP
7.4.3, but its public FPM runtime is PHP 7.0.33. Command-line lint alone does
not establish web-runtime compatibility. The first activation exposed this
difference and was rolled back; the corrected adapter avoids nullable/void
type declarations and short-form destructuring introduced after PHP 7.0.
It is a file-delivery adapter, not a persistent service or a proof executor.
No change to the kernel, proof language, browser source, application manifest,
BUILD, Stable membership or Alpha admission accompanies this transport change.
The existing static `peano-lab/.htaccess` remains unchanged for rollback.

Runtime compatibility is not a hosting-security audit. PHP 7.0 and 7.4 are
[unsupported upstream](https://www.php.net/eol.php); distribution/vendor
extended support has not been established by these tests. WMI should confirm
its security-support arrangements or upgrade the runtime separately. This
preview change does not modify the central PHP/Apache/proxy configuration.

## Request and file boundaries

- Only the dedicated Peano preview/production URL prefixes are accepted.
- Only GET and HEAD are allowed. Queries never select a filesystem path.
- Application files require their namespace-bound original manifest; arbitrary
  files, executables, hidden paths, encoded path tricks and directory listings
  are rejected. Vendor files require their canonical SHA-256 inventory.
- The old `v-2eaf25dc3894` vendor name is a byte-checked historical alias of
  `v-85fb3352e49c`; old flat vendor URLs are checked against the same inventory
  but do not receive immutable cache policy. Retained application manifests
  continue to be resolved by their own original IDs.
- Symlinks, shared-writable components, foreign-owner files and special files
  fail closed. Each authorized descriptor is hashed before streaming.
- File size is capped at 64 MiB; HTML/manifests at 1 MiB; relevant headers at
  8 KiB; request URIs at 4 KiB. Streaming uses at most 64 KiB per chunk.
- The PHP adapter has no filesystem writes, subprocesses, outbound network,
  sessions, cookies, credentials, uploads, theorem evaluation or Lean gateway.

## HTTP behavior

HTML is non-storable on both 200 and 304. Versioned successful resources,
including 206 and 304, receive one-year immutable caching. Unversioned vendor
metadata/files revalidate; every adapter error is non-storable. MIME types are
explicit and responses include `X-Content-Type-Options: nosniff`.

Server-owned denials are a separate boundary: WMI rejects `.htaccess` with
HTTP 403 before the adapter, without a cache header. That protection was
preserved and recorded separately; the adapter does not promise to control
responses generated before it runs.

ETags identify the selected identity/gzip bytes. If-Match, If-None-Match,
If-Unmodified-Since, If-Modified-Since and If-Range have their normal precedence.
Single ranges, open ranges and suffix ranges work; unsupported multipart or
malformed ranges are ignored. Unsatisfiable byte ranges return 416. HEAD does
not return a body or apply GET-only ranges. An unacceptable encoding returns
406; explicit q=0 is not overridden by a wildcard or duplicate coding.

The publisher creates deterministic gzip sidecars, verifies each compressed
hash, and independently decodes each sidecar to the exact source. The handler
checks the sidecar metadata and compressed-file hash before serving it.
`Vary: Accept-Encoding` separates negotiated responses. ZIP and WOFF2 have no
compressed sidecar and are never recompressed. Unknown older source hashes
can use an acceptable identity representation without rewriting their files.
Apache double-compression is disabled in the dedicated routing configuration.

These behaviors follow [HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
and PHP's [binary file streaming interface](https://www.php.net/manual/en/function.fpassthru.php).
The immutable source manifests and decoded-byte release checks, not this prose,
establish the actual delivery identities.

## Validation and staging

```bash
make peano-php-check PEANO_HTTP_PYTHON=python3.10
# Requires PHP CLI; it fails rather than silently skipping PHP tests.

make stage-peano-php PEANO_HTTP_PYTHON=python3.10
PYTHONDONTWRITEBYTECODE=1 python3.10 -B scripts/stage_peano_php_delivery.py --check
```

The original static stage is preserved. The separate PHP stage is created once
and later compared in full; it is never silently replaced. Its private
`.peano-delivery/stage.json` records all base and final file hashes, source
pins, exact compression sizes and original-byte preservation. It carries no
mathematical authority and is not served as a public route.

For a machine without PHP CLI, the portable PHP suite may be copied with the
exact adapter to a private temporary directory on the existing hosting account
and run there with `php -d memory_limit=64M`. It creates and removes only its
own random temporary fixture directory. This exercises the host's actual
command-line interpreter without starting a daemon or touching live content.
The unchanged real-HTTPS verifier must independently pass on the web FPM
runtime; do not infer its version or compatibility from SSH. Record the
tested file hashes and result; local Python tests are not a substitute for it.
CI has a separate transport job and does not require the private Lean companion.

## Preview activation and rollback

1. Freeze and push the clean source candidate; inspect the exact remote Peano
   preview path, original entrypoint/routing hashes and retained namespaces.
2. Preserve the current preview `.htaccess` outside the public tree and keep
   the exact local original. Retain `index.html` if a client release is changing.
3. Preview the checksum upload. Install all new immutable files and private
   transport metadata, then the PHP handler. Do not delete any old namespace.
4. Verify remote file hashes before activating the HTML and routing entrypoints.
   For this transport-only release the HTML itself is unchanged.
5. Activate the new `.htaccess` last and run:

   ```bash
   bash scripts/verify_peano_delivery.sh \
     https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next \
     _deploy/peano-lab-php
   ```

6. If any gate fails, restore only the exact retained preview `.htaccess`,
   confirm the original page hash, and record the failure. Uploaded additional
   inert files may remain for diagnosis; do not delete existing user content.
7. Confirm current and retained application/vendor responses, traversal/error
   handling and method rejection over real HTTPS. Browser visual/cold-start/Stop
   checks are separate and must not be claimed without an available browser.

Production is not changed by the preview procedure. An authorized promotion uses
the identical verified source and stage, preserves production's rollback, and
repeats all delivery gates on production. Neither missing cache headers nor a
failed compression/byte check may be bypassed by editing the verifier.
