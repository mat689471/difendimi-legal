"""Pianificatore: da un obiettivo a una sequenza di passi.

Due livelli, dal piu' semplice al piu' potente:

  * KeywordPlanner — deterministico, offline: tratta l'obiettivo come un
    singolo comando per il Cervello. Nessuna dipendenza, funziona sempre.

  * LlmPlanner — QUI vive il vero "ci pensa lui": dato un obiettivo in
    italiano, chiede a Claude di scomporlo in una lista di istruzioni per il
    Cervello, che poi vengono eseguite UNA PER UNA (ognuna con audit, kill
    switch, Guardiano e conferma sulle cose gravi). Richiede:
        pip install anthropic
        variabile d'ambiente ANTHROPIC_API_KEY
    Finche' non le fornisci, resta inattivo — niente magie nascoste.

Anche col planner LLM, Jarvis NON diventa incontrollabile: pianifica, ma
l'esecuzione passa sempre dallo stesso strato di sicurezza, e tu puoi fermarlo.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod

PLANNER_MODEL = "claude-sonnet-5"

_SYSTEM = (
    "Sei il pianificatore di Jarvis, un assistente operativo. Ricevi un "
    "obiettivo in italiano e lo scomponi in una breve lista ordinata di "
    "istruzioni semplici, ognuna eseguibile dal Cervello di Jarvis "
    "(esegui comandi di sistema, prepara contenuti, controlla lo stato). "
    "Rispondi SOLO con un array JSON di stringhe, senza altro testo. "
    "Non proporre passi irreversibili o pericolosi senza che siano espliciti "
    "nell'obiettivo."
)


class Planner(ABC):
    @abstractmethod
    def plan(self, goal: str) -> list[str]:
        ...


class KeywordPlanner(Planner):
    """Nessuna pianificazione: l'obiettivo e' un singolo passo."""

    def plan(self, goal: str) -> list[str]:
        return [goal.strip()] if goal.strip() else []


class LlmPlanner(Planner):
    """Pianificatore basato su Claude. Attivo solo con SDK + API key."""

    def __init__(self, model: str = PLANNER_MODEL, api_key: str | None = None,
                 max_steps: int = 8):
        self.model = model
        self.max_steps = max_steps
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def plan(self, goal: str) -> list[str]:
        if not self._api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY non impostata: il pianificatore LLM è inattivo. "
                "Imposta la chiave (e `pip install anthropic`) per abilitarlo."
            )
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - dipende dall'ambiente
            raise RuntimeError("Manca il pacchetto 'anthropic' (pip install anthropic).") from exc

        client = anthropic.Anthropic(api_key=self._api_key)
        msg = client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=_SYSTEM,
            messages=[{"role": "user", "content": f"Obiettivo: {goal}"}],
        )
        text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
        try:
            steps = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Il pianificatore ha risposto in un formato non valido: {text[:200]}") from exc
        if not isinstance(steps, list):
            raise RuntimeError("Il pianificatore non ha restituito una lista di passi.")
        return [str(s) for s in steps][: self.max_steps]
