const VIEWS = ["assistant", "projet", "maquette", "compte"];
const history = [];

async function api(path, options = {}) {
  const res = await fetch(path, {
    credentials: "same-origin",
    headers: options.body ? { "Content-Type": "application/json" } : {},
    ...options,
  });
  const type = res.headers.get("Content-Type") || "";
  const data = type.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) {
    const message = (data && (data.error || (data.errors && data.errors.join(" ")))) || data || `Erreur ${res.status}`;
    throw new Error(typeof message === "string" ? message : `Erreur ${res.status}`);
  }
  return data;
}

function showView(name) {
  const view = VIEWS.includes(name) ? name : "assistant";
  for (const v of VIEWS) document.getElementById(`view-${v}`).hidden = v !== view;
  for (const link of document.querySelectorAll(".nav-item")) {
    const active = link.dataset.view === view;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  if (view === "projet") loadProjet();
  if (view === "maquette") loadMaquettes();
}

// --- Assistant ------------------------------------------------------------

function addMessage(role, content) {
  const log = document.getElementById("chat-log");
  const item = document.createElement("div");
  item.className = `msg ${role}`;
  item.textContent = content;
  log.appendChild(item);
  log.scrollTop = log.scrollHeight;
  return item;
}

async function sendMessage(event) {
  event.preventDefault();
  const input = document.getElementById("chat-input");
  const button = document.getElementById("chat-send");
  const content = input.value.trim();
  if (!content) return;
  input.value = "";
  history.push({ role: "user", content });
  addMessage("user", content);
  const pending = addMessage("assistant pending", "…");
  button.disabled = true;
  try {
    const { reply } = await api("/api/chat", { method: "POST", body: JSON.stringify({ messages: history }) });
    history.push({ role: "assistant", content: reply });
    pending.className = "msg assistant";
    pending.textContent = reply;
  } catch (err) {
    history.pop();
    pending.className = "msg error";
    pending.textContent = `Message non envoyé : ${err.message}`;
  } finally {
    button.disabled = false;
    input.focus();
  }
}

// --- Mon projet -------------------------------------------------------------

async function loadProjet() {
  const form = document.getElementById("projet-form");
  const status = document.getElementById("projet-status");
  try {
    const projet = await api("/api/projet");
    for (const el of form.elements) {
      if (el.name) el.value = projet[el.name] ?? "";
    }
    status.textContent = "";
  } catch (err) {
    status.textContent = `Chargement impossible : ${err.message}`;
  }
}

async function saveProjet(event) {
  event.preventDefault();
  const form = event.target;
  const status = document.getElementById("projet-status");
  const data = {};
  for (const el of form.elements) {
    if (el.name && el.value.trim() !== "") data[el.name] = el.value;
  }
  status.textContent = "Enregistrement…";
  try {
    await api("/api/projet", { method: "PUT", body: JSON.stringify(data) });
    status.textContent = "Enregistré.";
  } catch (err) {
    status.textContent = `Non enregistré : ${err.message}`;
  }
}

// --- Ma maquette 3D ---------------------------------------------------------

function showMaquette(name) {
  const viewer = document.getElementById("viewer");
  viewer.src = `/api/maquettes/${encodeURIComponent(name)}`;
  viewer.hidden = false;
}

async function loadMaquettes() {
  const select = document.getElementById("maquette-select");
  const empty = document.getElementById("maquette-empty");
  const viewer = document.getElementById("viewer");
  const current = select.value;
  try {
    const { maquettes } = await api("/api/maquettes");
    select.replaceChildren(...maquettes.map((name) => new Option(name, name)));
    empty.hidden = maquettes.length > 0;
    select.hidden = maquettes.length === 0;
    if (!maquettes.length) {
      viewer.hidden = true;
      viewer.removeAttribute("src");
      return;
    }
    const chosen = maquettes.includes(current) ? current : maquettes[0];
    select.value = chosen;
    showMaquette(chosen);
  } catch (err) {
    empty.hidden = false;
    empty.textContent = `Chargement impossible : ${err.message}`;
  }
}

// --- Démarrage --------------------------------------------------------------

async function init() {
  document.getElementById("chat-form").addEventListener("submit", sendMessage);
  document.getElementById("chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      e.target.form.requestSubmit();
    }
  });
  document.getElementById("projet-form").addEventListener("submit", saveProjet);
  document.getElementById("maquette-refresh").addEventListener("click", loadMaquettes);
  document.getElementById("maquette-select").addEventListener("change", (e) => showMaquette(e.target.value));
  window.addEventListener("hashchange", () => showView(location.hash.slice(1)));

  try {
    const me = await api("/api/me");
    document.getElementById("user-email").textContent = me.email;
    if (me.portalUrl) document.getElementById("portal-link").href = `${me.portalUrl.replace(/\/$/, "")}/my`;
  } catch {
    // The page is only served after authentication; a failure here is shown on the next action.
  }
  showView(location.hash.slice(1));
}

init();
