# Deploying

Two live targets on the faculty server (`bnaskrecki@lts-faculty.wmi.amu.edu.pl`, static Apache + PHP,
**no persistent daemons** — which is why the lab is fully client-side):

| URL | Server path | Contents |
|-----|-------------|----------|
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026> | `~/public_html/vietnam2026/` | landing page + built book + slides |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda> | `~/public_html/lab-lambda/` | the browser Lambda Lab |

The SSH key (`~/.ssh/id_ed25519`) is already configured for the `lts-faculty` host.

## One command

```bash
make deploy        # = stage + deploy-site + deploy-lab
```

## Step by step

```bash
# 1. Build & assemble the site (landing + book + slides) into _deploy/vietnam2026
make stage

# 2. Push the site
rsync -avz --delete _deploy/vietnam2026/ lts-faculty.wmi.amu.edu.pl:~/public_html/vietnam2026/

# 3. Push the browser lab
rsync -avz --delete --exclude '__pycache__' lab-lambda/ lts-faculty.wmi.amu.edu.pl:~/public_html/lab-lambda/
```

## Notes

- `book/_build/html/index.html` is an auto-generated redirect to `intro.html`, so `/vietnam2026/book/`
  resolves via Apache's directory index.
- All computation stays in the browser after boot; offline operation is not guaranteed until assets are
  self-hosted with a service-worker precache (audit LL-REL-001, P1).
- Formal artifacts are browsed on GitHub (`nasqret/vietnam2026/tree/main/artifacts`), not deployed to the
  server, so the landing page's artifact links point there.

## GitHub

The repository `nasqret/vietnam2026` is the source of record. Push `main`; optionally enable GitHub Pages
as a mirror of the built book.
