import {
  buildChatMessages,
  isValidMaquetteName,
  maquetteContentType,
  maquettePrefix,
  normalizeEmail,
  projetKey,
  validateProjet,
  verifyAccessJwt,
} from "./lib.js";
import { SYSTEM_PROMPT } from "./prompt.js";

const MAX_PROJET_BODY = 16 * 1024;
const MAX_CHAT_BODY = 64 * 1024;
const JWKS_TTL_MS = 60 * 60 * 1000;

const SECURITY_HEADERS = {
  "Content-Security-Policy": [
    "default-src 'self'",
    // model-viewer compiles a WebAssembly decoder; this allows WebAssembly only, not eval().
    "script-src 'self' 'wasm-unsafe-eval'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "connect-src 'self' data: blob:",
    "worker-src 'self' blob:",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; "),
  "X-Frame-Options": "DENY",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
};

let jwksCache = { keys: null, fetchedAt: 0 };

async function getAccessKeys(teamDomain) {
  if (jwksCache.keys && Date.now() - jwksCache.fetchedAt < JWKS_TTL_MS) return jwksCache.keys;
  const res = await fetch(`https://${teamDomain}/cdn-cgi/access/certs`);
  if (!res.ok) throw new Error(`certs ${res.status}`);
  const { keys } = await res.json();
  jwksCache = { keys: Array.isArray(keys) ? keys : [], fetchedAt: Date.now() };
  return jwksCache.keys;
}

function getCookie(request, name) {
  const cookie = request.headers.get("Cookie") || "";
  for (const part of cookie.split(";")) {
    const [k, ...v] = part.trim().split("=");
    if (k === name) return v.join("=");
  }
  return null;
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function text(message, status) {
  return new Response(message, {
    status,
    headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function withSecurityHeaders(response) {
  const res = new Response(response.body, response);
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) res.headers.set(k, v);
  return res;
}

async function readBody(request, limit) {
  const body = await request.text();
  if (body.length > limit) return { error: text("Requête trop volumineuse.", 413) };
  try {
    return { value: JSON.parse(body) };
  } catch {
    return { error: text("JSON invalide.", 400) };
  }
}

// Fails closed: without a valid Cloudflare Access token, nothing is served.
async function authenticate(request, env) {
  if (!env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD) {
    return { error: text("Service non configuré : la protection d'accès est absente.", 503) };
  }
  const token = request.headers.get("Cf-Access-Jwt-Assertion") || getCookie(request, "CF_Authorization");
  if (!token) return { error: text("Accès refusé.", 401) };
  try {
    const payload = await verifyAccessJwt(token, {
      teamDomain: env.ACCESS_TEAM_DOMAIN,
      aud: env.ACCESS_AUD,
      getKeys: () => getAccessKeys(env.ACCESS_TEAM_DOMAIN),
    });
    const email = normalizeEmail(payload.email);
    return email ? { email } : { error: text("Accès refusé.", 403) };
  } catch {
    return { error: text("Accès refusé.", 403) };
  }
}

async function handleApi(request, env, url, email) {
  const path = url.pathname;
  const method = request.method;

  if (path === "/api/me" && method === "GET") {
    return json({ email, portalUrl: env.CLIENT_PORTAL_URL || "" });
  }

  if (path === "/api/projet") {
    if (method === "GET") {
      return json((await env.CLIENT_DATA.get(projetKey(email), "json")) || {});
    }
    if (method === "PUT") {
      const { value, error } = await readBody(request, MAX_PROJET_BODY);
      if (error) return error;
      const result = validateProjet(value);
      if (!result.ok) return json({ errors: result.errors }, 422);
      await env.CLIENT_DATA.put(projetKey(email), JSON.stringify(result.value));
      return json(result.value);
    }
    return text("Méthode non autorisée.", 405);
  }

  if (path === "/api/maquettes" && method === "GET") {
    const prefix = maquettePrefix(email);
    const names = [];
    let cursor;
    do {
      const page = await env.CLIENT_DATA.list({ prefix, cursor });
      for (const key of page.keys) names.push(key.name.slice(prefix.length));
      cursor = page.list_complete ? undefined : page.cursor;
    } while (cursor);
    return json({ maquettes: names.filter(isValidMaquetteName).sort() });
  }

  if (path.startsWith("/api/maquettes/") && method === "GET") {
    const name = decodeURIComponent(path.slice("/api/maquettes/".length));
    if (!isValidMaquetteName(name)) return text("Nom de maquette invalide.", 400);
    const stream = await env.CLIENT_DATA.get(maquettePrefix(email) + name, "stream");
    if (!stream) return text("Maquette introuvable.", 404);
    return new Response(stream, {
      headers: { "Content-Type": maquetteContentType(name), "Cache-Control": "private, no-store" },
    });
  }

  if (path === "/api/chat" && method === "POST") {
    const { value, error } = await readBody(request, MAX_CHAT_BODY);
    if (error) return error;
    const projet = (await env.CLIENT_DATA.get(projetKey(email), "json")) || {};
    const messages = buildChatMessages(value && value.messages, projet, SYSTEM_PROMPT);
    if (!messages) return text("Le dernier message doit venir du client.", 400);
    const out = await env.AI.run(env.AI_MODEL, { messages, max_tokens: 700, temperature: 0.4 });
    const reply = out?.response ?? out?.choices?.[0]?.message?.content ?? "";
    if (!reply) return json({ error: "L'assistant n'a pas répondu. Réessayez dans un instant." }, 502);
    return json({ reply });
  }

  return text("Introuvable.", 404);
}

export default {
  async fetch(request, env) {
    try {
      const auth = await authenticate(request, env);
      if (auth.error) return withSecurityHeaders(auth.error);
      const url = new URL(request.url);
      const response = url.pathname.startsWith("/api/")
        ? await handleApi(request, env, url, auth.email)
        : await env.ASSETS.fetch(request);
      return withSecurityHeaders(response);
    } catch (err) {
      console.error(err);
      return withSecurityHeaders(json({ error: "Erreur interne." }, 500));
    }
  },
};
