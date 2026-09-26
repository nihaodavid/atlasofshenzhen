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

The domain was purchased with Cloudflare DNS. Decide one of:

**Option A — keep Cloudflare managing DNS (recommended)**

In the Cloudflare dashboard for `atlasofshenzhen.online` → **DNS → Records**,
add:

| Type | Name | Value | Proxy |
|---|---|---|---|
| `A` | `@` | `76.76.21.21` | DNS only (grey cloud) |
| `CNAME` | `www` | `cname.vercel-dns.com` | DNS only (grey cloud) |

> Start with the proxy **off** (grey cloud). Cloudflare's proxy can interfere
> with Vercel's automatic TLS issuance. Once the certificate is issued and the
> site loads correctly, you may switch to proxied (orange cloud) if you want
> Cloudflare's caching — but re-test HTTPS afterwards.

**Option B — move DNS to Vercel entirely**

In Vercel → Domains → the domain → **Nameservers**, copy the two
`ns1.vercel-dns.com` / `ns2.vercel-dns.com` values, then set them as the
custom nameservers in your registrar. DNS propagation then takes up to 48 h
(usually well under an hour).

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
Expected for now — content images still point at the Squarespace CDN. See
*Next steps* in the README. The local site assets (`/images/logo.jpg`,
`/images/hero-flower.webp`) are served from the repo and always work.

---

## Deployment checklist

- [ ] Repo pushed, `node_modules/` and `dist/` excluded
- [ ] Vercel project imported, Node 22.x
- [ ] Build succeeds; `*.vercel.app` preview verified
- [ ] Custom domain added, DNS records set, TLS issued
- [ ] Old `.cn` domain 301-redirects to the new domain
- [ ] Sitemap submitted to Google Search Console:
      `https://atlasofshenzhen.online/sitemap-index.xml`
- [ ] Analytics/monitoring considered (Vercel Analytics or similar)
