import { test, before } from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";

const TEAM = "aspar.cloudflareaccess.com";
const AUD = "test-aud-tag";
let sign;
let jwk;

before(async () => {
  const { publicKey, privateKey } = await crypto.subtle.generateKey(
    { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" },
    true,
    ["sign", "verify"],
  );
  jwk = { ...(await crypto.subtle.exportKey("jwk", publicKey)), kid: "k1" };
  sign = async (email) => {
    const enc = (o) => Buffer.from(JSON.stringify(o)).toString("base64url");
    const nowS = Math.floor(Date.now() / 1000);
    const input = `${enc({ alg: "RS256", kid: "k1" })}.${enc({ aud: [AUD], iss: `https://${TEAM}`, exp: nowS + 600, email })}`;
    const sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", privateKey, new TextEncoder().encode(input));
    return `${input}.${Buffer.from(sig).toString("base64url")}`;
  };
  globalThis.fetch = async (url) => {
    if (String(url) === `https://${TEAM}/cdn-cgi/access/certs`) return Response.json({ keys: [jwk] });
    throw new Error(`unexpected fetch ${url}`);
  };
});

function memoryKv(initial = {}) {
  const store = new Map(Object.entries(initial));
  return {
    async get(key, type) {
      if (!store.has(key)) return null;
      const v = store.get(key);
      if (type === "json") return JSON.parse(v);
      if (type === "stream") return new Blob([v]).stream();
      return v;
    },
    async put(key, value) { store.set(key, value); },
    async list({ prefix }) {
      return { keys: [...store.keys()].filter((k) => k.startsWith(prefix)).map((name) => ({ name })), list_complete: true };
    },
  };
}

function makeEnv(overrides = {}) {
  const calls = [];
  return {
    calls,
    env: {
      ACCESS_TEAM_DOMAIN: TEAM,
      ACCESS_AUD: AUD,
      AI_MODEL: "@cf/test/model",
      CLIENT_PORTAL_URL: "https://client.aspar.group",
      ASSETS: { fetch: async () => new Response("<html>ui</html>", { headers: { "Content-Type": "text/html" } }) },
      AI: { run: async (model, input) => { calls.push({ model, input }); return { response: "Réponse de test" }; } },
      CLIENT_DATA: memoryKv({
        "maquette:a@example.com:centre.glb": "GLB-A",
        "maquette:b@example.com:secret.glb": "GLB-B",
      }),
      ...overrides,
    },
  };
}

async function call(env, path, { email, method = "GET", body } = {}) {
  const headers = {};
  if (email) headers["Cf-Access-Jwt-Assertion"] = await sign(email);
  if (body !== undefined) headers["Content-Type"] = "application/json";
  return worker.fetch(new Request(`https://agent.aspar.group${path}`, { method, headers, body }), env);
}

test("without Access configuration nothing is served", async () => {
  const { env } = makeEnv({ ACCESS_AUD: "" });
  const res = await call(env, "/", { email: "a@example.com" });
  assert.equal(res.status, 503);
});

test("without a token nothing is served, UI included", async () => {
  const { env } = makeEnv();
  assert.equal((await call(env, "/")).status, 401);
  assert.equal((await call(env, "/api/me")).status, 401);
});

test("a forged identity header without a valid token is refused", async () => {
  const { env } = makeEnv();
  const res = await worker.fetch(
    new Request("https://agent.aspar.group/api/me", { headers: { "Cf-Access-Authenticated-User-Email": "a@example.com", "Cf-Access-Jwt-Assertion": "x.y.z" } }),
    env,
  );
  assert.equal(res.status, 403);
});

test("the UI is served with security headers once authenticated", async () => {
  const { env } = makeEnv();
  const res = await call(env, "/", { email: "a@example.com" });
  assert.equal(res.status, 200);
  assert.match(res.headers.get("Content-Security-Policy"), /frame-ancestors 'none'/);
  assert.equal(res.headers.get("X-Frame-Options"), "DENY");
});

test("a client only sees and opens their own maquettes", async () => {
  const { env } = makeEnv();
  const list = await (await call(env, "/api/maquettes", { email: "A@example.com" })).json();
  assert.deepEqual(list.maquettes, ["centre.glb"]);
  const own = await call(env, "/api/maquettes/centre.glb", { email: "a@example.com" });
  assert.equal(own.status, 200);
  assert.equal(own.headers.get("Content-Type"), "model/gltf-binary");
  assert.equal(await own.text(), "GLB-A");
  assert.equal((await call(env, "/api/maquettes/secret.glb", { email: "a@example.com" })).status, 404);
  assert.equal((await call(env, "/api/maquettes/..%2Fb%40example.com%3Asecret.glb", { email: "a@example.com" })).status, 400);
});

test("the project sheet is stored per client and validated", async () => {
  const { env } = makeEnv();
  const saved = await call(env, "/api/projet", { email: "a@example.com", method: "PUT", body: JSON.stringify({ nom: "Café", surface_m2: "80" }) });
  assert.equal(saved.status, 200);
  assert.deepEqual(await (await call(env, "/api/projet", { email: "a@example.com" })).json(), { nom: "Café", surface_m2: 80 });
  assert.deepEqual(await (await call(env, "/api/projet", { email: "b@example.com" })).json(), {});
  const bad = await call(env, "/api/projet", { email: "a@example.com", method: "PUT", body: JSON.stringify({ surface_m2: -1 }) });
  assert.equal(bad.status, 422);
  const huge = await call(env, "/api/projet", { email: "a@example.com", method: "PUT", body: JSON.stringify({ remarques: "x".repeat(20000) }) });
  assert.equal(huge.status, 413);
});

test("chat answers with the client's own project as context", async () => {
  const { env, calls } = makeEnv();
  await call(env, "/api/projet", { email: "a@example.com", method: "PUT", body: JSON.stringify({ nom: "Café IA" }) });
  const res = await call(env, "/api/chat", {
    email: "a@example.com",
    method: "POST",
    body: JSON.stringify({ messages: [{ role: "user", content: "Bonjour" }] }),
  });
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { reply: "Réponse de test" });
  assert.equal(calls[0].model, "@cf/test/model");
  assert.match(calls[0].input.messages[0].content, /Café IA/);
  assert.equal(calls[0].input.messages.at(-1).content, "Bonjour");
});

test("chat refuses a conversation that does not end with the client", async () => {
  const { env } = makeEnv();
  const res = await call(env, "/api/chat", {
    email: "a@example.com",
    method: "POST",
    body: JSON.stringify({ messages: [{ role: "assistant", content: "x" }] }),
  });
  assert.equal(res.status, 400);
});
