/* Interfaccia vocale di Jarvis.
 * Voce IT nativa del browser: SpeechSynthesis (parla) + SpeechRecognition (ascolta).
 * Comanda il modulo di automazione tramite il ponte HTTP locale (server.py).
 */

const orb = document.getElementById("orb");
const subtitle = document.getElementById("subtitle");
const micBtn = document.getElementById("micBtn");
const testBtn = document.getElementById("testBtn");
const stopBtn = document.getElementById("stopBtn");
const sendBtn = document.getElementById("sendBtn");
const cmdInput = document.getElementById("cmdInput");
const logEl = document.getElementById("log");
const dot = document.getElementById("dot");
const statusText = document.getElementById("statusText");

/* ---------------- Voce: sintesi (Jarvis parla) ---------------- */
let itVoice = null;
function pickItalianVoice() {
  itVoice = Persona.scegliVoce(speechSynthesis.getVoices());
}
pickItalianVoice();
if (typeof speechSynthesis !== "undefined") {
  speechSynthesis.onvoiceschanged = pickItalianVoice;
}

// Sintesi del sistema, tunata per il timbro Jarvis (più lento e grave).
function sintetizza(testo) {
  if (!("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(testo);
  u.lang = "it-IT";
  if (itVoice) u.voice = itVoice;
  u.rate = Persona.TUNING.rate;
  u.pitch = Persona.TUNING.pitch;
  u.onstart = () => setState("speaking");
  u.onend = () => setState("idle");
  speechSynthesis.speak(u);
}

/* Parla in carattere. Se `chiave` ha un clip pre-renderizzato in voice/,
 * riproduce quello (timbro premium); altrimenti usa la sintesi del sistema.
 * `testoLibero` è per contenuti dinamici senza clip (es. output di comando). */
function parlaPersona(chiave, testoLibero) {
  const testo = testoLibero || Persona.frase(chiave);
  if (!chiave) { sintetizza(testo); return; }
  // Prova il clip pre-renderizzato; se manca, ripiega sulla sintesi UNA volta sola.
  let ripiegato = false;
  const ripiega = () => { if (!ripiegato) { ripiegato = true; sintetizza(testo); } };
  const audio = new Audio(`voice/${chiave}.mp3`);
  audio.onplay = () => setState("speaking");
  audio.onended = () => setState("idle");
  audio.onerror = ripiega;              // nessun clip: sintesi di sistema
  audio.play().catch(ripiega);
}

/* ---------------- Voce: riconoscimento (Jarvis ascolta) ---------------- */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null, listening = false;
if (SR) {
  recognition = new SR();
  recognition.lang = "it-IT";
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.onresult = (e) => {
    const testo = Array.from(e.results).map(r => r[0].transcript).join("");
    subtitle.textContent = "“" + testo + "”";
    if (e.results[e.results.length - 1].isFinal) eseguiComando(testo.trim());
  };
  recognition.onend = () => { listening = false; micBtn.classList.remove("on"); if (orb.classList.contains("listening")) setState("idle"); };
  recognition.onerror = (e) => { subtitle.textContent = "Riconoscimento non disponibile (" + e.error + ")."; setState("idle"); };
} else {
  micBtn.disabled = true;
  micBtn.textContent = "🎙️ Voce non supportata";
}

micBtn.addEventListener("click", () => {
  if (!recognition) return;
  if (listening) { recognition.stop(); return; }
  listening = true; micBtn.classList.add("on"); setState("listening");
  subtitle.textContent = Persona.frase("ascolto");
  recognition.start();
});

/* ---------------- Stato visivo dell'orbe ---------------- */
function setState(s) {
  orb.classList.remove("listening", "speaking", "busy");
  if (s !== "idle") orb.classList.add(s);
}

/* ---------------- Ponte verso il backend ---------------- */
/* Il token che rende Jarvis tuo: arriva nell'URL (?k=...), lo teniamo in
 * memoria e lo togliamo subito dalla barra degli indirizzi. */
const TOKEN = new URLSearchParams(location.search).get("k") || "";
if (TOKEN) history.replaceState(null, "", location.pathname);

async function api(path, opts = {}) {
  opts.headers = Object.assign({}, opts.headers, { "X-Jarvis-Token": TOKEN });
  const r = await fetch(path, opts);
  return r.json();
}

async function eseguiComando(comando) {
  if (!comando) return;
  setState("busy");
  subtitle.textContent = "Eseguo: " + comando;
  try {
    const res = await api("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: comando }),
    });
    interpretaRisultato(res);
  } catch (err) {
    subtitle.textContent = "Errore di connessione al backend.";
    parlaPersona("offline");
    setState("idle");
  }
  aggiornaLog();
  aggiornaStato();
}

function interpretaRisultato(res) {
  if (res.error) { subtitle.textContent = res.error; parlaPersona("errore"); setState("idle"); return; }
  if (!res.executed) {
    if (res.risk === "CATASTROPHIC") {
      subtitle.textContent = "⛔ Operazione irreversibile: va confermata dal terminale.";
      parlaPersona("catastrofico");
    } else if (res.note && res.note.toLowerCase().includes("kill switch")) {
      subtitle.textContent = "⏹ Sono fermato. Riattivami per operare."; parlaPersona("fermato");
    } else {
      subtitle.textContent = "Non eseguito: " + (res.note || ""); parlaPersona("non_eseguito");
    }
    setState("idle"); return;
  }
  const ok = res.exit_code === 0;
  const out = (res.stdout || res.stderr || "").trim();
  subtitle.textContent = (ok ? "✓ " : "✗ ") + res.command + (out ? "\n" + out : "");
  parlaPersona(ok ? "successo" : "errore");
  setState("idle");
}

/* ---------------- Stop / start ---------------- */
stopBtn.addEventListener("click", async () => {
  const armed = stopBtn.classList.contains("armed");
  await api(armed ? "/api/start" : "/api/stop", { method: "POST" });
  aggiornaStato();
  parlaPersona(armed ? "ripresa" : "in_pausa");
});

/* ---------------- Input testuale ---------------- */
function inviaTesto() { const v = cmdInput.value.trim(); if (v) { cmdInput.value = ""; eseguiComando(v); } }
sendBtn.addEventListener("click", inviaTesto);
cmdInput.addEventListener("keydown", (e) => { if (e.key === "Enter") inviaTesto(); });

testBtn.addEventListener("click", () => parlaPersona("prova"));

/* ---------------- Aggiornamento pannello ---------------- */
async function aggiornaStato() {
  try {
    const s = await api("/api/status");
    const armed = s.stopped;
    dot.classList.toggle("armed", armed);
    stopBtn.classList.toggle("armed", armed);
    stopBtn.textContent = armed ? "▶ Riavvia Jarvis" : "⏹ Ferma Jarvis";
    statusText.textContent = armed ? ("fermato — " + (s.reason || "")) : ("operativo — autonomia: " + s.autonomy);
  } catch (_) { statusText.textContent = "backend non raggiungibile"; }
}

async function aggiornaLog() {
  try {
    const { entries } = await api("/api/log");
    logEl.innerHTML = "";
    entries.slice().reverse().forEach(e => {
      const line = document.createElement("div");
      line.className = "line";
      const t = (e.iso || "").split("T")[1] || "";
      const risk = e.risk && e.risk !== "-" ? `<span class="badge ${e.risk}">${e.risk}</span>` : "";
      line.innerHTML = `<span class="t">${t}</span>${risk}<span class="cmd">${e.event}: ${e.command || e.note || ""}</span>`;
      logEl.appendChild(line);
    });
  } catch (_) {}
}

/* avvio */
aggiornaStato();
aggiornaLog();
setInterval(aggiornaStato, 4000);
// All'avvio: se c'e' il clip premium voice/avvio.mp3 lo riproduce, altrimenti
// sintetizza il saluto in base all'ora.
window.addEventListener("load", () => { setTimeout(() => parlaPersona("avvio", Persona.saluto()), 400); });
