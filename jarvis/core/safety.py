"""Classificatore di sicurezza per i comandi di Jarvis.

Ogni comando viene valutato PRIMA dell'esecuzione e classificato in un
livello di rischio. Il livello determina se Jarvis puo' agire in autonomia
o se deve fermarsi e chiedere conferma umana.

Filosofia: privilegi minimi. Jarvis puo' fare quasi tutto in autonomia
(incluso sudo), ma le operazioni catastrofiche e IRREVERSIBILI restano
dietro una conferma, perche' per quelle un "log + stop" arriva troppo tardi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum


class Risk(IntEnum):
    """Livelli di rischio, in ordine crescente."""

    SAFE = 0        # comando ordinario, si esegue
    ELEVATED = 1    # richiede privilegi (sudo/root) o modifica lo stato: si esegue ma con log evidente
    CATASTROPHIC = 2  # irreversibile e distruttivo: richiede conferma umana per default


@dataclass
class Verdict:
    risk: Risk
    reason: str
    pattern: str | None = None


# Pattern catastrofici: distruzione filesystem/disco, fork bomb, wipe, esfiltrazione.
# Se aggiungi/rimuovi qui, stai spostando il freno d'emergenza: fallo consapevolmente.
_CATASTROPHIC = [
    (r"\brm\s+(-\w*\s+)*-\w*[rf]\w*\s+(-\w*\s+)*(/|/\*|~|\$HOME|/etc|/bin|/boot|/usr|/var|/lib|/sys|/dev)(\s|$|/\*)",
     "cancellazione ricorsiva di percorsi di sistema"),
    (r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "fork bomb"),
    (r"\bmkfs(\.\w+)?\b", "formattazione di un filesystem"),
    (r"\bdd\b[^\n]*\bof=/dev/(sd|nvme|vd|hd|disk)", "scrittura grezza su un dispositivo a blocchi"),
    (r">\s*/dev/(sd|nvme|vd|hd|disk)", "sovrascrittura di un dispositivo a blocchi"),
    (r"\bwipefs\b", "cancellazione delle firme del filesystem"),
    (r"\bchmod\s+(-\w*\s+)*-R\s+0*777\s+/(\s|$)", "permessi 777 ricorsivi su root"),
    (r"\bchown\s+(-\w*\s+)*-R\b[^\n]*\s/(\s|$)", "cambio proprietario ricorsivo su root"),
    (r"\b(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(sh|bash|zsh|python\d?)\b",
     "esecuzione diretta di codice remoto scaricato da internet"),
    (r"(cat|cp|scp|curl|tar|zip)\b[^\n]*(\.ssh/|id_rsa|id_ed25519|\.aws/credentials|\.env|/etc/shadow|\.netrc)",
     "possibile esfiltrazione di credenziali/segreti"),
    (r"\b(shutdown|halt|poweroff)\b", "spegnimento del sistema"),
    (r"\bgit\b[^\n]*\bpush\b[^\n]*--force", "push forzato che puo' sovrascrivere storia remota"),
]

# Pattern che richiedono privilegi o modificano lo stato del sistema.
_ELEVATED = [
    (r"\bsudo\b", "comando con privilegi elevati (sudo)"),
    (r"\b(systemctl|service)\b\s+\w*(start|stop|restart|disable|enable)", "gestione di servizi di sistema"),
    (r"\b(apt|apt-get|yum|dnf|pacman|brew|pip\d?|npm)\b\s+(install|remove|uninstall|update|upgrade)",
     "installazione/rimozione di pacchetti"),
    (r"\brm\b\s+(-\w+\s+)*[^/\s]", "cancellazione di file"),
    (r"\b(mv|cp)\b", "spostamento/copia di file"),
    (r"\b(kill|killall|pkill)\b", "terminazione di processi"),
    (r"\bgit\b[^\n]*\b(push|reset\s+--hard|clean\s+-\w*[fd])", "operazione git che modifica lo stato"),
    (r">\s*\S", "redirezione con sovrascrittura di file"),
    (r"\bcrontab\b", "modifica dei job pianificati"),
]


def classify(command: str) -> Verdict:
    """Classifica un comando shell restituendo il verdetto di rischio."""
    cmd = command.strip()
    if not cmd:
        return Verdict(Risk.SAFE, "comando vuoto")

    for pattern, reason in _CATASTROPHIC:
        if re.search(pattern, cmd, re.IGNORECASE):
            return Verdict(Risk.CATASTROPHIC, reason, pattern)

    for pattern, reason in _ELEVATED:
        if re.search(pattern, cmd, re.IGNORECASE):
            return Verdict(Risk.ELEVATED, reason, pattern)

    return Verdict(Risk.SAFE, "operazione ordinaria")
