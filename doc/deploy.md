# Deploying the app to Cloud Run

The app runs as a Cloud Run service called `miflaga` in `us-central1`; the
project, service name and region are in `.gcp.conf`. It has
no database and no secrets.

## Regular deploy

```bash
gcloud_deploy.sh
```

The script (from `utils-bash`) wraps `gcloud run deploy --source .`: Cloud
Build builds the `Dockerfile` and the new revision replaces the old one
with no downtime. It also writes `build_info.json`, which the service
serves back at `/app/version` together with the Cloud Run revision, so a
deploy can be verified from the outside:

```bash
gcloud_browse.sh -n app/version
```

`/app/version` is the one path that is never redirected, so it can be asked
of every address. `gcloud_browse.sh` prefers the custom domain. For the run.app address in
its stable project-number form (the one to give to scripts and health
checks), use:

```bash
gcloud_browser_gcp_url.sh
```

## One-time project setup

`gcloud_project_setup.sh` enables the APIs a source deploy needs (Cloud
Run, Cloud Build, Artifact Registry). Nothing else is required.

## Addresses

The site has one address, `https://miflaga.online`; every other name the
service answers on redirects there. See [addresses.md](addresses.md).

## Local development

```bash
uv sync
python src/main.py
```
