# Public, independently checked Lean proofs

For Hydra's single product roadmap and current Alpha-v25 theorem/definition
authority, see [`HYDRA_PRODUCT_ROADMAP.md`](HYDRA_PRODUCT_ROADMAP.md).
The public selector reads the same **2,080-theorem**, **6,633-edge** checked
Alpha v25 release and unchanged **432-theorem Stable default** as every other
campaign browser. Its **27 proof families**, **29 canonical theorem-graph
surfaces**, and **3,937 eligible staged graph/theorem pages** share one
same-origin proof action; all **764 checked Alpha exact-edition theorem
pages** require both their original independent checked-use receipts.

The published theorem explorers can build a selected Peano theorem, reconstruct
its complete named dependency strand, independently compile the generated Lean
code, report progress, download its proof, and open every genuinely standalone
proof directly in Lean Live.

The existing faculty website is static Apache with PHP 7.4. Its Python is 3.8,
Lean is not installed, and persistent server daemons are prohibited. Hydra does
not install a daemon, toolchain, repository checkout, private companion, or SSH
credential on that host. The faculty web and SSH login machines are distinct,
but share the owner's private home directory. The public installation has four
separate pieces:

1. The unchanged canonical proof-family pages and two selector assets are
   staged under `~/public_html/proofs/`.
2. A narrow PHP gateway is staged only under
   `~/public_html/api/lean-strands/`. It accepts the reviewed configuration,
   bounded job, progress, cancellation, and proof-download routes; it is never
   a general-purpose HTTP proxy.
3. An owner-private `~/.hydra-lean-mailbox` directory, outside `public_html`,
   connects the separate faculty PHP and SSH machines. Its foreground broker
   accepts only exact reviewed proof requests and authenticates every streamed
   response with SHA-256; its directory is `0700` and all files are `0600`.
   Bounded directory revalidation handles the faculty machines' independent
   NFS caches without introducing a public listener.
4. The normal, single-worker Lean service runs on its existing trusted machine
   at `127.0.0.1:8787`. An owner-authenticated SSH reverse tunnel exposes it
   only at `127.0.0.1:18787` on the faculty login host. The PHP gateway is its
   sole public HTTPS entrypoint.

```text
Public HTTPS theorem explorer
  https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/...
            │ same-origin JSON requests
            ▼
  /api/lean-strands/* · reviewed faculty PHP gateway
            │ owner-private shared home · 0700 directory · 0600 files
            ▼
  ~/.hydra-lean-mailbox · foreground faculty-login broker
            │ fixed login-host loopback socket, not a public port
            ▼
  127.0.0.1:18787 ── owner-authenticated SSH ──▶ 127.0.0.1:8787
                                                   │
                                                   ▼
                                      one independently checked Lean worker
```

## Publish and start

Publish the static explorer integration and its isolated public API gateway:

```bash
make deploy-lean-public
```

Start the bounded local worker, if it is not already running, and connect the
reviewed background SSH tunnel:

```bash
make lean-public-start
```

Check the public theorem graph, reconstruct `add_comm`, independently compile
its complete standalone proof, authenticate its downloaded bytes, and validate
its exact Lean Live share:

```bash
make lean-public-check
```

On macOS Python installations without a configured OpenSSL certificate store,
the public checker and launchers automatically use an already installed
`certifi` trust bundle. Hostname and certificate verification always remain
enabled; configured system trust stores are never replaced.

Operational controls:

```bash
make lean-public-status
make lean-public-stop
```

`lean-public-status` also recognizes a safely verified foreground
`make lean-public` session and reports that the background manager does not
own it; existing operator processes are never silently terminated.

### Restart after updating local Python code

An existing Lean service does not automatically reload upgraded Python
modules. At an operator-selected maintenance time, restart a manager-owned
service explicitly:

```bash
make lean-public-stop
make lean-public-start
make lean-public-status
```

If the local service was started manually with `make lean-browser`, stop it
in its owning terminal and rerun that command there. Never automatically stop
someone else's service or interrupt an active public SSH tunnel; coordinate
any maintenance interruption with its operator. Restarting a local process
does not deploy content or change the supported same-origin public route.

The public proof action is live while the trusted machine, foreground mailbox
broker, and SSH tunnel are running. If the tunnel is offline, the public gateway
responds with a clear
JSON `503` instead of exposing a broken proof or pretending that Lean verified
it. The public website's existing static proof pages remain available.

## Security and resource boundaries

- Faculty forwarding binds exactly `127.0.0.1`, never `0.0.0.0`.
- The cross-host mailbox never enters `public_html`, rejects symbolic links and
  wrong owners, and uses atomic owner-only files with short retention.
- The gateway pins its own public hostname and the exact same-origin browser
  origin; its upstream host and ports are fixed source constants.
- Accepted routes, methods, opaque hexadecimal job identifiers, query strings,
  content types, and request/response byte limits are strictly allowlisted.
- No user-selected URL, remote command, arbitrary source text, repository file,
  credential, cookie, or environment variable is forwarded.
- Existing SSH credentials remain on the owner's machine. No credential or
  Lean companion is uploaded to the public faculty account.
- Hydra retains one compiler worker, its 1,024 MiB memory ceiling, a maximum
  1,024 theorem nodes, a 1 MiB standalone source, and a 512 KiB Lean Live URL.
- Lean Live appears only after the exact import-free standalone source is
  independently compiled and its authenticated receipt matches the share.
- Proofs requiring a checked certificate companion remain honestly labelled;
  they are downloadable but never misrepresented as standalone Lean Live code.
- `deploy-proofs` and `deploy-lean-api` retain disjoint, fixed deletion
  targets. Neither target can be widened through a Make command-line override.

The published selector is intentionally same-origin only: proof jobs and
downloads remain on the existing faculty HTTPS site and its owner-controlled
private SSH tunnel. An external HTTPS proof-service origin is not a supported
public browser path, even if a lower-level backend or staging option can be
configured independently.
