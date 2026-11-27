# ASPAR AGENT — client web app on Cloudflare

The client-facing ASPAR AGENT, hosted entirely on Cloudflare (free tier): one Worker serves a UI with a left sidebar — **Assistant**, **Mon projet**, **Ma maquette 3D**, **Mon compte** — behind Cloudflare Access at `agent.aspar.group`.

It is the bounded client layer described in [`domains/agent.md`](../../domains/agent.md), not the internal delivery stack: no tools, no access to Odoo, files or e-mail. The assistant only knows the conversation and the client's own project sheet; it never quotes a price, a delay or a commitment.

**Status (2026-11-27): built and tested, not deployed.**

## How it works

| Part | Implementation |
| --- | --- |
| Identity | Cloudflare Access logs each client in by e-mail. The Worker re-verifies the Access token (RS256 signature, audience, issuer, expiry) on every request and serves nothing without it, the UI included. If `ACCESS_TEAM_DOMAIN` or `ACCESS_AUD` is empty, it answers 503. |
| Client data | KV namespace `CLIENT_DATA`, keyed by the verified e-mail: `projet:<email>` (project sheet JSON) and `maquette:<email>:<file>.glb` (3D models). A client can only list and read keys under their own e-mail. |
| Assistant | Workers AI (`AI_MODEL`), no external API key. System prompt: [`src/prompt.js`](src/prompt.js). |
| Mon compte | Opens `client.aspar.group` (ASPAR OS, Odoo) in a new tab: the portal refuses to be embedded (`X-Frame-Options: SAMEORIGIN`). |
| 3D viewer | [model-viewer](https://modelviewer.dev) 4.4.0 (Apache-2.0, see `public/vendor/model-viewer.LICENSE.txt`), served from the Worker, no CDN at runtime. |
| Browser hardening | Strict CSP (`'self'` only, WebAssembly allowed for the viewer's decoder, no `eval`), `frame-ancestors 'none'`, no `*.workers.dev` URL. |

## Test

```bash
npm test        # 20 tests: Access token checks, isolation between clients, validation, chat
npm run check   # wrangler dry-run build, publishes nothing
```

## Deploy (once)

1. **Access** — In Zero Trust, create a self-hosted Access application for `agent.aspar.group` with a policy allowing the CEO's and the clients' e-mails. Put the team domain (`<team>.cloudflareaccess.com`) and the application's AUD tag in `wrangler.toml`.
2. **Storage** — `npx -y wrangler@4.169.0 kv namespace create CLIENT_DATA`, then put the returned id in `wrangler.toml`.
3. **Model** — Check that `AI_MODEL` is listed in the account's Workers AI models; change it if not.
4. **Free the hostname** — `agent.aspar.group` currently answers with a Cloudflare redirect to `www.aspar.group/app/?assistant=1`. Remove that rule (Rules, Page Rules, Bulk Redirects or a Worker route) and the hostname's DNS record.
5. **Publish** — Uncomment the `routes` line in `wrangler.toml`, then `npm run deploy`.
6. **Verify** — An anonymous visit must land on the Access login page, never on the app.

The repository is public: client e-mails and names go in the Access policy and in KV, never in this folder.

## Add a client

1. Add their e-mail to the Access policy.
2. Export the maquette from Blender: *File > Export > glTF 2.0*, format **glTF Binary (.glb)**, **Compression unchecked** (Draco/KTX2 decoders load from external CDNs that the CSP blocks).
3. Upload it under their e-mail (name: letters, digits, `.`, `_`, `-`, ending in `.glb`; 25 MiB max):

   ```bash
   npx -y wrangler@4.169.0 kv key put "maquette:<email>:<name>.glb" --path ./<name>.glb --binding CLIENT_DATA --remote
   ```

## Limits

- Workers AI has a daily free allocation; past it the assistant answers with an error until the next day.
- 25 MiB per maquette (KV value limit).
- The project sheet is stored in Cloudflare KV, not in Odoo: it is a preparation aid, not a business record.
