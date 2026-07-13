"""Esecutore di comandi con audit, kill switch e livelli di autonomia.

E' il cuore del modulo "automazione di sistema". Ogni comando passa da qui:
  1. controllo kill switch
  2. classificazione del rischio (safety.py)
  3. decisione in base al livello di autonomia
  4. esecuzione + registrazione nel log di audit
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Callable

from .audit import AuditLog
from .killswitch import KillSwitch
from .safety import Risk, classify


@dataclass
class Result:
    command: str
    executed: bool
    exit_code: int | None
    stdout: str
    stderr: str
    risk: str
    note: str


# Un "confirmer" e' una funzione che riceve comando+motivo e ritorna True/False.
# In CLI e' un input(); via voce potrebbe essere un "confermi?" parlato.
Confirmer = Callable[[str, str], bool]


class Executor:
    def __init__(
        self,
        audit: AuditLog,
        killswitch: KillSwitch,
        confirmer: Confirmer,
        *,
        autonomy: str = "auto",           # "auto" (log+stop) | "confirm" (chiede sempre l'irreversibile)
        guard_catastrophic: bool = True,  # freno d'emergenza sulle operazioni irreversibili
        allow_sudo: bool = True,
        dry_run: bool = False,
        timeout: int = 600,
    ):
        self.audit = audit
        self.killswitch = killswitch
        self.confirmer = confirmer
        self.autonomy = autonomy
        self.guard_catastrophic = guard_catastrophic
        self.allow_sudo = allow_sudo
        self.dry_run = dry_run
        self.timeout = timeout

    def run(self, command: str) -> Result:
        verdict = classify(command)

        # 1. Kill switch: se armato, non si esegue nulla.
        if self.killswitch.is_engaged():
            note = f"BLOCCATO dal kill switch ({self.killswitch.reason()})"
            self.audit.record("blocked", command=command, risk=verdict.risk.name, note=note)
            return Result(command, False, None, "", "", verdict.risk.name, note)

        # 2. sudo disabilitato da config: blocca a QUALSIASI livello di rischio
        #    (anche prima del freno catastrofico), con match su parola intera
        #    per non colpire "pseudo" e simili.
        if not self.allow_sudo and re.search(r"\bsudo\b", command):
            note = "sudo disabilitato nella configurazione"
            self.audit.record("denied", command=command, risk=verdict.risk.name, note=note)
            return Result(command, False, None, "", "", verdict.risk.name, note)

        # 3. Freno d'emergenza sulle operazioni catastrofiche.
        if verdict.risk == Risk.CATASTROPHIC and self.guard_catastrophic:
            self.audit.record("confirm_requested", command=command,
                              risk=verdict.risk.name, reason=verdict.reason)
            approved = self.confirmer(command, f"OPERAZIONE IRREVERSIBILE: {verdict.reason}")
            if not approved:
                note = "conferma negata (operazione catastrofica)"
                self.audit.record("aborted", command=command, risk=verdict.risk.name, note=note)
                return Result(command, False, None, "", "", verdict.risk.name, note)

        # 4. In modalita' "confirm", anche le operazioni elevate chiedono conferma.
        if self.autonomy == "confirm" and verdict.risk >= Risk.ELEVATED:
            approved = self.confirmer(command, verdict.reason)
            if not approved:
                note = "conferma negata"
                self.audit.record("aborted", command=command, risk=verdict.risk.name, note=note)
                return Result(command, False, None, "", "", verdict.risk.name, note)

        # 5. Esecuzione (o dry-run).
        if self.dry_run:
            note = "dry-run: comando non eseguito"
            self.audit.record("dry_run", command=command, risk=verdict.risk.name, reason=verdict.reason)
            return Result(command, False, None, "", "", verdict.risk.name, note)

        self.audit.record("executing", command=command, risk=verdict.risk.name, reason=verdict.reason)
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=self.timeout
            )
            self.audit.record("executed", command=command, risk=verdict.risk.name,
                              exit_code=proc.returncode)
            return Result(command, True, proc.returncode, proc.stdout, proc.stderr,
                          verdict.risk.name, verdict.reason)
        except subprocess.TimeoutExpired:
            note = f"timeout dopo {self.timeout}s"
            self.audit.record("timeout", command=command, risk=verdict.risk.name, note=note)
            return Result(command, False, None, "", note, verdict.risk.name, note)
        except Exception as exc:  # noqa: BLE001 - vogliamo loggare qualsiasi errore
            note = f"errore: {exc}"
            self.audit.record("error", command=command, risk=verdict.risk.name, note=note)
            return Result(command, False, None, "", note, verdict.risk.name, note)
