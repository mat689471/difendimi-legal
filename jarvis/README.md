# Jarvis — modulo automazione di sistema

Primo mattone di Jarvis: un assistente che può eseguire operazioni sul
computer **in autonomia**, con privilegi elevati quando serve, ma con una
**scatola nera** (audit log) e un **freno d'emergenza** (kill switch).

## Filosofia di sicurezza

Root e autonomia sono potenti ma pericolosi. Qui il compromesso è:
Jarvis agisce da solo su quasi tutto (incluso `sudo`), ma le **operazioni
irreversibili e catastrofiche** — wipe del disco, formattazione, fork bomb,
esfiltrazione di credenziali — restano dietro una conferma. Per quelle un
"log + stop" arriva sempre troppo tardi: quando il log le registra, il
danno è già fatto e non c'è undo.

Il freno è **tuo**: è la riga `guard_catastrophic` in `config.yaml`. Vedi
il codice, lo regoli, lo disattivi se vuoi. Niente è nascosto.

## Livelli di rischio (`core/safety.py`)

| Livello        | Esempi                                   | In modalità `auto`        |
|----------------|------------------------------------------|---------------------------|
| `SAFE`         | `ls`, `df -h`, `git status`              | eseguito                  |
| `ELEVATED`     | `sudo …`, `systemctl`, `rm file`, `apt`  | eseguito + log evidente   |
| `CATASTROPHIC` | `rm -rf /`, `mkfs`, `dd of=/dev/sda`, `curl \| bash` | conferma richiesta |

## Uso

```bash
pip install -r jarvis/requirements.txt

# esegue comandi in autonomia
python -m jarvis.cli run "df -h" "free -m"

# esegue un piano (un comando per riga)
python -m jarvis.cli plan piano.txt

# freno d'emergenza
python -m jarvis.cli stop      # Jarvis si ferma
python -m jarvis.cli start     # riparte
python -m jarvis.cli status

# scatola nera
python -m jarvis.cli log -n 30
```

## Configurazione (`config.yaml`)

- `autonomy`: `auto` (agisce da solo) o `confirm` (chiede anche per le operazioni elevate)
- `guard_catastrophic`: freno d'emergenza sulle operazioni irreversibili
- `allow_sudo`: consenti/blocca i privilegi elevati
- `dry_run`: simula senza eseguire

## Test

```bash
python -m pytest jarvis/tests/ -v
```

## Prossimi moduli

Si agganceranno tutti a questa infrastruttura (audit + kill switch + livelli):
interfaccia + voce italiana, pipeline contenuti (base Remotion già nel repo),
trading MetaTrader/Fusion Market **in demo** con limiti hard.
