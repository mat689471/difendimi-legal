"""Agente Jarvis: orchestra config, esecutore, audit e kill switch.

Espone un'interfaccia semplice: dai a Jarvis una lista di comandi (un
"piano") e lui li esegue in autonomia, fermandosi solo dove serve.
Questo modulo e' pensato per essere richiamato dalla CLI o, in futuro,
dall'interfaccia vocale in italiano.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Manca PyYAML. Installa con: pip install -r jarvis/requirements.txt") from exc

from .core import AuditLog, Executor, KillSwitch, Result


DEFAULTS = {
    "autonomy": "auto",
    "guard_catastrophic": True,
    "allow_sudo": True,
    "dry_run": False,
    "timeout": 600,
    "audit_path": "jarvis/logs/audit.jsonl",
    "stop_sentinel": "jarvis/logs/STOP",
}


def _cli_confirmer(command: str, reason: str) -> bool:
    print(f"\n  Jarvis chiede conferma -> {reason}")
    print(f"    comando: {command}")
    answer = input("    Confermi? [s/N] ").strip().lower()
    return answer in ("s", "si", "sì", "y", "yes")


def load_config(config_path: str = "jarvis/config.yaml") -> dict:
    """Carica e valida la config, riempiendo i default. Fonte unica di verita'
    per i percorsi (audit, kill switch): la usano sia l'agente sia la CLI."""
    cfg = dict(DEFAULTS)
    p = Path(config_path)
    if p.exists():
        loaded = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        cfg.update({k: v for k, v in loaded.items() if v is not None})

    # Validazione: un typo nella config non deve passare in silenzio.
    if cfg["autonomy"] not in ("auto", "confirm"):
        raise ValueError(
            f"config non valida: autonomy='{cfg['autonomy']}' "
            "(valori ammessi: 'auto', 'confirm')"
        )
    return cfg


@dataclass
class Jarvis:
    executor: Executor
    audit: AuditLog
    killswitch: KillSwitch

    @classmethod
    def from_config(cls, config_path: str = "jarvis/config.yaml", confirmer=_cli_confirmer) -> "Jarvis":
        cfg = load_config(config_path)

        audit = AuditLog(cfg["audit_path"])
        killswitch = KillSwitch(cfg["stop_sentinel"])
        executor = Executor(
            audit=audit,
            killswitch=killswitch,
            confirmer=confirmer,
            autonomy=cfg["autonomy"],
            guard_catastrophic=bool(cfg["guard_catastrophic"]),
            allow_sudo=bool(cfg["allow_sudo"]),
            dry_run=bool(cfg["dry_run"]),
            timeout=int(cfg["timeout"]),
        )
        audit.record("startup", config=cfg)
        return cls(executor=executor, audit=audit, killswitch=killswitch)

    def execute_plan(self, commands: list[str]) -> list[Result]:
        """Esegue una sequenza di comandi. Si ferma se il kill switch scatta."""
        results: list[Result] = []
        for command in commands:
            if self.killswitch.is_engaged():
                print(f"  ⏹ Fermato: {self.killswitch.reason()}")
                break
            result = self.executor.run(command)
            results.append(result)
            self._print_result(result)
        return results

    @staticmethod
    def _print_result(r: Result) -> None:
        if not r.executed:
            print(f"  ✗ [{r.risk}] {r.command}  -> {r.note}")
            return
        status = "✓" if r.exit_code == 0 else f"✗(exit {r.exit_code})"
        print(f"  {status} [{r.risk}] {r.command}")
        if r.stdout.strip():
            print("    " + r.stdout.strip().replace("\n", "\n    "))
        if r.stderr.strip():
            print("    [stderr] " + r.stderr.strip().replace("\n", "\n    "))
