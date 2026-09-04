# Deploying the app to Cloud Run

The app runs as a Cloud Run service called `miflaga` in `us-central1`; the
gcloud configuration, service name and region are in `.gcp.conf`. It has
no database and no secrets.

## Regular deploy

```bash
gcloud_run_deploy.sh
```

The script (from `utils-bash`) wraps `gcloud run deploy --source .`: Cloud
Build builds the `Dockerfile` and the new revision replaces the old one
with no downtime. It also writes `build_info.json`, which the service
serves back at `/app/version` together with the Cloud Run revision, so a
deploy can be verified from the outside:

```bash
gcloud_browse.sh -n app/version
```

`gcloud_browse.sh` prefers the custom domain. For the run.app address in
its stable project-number form (the one to give to scripts and health
checks), use:

```bash
gcloud_browser_gcp_url.sh
```

## One-time project setup

`gcloud_project_setup.sh` enables the APIs a source deploy needs (Cloud
Run, Cloud Build, Artifact Registry). Nothing else is required.

## Custom domain

The service answers on `https://miflaga.online` (`gcp_domain` in
`.gcp.conf`). The domain is registered at Cloudflare, which also serves
its DNS; Cloud Run owns the TLS certificate through a domain mapping, so
the Cloudflare records are plain DNS (proxy off), or Google could not
issue and renew the certificate.

Set up once: the domain was verified for the Google account (a
`google-site-verification` TXT record on `@`), then `gcloud_run_domain.sh`
created the mapping and printed the `A` and `AAAA` records, which were
imported at Cloudflare as a BIND zone file with "proxy imported records"
off. `gcloud_run_domain.sh` doubles as the certificate status check.
`www.miflaga.online` is not mapped.

## Local development

```bash
uv sync
python src/main.py
```
