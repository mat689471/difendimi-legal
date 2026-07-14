"""Il Cervello di Jarvis — l'unico punto a cui parli.

Finora Jarvis era fatto di moduli separati (sistema, contenuti, trading,
guardiano). Questo e' lo strato che li unisce: gli dai un'istruzione in
italiano, lui capisce l'intento, sceglie la capacita' giusta e agisce —
sempre sotto le regole di sicurezza (audit, kill switch, Guardiano, e la
conferma umana sulle operazioni irreversibili gia' garantita dall'executor).

ONESTA' su cosa e' e cosa non e':
  * E' un router di intenti + esecutore coordinato. Reale, funzionante, tuo.
  * NON e' un'intelligenza che si inventa piani complessi da sola. Il "pianifi-
    catore" qui e' a regole (deterministico). E' predisposto per un planner LLM
    (Claude) piu' avanzato: si attiva quando colleghi una API key — vedi
    `planner.py`. Ma anche allora resta con te al comando sulle cose gravi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..agent import Jarvis
from ..core.safety import classify
from ..guardian import Advisory, Guardian


@dataclass
class Reply:
    intent: str
    text: str
    advisories: list[Advisory] = field(default_factory=list)
    data: dict | None = None


class Brain:
    def __init__(self, jarvis: Jarvis | None = None, guardian: Guardian | None = None,
                 config_path: str = "jarvis/config.yaml", responder=None):
        self.jarvis = jarvis or Jarvis.from_config(config_path)
        self.guardian = guardian or Guardian()
        # risponditore conversazionale (Claude), se disponibile
        if responder is None:
            from .responder import LlmResponder
            r = LlmResponder()
            responder = r if r.available() else None
        self.responder = responder

    # --- comprensione dell'intento --------------------------------------
    def _route(self, message: str) -> tuple[str, str]:
        m = message.strip()
        low = m.lower()

        # fermare / riprendere
        if re.search(r"\b(fermati|ferma|stop|bloccati)\b", low):
            return "stop", ""
        if re.search(r"\b(riprendi|riparti|sveglia|ripartiamo|riattivati)\b", low):
            return "start", ""

        # trading (prima dello stato: "come va il trading" è trading, non stato)
        if re.search(r"\b(trading|mercato|conto|posizion|borsa)\w*", low):
            return "trading", ""

        # stato
        if re.search(r"\b(stato|situazione|come va|come stai|report)\b", low):
            return "status", ""

        # contenuti / video: "crea un video su X", "fai un contenuto su X"
        content_match = re.search(
            r"\b(?:video|contenut\w+|post|reel)\b.*?\b(?:su|di|per|sul|sulla|sui)\b\s+(.+)", low)
        if content_match:
            return "content", content_match.group(1).strip()
        if re.search(r"\b(video|contenut\w+|reel)\b", low):
            return "content", ""

        # comando di sistema: "esegui ...", "lancia ...", "comando ..."
        cmd_match = re.match(r"(?:esegui|lancia|comando|run)\s+(.+)", m, re.IGNORECASE)
        if cmd_match:
            return "system", cmd_match.group(1).strip()

        return "help", ""

    # --- azione ----------------------------------------------------------
    def handle(self, message: str, now=None) -> Reply:
        intent, arg = self._route(message)

        # il Guardiano osserva PRIMA di agire (rischio stimato dall'intento)
        risk = classify(arg).risk.name if intent == "system" else "SAFE"
        advisories = self.guardian.observe(risk=risk, now=now)

        if intent == "stop":
            self.jarvis.killswitch.engage("stop richiesto a voce/testo")
            return Reply(intent, "Mi fermo, signore. Nessuna nuova azione finché non mi riattiva.", advisories)

        if intent == "start":
            self.jarvis.killswitch.disengage()
            return Reply(intent, "Di nuovo operativo, signore.", advisories)

        if intent == "status":
            stopped = self.jarvis.killswitch.is_engaged()
            stato = f"fermo ({self.jarvis.killswitch.reason()})" if stopped else "operativo"
            return Reply(intent, f"Sono {stato}, signore. Autonomia: {self.jarvis.executor.autonomy}.",
                         advisories, data={"stopped": stopped})

        if intent == "trading":
            return Reply(intent,
                         "Il trading è in modalità paper (simulata), signore: nessun denaro reale. "
                         "Per la demo: python -m jarvis.trading. Il live richiede la sua conferma esplicita.",
                         advisories)

        if intent == "content":
            if not arg:
                return Reply(intent,
                             "Su quale argomento preparo il contenuto, signore? Es. «crea un video sui ricorsi per multe».",
                             advisories)
            out = self._make_content(arg)
            return Reply(intent,
                         f"Ho preparato un contenuto su «{arg}», signore. Props e testo social pronti.",
                         advisories, data=out)

        if intent == "system":
            if not arg:
                return Reply(intent, "Quale comando devo eseguire, signore?", advisories)
            result = self.jarvis.executor.run(arg)
            if result.executed:
                out = (result.stdout or result.stderr or "").strip()
                testo = f"Eseguito, signore." + (f"\n{out}" if out else "")
            else:
                testo = f"Non eseguito: {result.note}"
            return Reply(intent, testo, advisories,
                         data={"executed": result.executed, "risk": result.risk})

        # conversazione libera: se c'è Claude, Jarvis risponde davvero
        if self.responder is not None:
            try:
                return Reply("chat", self.responder.reply(message), advisories)
            except Exception:  # noqa: BLE001 - se l'LLM fallisce, ripiega sull'aiuto
                pass

        # aiuto predefinito (senza LLM)
        return Reply("help",
                     "Sono Jarvis, signore. Posso: eseguire comandi ('esegui ...'), "
                     "preparare contenuti ('crea un video su ...'), informarla sul trading, "
                     "dirle il mio stato, e fermarmi/riprendere a suo comando.",
                     advisories)

    def plan_and_do(self, goal: str, planner=None, now=None) -> list[Reply]:
        """Prende un obiettivo, lo fa scomporre in passi dal pianificatore, e li
        esegue uno per uno — fermandosi se scatta il kill switch. E' la versione
        onesta di 'ci pensa lui': autonomo nei passi, ma sotto le regole di
        sicurezza, e interrompibile in qualsiasi momento."""
        from .planner import KeywordPlanner
        planner = planner or KeywordPlanner()
        replies: list[Reply] = []
        for step in planner.plan(goal):
            if self.jarvis.killswitch.is_engaged():
                replies.append(Reply("stop", "Mi sono fermato, signore: kill switch attivo.", []))
                break
            replies.append(self.handle(step, now=now))
        return replies

    def _make_content(self, topic: str) -> dict:
        from ..content import prepare
        brief = {
            "name": topic,
            "title": topic.capitalize(),
            "hook": f"{topic.capitalize()}?",
            "hashtags": "#difendimi #" + re.sub(r"[^a-z0-9]+", "", topic.lower()),
        }
        out = prepare(brief)
        return {"slug": out.slug, "props": str(out.props_path), "social": str(out.social_path)}
