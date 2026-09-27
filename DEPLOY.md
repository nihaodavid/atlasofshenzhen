# Deployment guide — GitHub → Vercel

Target: get the rebuilt site live on **atlasofshenzhen.online** with **zero
downtime**, and without touching the existing Squarespace site until the new
one is verified.

> **Order matters.** Never point DNS at Vercel before the new site builds
> successfully there. Do it in the sequence below and the old site stays up
> the entire time.

---

## Phase 1 — Push to GitHub

The repository is <https://github.com/nihaodavid/atlasofshenzhen>.

### 1.1 First push (if the repo is empty)

```bash
cd atlas-of-shenzhen

git init
git branch -M main
git add .
git commit -m "Rebuild Atlas of Shenzhen on Astro, migrated from Squarespace"
git remote add origin https://github.com/nihaodavid/atlasofshenzhen.git
git push -u origin main
```

If the remote already has commits, pull first to avoid a non-fast-forward
error:

```bash
git pull --rebase origin main
git push -u origin main
```

### 1.2 If the repo already has content you want to keep

```bash
git init
git remote add origin https://github.com/nihaodavid/atlasofshenzhen.git
git fetch origin
git checkout -b main origin/main
# copy the project files in, then:
git add .
git commit -m "Add Astro rebuild"
git push origin main
```

**Verify:** the repo shows `package.json`, `src/`, `content/`, and
`vercel.json`. `node_modules/` and `dist/` must **not** appear (they are
git-ignored).

---

## Phase 2 — Import into Vercel

1. Sign in at <https://vercel.com> and choose **Add New → Project**.
2. **Import Git Repository** → authorise GitHub if prompted → select
   `nihaodavid/atlasofshenzhen`.
3. Vercel auto-detects Astro. Confirm these settings:

   | Setting | Value |
   |---|---|
   | Framework Preset | `Astro` |
   | Root Directory | `./` |
   | Build Command | `npm run build` |
   | Output Directory | `dist` |
   | Install Command | `npm install` |
   | Node.js Version | `22.x` |

4. Click **Deploy**. First build takes roughly 1–3 minutes.

**Verify:** the deployment succeeds and `https://<project>.vercel.app` loads
the new site — homepage, `/videos/`, and a video detail page.

> Do **not** add the custom domain yet. Test on the `.vercel.app` URL first.

---

## Phase 3 — Check the preview deployment

Open the `*.vercel.app` URL and confirm:

- [ ] Homepage hero shows the teal panel with the flower artwork
- [ ] All four nav items work; About and Opinions open their dropdowns
- [ ] At least one job from each collection loads (a video, an article)
- [ ] A video detail page shows a thumbnail that plays on click
- [ ] Page source contains `<title>` and `<meta name="description">` (SEO)
- [ ] Tab through the header — focus outlines are visible (a11y)
- [ ] Resize to mobile width — the burger menu opens the drawer

Only proceed once these pass.

---

## Phase 4 — Add the custom domain

1. Vercel project → **Settings → Domains** → **Add**.
2. Enter `atlasofshenzhen.online`, and add `www.atlasofshenzhen.online` too.
3. Choose which one is canonical; Vercel will 308-redirect the other.

Vercel will then show the DNS records you need. Because you have API/Vercel
access, either add them in the dashboard or via the CLI:

```bash
npm i -g vercel
vercel login
vercel domains add atlasofshenzhen.online
vercel domains add www.atlasofshenzhen.online
vercel domains inspect atlasofshenzhen.online   # prints required DNS records
```

### 4.1 Locate your current nameservers

**This domain uses Porkbun nameservers** (verified via the Vercel domain
config API), *not* Cloudflare:

```
maceio.ns.porkbun.com     curitiba.ns.porkbun.com
salvador.ns.porkbun.com   fortaleza.ns.porkbun.com
```

Two options — pick one.

**Option A — add DNS records at Porkbun (recommended, fastest)**

In Porkbun → **Domain Management → atlasofshenzhen.online → DNS Records**,
delete the existing `A` records for `@` (currently `207.207.210.107` and
`207.207.210.229`) and add:

| Type | Host | Answer | TTL |
|---|---|---|---|
| `A` | *(blank / @)* | `216.198.79.1` | 600 |
| `A` | *(blank / @)* | `64.29.17.1` | 600 |
| `CNAME` | `www` | `0dc97e5e951fca09.vercel-dns-017.com` | 600 |

> Those are Vercel's **rank-1 recommended** values for this domain. The older
> `76.76.21.21` / `cname.vercel-dns.com` pair (rank 2) also works. Do not mix
> ranks — pick one set.

**Option B — delegate DNS to Vercel entirely**

Change the domain's nameservers at Porkbun to `ns1.vercel-dns.com` and
`ns2.vercel-dns.com`. Propagation takes up to 48 h (usually well under an
hour), and Vercel then manages all records.

**Option C — move to Cloudflare (if you want Cloudflare in front)**

Add the site at Cloudflare, then create the same records as Option A with the
proxy set to **DNS only (grey cloud)** first. Turn the orange cloud on only
after Vercel has issued the TLS certificate.

### 4.2 Wait for verification

Vercel shows the domain as **Valid** once it resolves and TLS is issued.
Check with:

```bash
dig +short atlasofshenzhen.online
curl -I https://atlasofshenzhen.online
```

---

## Phase 5 — Switch production traffic (zero downtime)

If the new domain and the old site are different domains, there is nothing to
"switch" — `atlasofshenzhen.online` is simply new. The only remaining task is
to decide what happens to the old `.cn` domain.

### Recommended: 301-redirect the old domain

This preserves search ranking and keeps existing links working.

In Squarespace: **Settings → Domains → atlasofshenzhen.cn → Add forwarding /
redirect** to `https://atlasofshenzhen.online`, using **301 (permanent)**.

Alternatively, if you move the `.cn` domain's DNS elsewhere, add a redirect
rule sending every path to the same path on the new domain:

```
/history/coffee-old  ->  https://atlasofshenzhen.online/history/coffee-old
```

Because this rebuild preserves every original permalink, a single
"redirect all paths, keeping the path" rule is sufficient — no per-page map
needed.

> **Do not** leave the `.cn` domain resolving to the old Squarespace site
> indefinitely. Duplicate content hurts SEO, and the two sites will diverge.

---

## Rollback

The old Squarespace site is untouched throughout, so rollback is just:

1. Remove the custom domain from Vercel (**Settings → Domains → Remove**), or
2. Point DNS back to the previous records.

Nothing in this plan is destructive until/unless you explicitly shut the
Squarespace subscription down — and that should wait until the new site has
run happily for at least two weeks.

---

## Troubleshooting

**Vercel CLI rejects the token (`token is not valid`) but the REST API accepts it**
Vercel's newer `vck_`-prefixed tokens can be *restricted* (the user profile
shows `"limited": true`). Such a token reads fine over REST but cannot create
projects (`403 forbidden`) or attach domains, and CLI 60.x fails its
`whoami` probe on them. Create the token again from
<https://vercel.com/account/tokens> with **Full Access**, or import the project
through the dashboard instead.

**Vercel build fails with a JSON parse error on `vercel.json`**
`vercel.json` is parsed as strict JSON — no `//` comments, no trailing commas.
Validate with `python -c "import json;json.load(open('vercel.json'))"`.

**Build fails on Vercel but works locally**
Almost always a Node version mismatch. Set Node to `22.x` in
**Settings → General → Node.js Version**, then redeploy.

**`404` on a page that exists locally**
Check you committed `content/`. It is required at build time; if it is
missing from the repo the dynamic routes generate nothing.

**Domain stuck on "Invalid Configuration"**
DNS has not propagated, or the Cloudflare proxy is on. Set it to grey cloud
and re-check with `dig`.

**TLS certificate not issued**
Give it up to 24 h after DNS resolves. If it stalls, remove and re-add the
domain in Vercel to retrigger issuance.

**Images not loading**
All media is now localized — every image is committed under
`public/images/<collection>/` as WebP and every reference points at
`/images/...` on our own domain. There are no Squarespace CDN URLs left.
If an image 404s, it was pruned as unused: check `.media-backup/` and
restore it, or re-run `scripts/fetch_media.py`.

**Pushes do not trigger a deployment**
The project must be linked to the *correct* repository **and** the Vercel
GitHub App must be installed on that repo. Verify the link:

```bash
curl -s --proxy "$PROXY" -H "Authorization: Bearer $TOKEN" \
  "https://api.vercel.com/v9/projects/$PROJECT_ID" \
  | python -c "import sys,json;print(json.load(sys.stdin).get('link'))"
```

If `link.repo` is not `nihaodavid/atlasofshenzhen`, unlink and relink:

```bash
curl -s -X DELETE "https://api.vercel.com/v9/projects/$PROJECT_ID/link" -H "Authorization: Bearer $TOKEN"
curl -s -X POST   "https://api.vercel.com/v9/projects/$PROJECT_ID/link" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"github","repo":"nihaodavid/atlasofshenzhen","productionBranch":"main"}'
```

Relinking fails with *"you need to install the GitHub integration first"*
until the owner installs <https://github.com/apps/vercel> and grants it access
to the repository. Until then, deploy from local source:

```bash
npm i --no-save vercel@latest
VERCEL_ORG_ID=$ORG_ID VERCEL_PROJECT_ID=$PROJECT_ID \
  node_modules/.bin/vercel deploy --prod --yes --token "$TOKEN"
```

**`git push` fails with `CONNECT tunnel failed, response 502`**
The environment may inject its own proxy (e.g. `HTTPS_PROXY=127.0.0.1:53514`)
that is broken for git. Probe ports, then pin the working one explicitly:

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
git -c http.proxy=http://127.0.0.1:7890 -c http.version=HTTP/1.1 push origin main
```

If git then reports `could not read Username ... terminal prompts disabled`,
pass the token in the URL for that one command and disable the credential
helper so it is not cached:

```bash
git -c http.proxy=http://127.0.0.1:7890 -c credential.helper= \
    push "https://<TOKEN>@github.com/nihaodavid/atlasofshenzhen.git" main
```

---

## Deployment checklist

- [x] Repo pushed, `node_modules/` and `dist/` excluded
- [x] Vercel project imported, Node 22.x
- [x] Build succeeds; production deployment verified (71 pages)
- [x] Custom domain added, DNS records set, TLS issued
- [x] All media localized to WebP; zero Squarespace references
- [ ] Vercel GitHub App installed on `nihaodavid/atlasofshenzhen` (auto-deploy)
- [ ] Old `.cn` domain 301-redirects to the new domain
- [ ] Sitemap submitted to Google Search Console:
      `https://atlasofshenzhen.online/sitemap-index.xml`
- [ ] Analytics/monitoring considered (Vercel Analytics or similar)
