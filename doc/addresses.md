# The addresses of the site

The site has one address:

<https://miflaga.online>

The Cloud Run service behind it answers on four hostnames. The other three
redirect to the first, so whatever a visitor types, the address bar ends up
on `miflaga.online`.

| Hostname | What it is | Behavior |
| --- | --- | --- |
| `miflaga.online` | custom domain, bought at Cloudflare | serves the site |
| `miflaga.veltzer.org` | subdomain of the personal domain | redirects |
| `miflaga-685488725451.us-central1.run.app` | Cloud Run, project-number form | redirects |
| `miflaga-wzzqi4d64a-uc.a.run.app` | Cloud Run, older random-tag form | redirects |

All four are names for the same service (`miflaga` in `us-central1`), so a
deploy changes all of them at once.

## Why one address

Nothing in the app depends on the hostname: there is no sign-in, no cookie
and no stored state, so the site worked the same on every name. (In
gcp-myworld the same redirect is a necessity, because OAuth redirect URIs
and cookies belong to a single origin.) Here the reasons are tidiness:

- Search engines see one page rather than four copies, and cannot choose a
  run.app name as the one to show.
- The share button sends the address of the page it is on, so shared links
  always carry `miflaga.online`.
- Analytics or a sign-in, if ever added, start from a single origin.

## How the redirect works

`gcloud_deploy.sh` passes `gcp_domain` from `.gcp.conf` to the service as
the `CANONICAL_HOST` environment variable. A `before_request` hook in
`src/main.py` compares the `Host` of each request with it and answers any
other host with a `308` to the same path and query on
`https://miflaga.online`. A `308` keeps the request method, unlike a `301`.

Two exceptions:

- `/app/version` is never redirected, so the deploy stamp can be asked of
  each address directly: `curl https://miflaga.veltzer.org/app/version`.
- When `CANONICAL_HOST` is unset, as in local development, nothing is
  redirected and the app answers on whatever host it is reached on.

The redirect is the app's own doing. Cloud Run and Cloudflare only route
each name to the service; the mappings below must stay in place for the
redirecting names to resolve at all.

## How each name reaches the service

The two run.app names come with the service and need no setup.

The two custom names each have a Cloud Run domain mapping, which also
issues and renews the TLS certificate, and DNS records at Cloudflare.
Those records are plain DNS (proxy off): Google has to see the origin
directly, or it cannot issue the certificate.

### `miflaga.online`

The domain was verified for the Google account (a
`google-site-verification` TXT record on `@`), then `gcloud_run_domain.sh`
(from `utils-bash`) created the mapping and printed the `A` and `AAAA`
records, which were imported at Cloudflare as a BIND zone file with "proxy
imported records" off. `gcloud_run_domain.sh` doubles as the certificate
status check. `www.miflaga.online` is not mapped.

### `miflaga.veltzer.org`

`veltzer.org` was already verified (`gcloud domains list-user-verified`),
so this took a mapping and one record:

```bash
gcloud beta run domain-mappings create --service miflaga \
    --domain miflaga.veltzer.org --region us-central1
```

and at Cloudflare, in the `veltzer.org` zone, DNS only:
`miflaga CNAME ghs.googlehosted.com`.

The certificate took close to an hour to arrive, and Cloud Run reported
"challenge data was not visible through the public internet" for most of
that time although the record resolved everywhere. Its progress shows in:

```bash
gcloud beta run domain-mappings describe \
    --domain miflaga.veltzer.org --region us-central1
```

## Changing things

- Another redirecting name: create a mapping and a DNS record as for
  `miflaga.veltzer.org`. The app needs no change and no deploy, since it
  redirects every host that is not `CANONICAL_HOST`.
- A different canonical address: change `gcp_domain` in `.gcp.conf` and
  deploy. The old name keeps working as a redirect while its mapping
  stays.
- Serving a second name as it is, without a redirect: the app would need a
  list of such names, as gcp-nikuda and gcp-myworld have in
  `gcp_alias_domains` and `ALIAS_HOSTS`.
