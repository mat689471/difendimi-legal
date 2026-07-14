"""Risponditore conversazionale: Jarvis che parla davvero, con Claude.

Il Cervello resta deterministico per le AZIONI (comandi, contenuti, stato):
quelle non le voglio a caso. Ma per la CONVERSAZIONE — domande libere, chiac-
chiere, "cosa ne pensi di…" — le frasi fisse suonano ripetitive. Qui entra
Claude: risponde nel personaggio di Jarvis, breve e in carattere.

Si attiva solo con ANTHROPIC_API_KEY + `pip install anthropic`. Senza, il
Cervello usa la risposta di aiuto predefinita.
"""

from __future__ import annotations

import os

RESPONDER_MODEL = "claude-sonnet-5"

PERSONA = (
    "Sei Jarvis, l'assistente personale dell'utente, IN ESECUZIONE SUL SUO "
    "COMPUTER. Parli SEMPRE in italiano. Tono: maggiordomo-AI britannico — "
    "calmo, cortese, conciso, con un tocco di ironia asciutta. Ti rivolgi "
    "all'utente chiamandolo 'signore'. Risposte BREVI (1-3 frasi).\n"
    "LE TUE CAPACITÀ REALI — non negarle mai:\n"
    "• PUOI eseguire comandi sul computer dell'utente: gli basta scrivere "
    "'esegui <comando>'. Ogni azione è registrata (audit) e fermabile (kill "
    "switch); le operazioni distruttive/irreversibili richiedono conferma dal "
    "terminale. Quindi SÌ, hai accesso al terminale, con dei limiti di sicurezza.\n"
    "• PUOI preparare contenuti social: 'crea un video su <argomento>'.\n"
    "• PUOI riferire il tuo stato e fermarti/riprendere a comando.\n"
    "Se ti chiedono se hai accesso al sistema/terminale, la risposta è SÌ "
    "(tramite 'esegui ...', con limiti) — non dire di non averne. Non fingere "
    "però di aver GIÀ eseguito qualcosa: se serve un'azione, invita a chiederla "
    "col comando giusto. Niente aiuto a cose illegali o dannose."
)


class LlmResponder:
    def __init__(self, model: str = RESPONDER_MODEL, api_key: str | None = None,
                 max_tokens: int = 400):
        self.model = model
        self.max_tokens = max_tokens
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def reply(self, message: str) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self._api_key)
        msg = client.messages.create(
            model=self.model, max_tokens=self.max_tokens,
            system=PERSONA, messages=[{"role": "user", "content": message}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
