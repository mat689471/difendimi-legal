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

## Interfaccia + voce italiana

Il "volto" di Jarvis: un'interfaccia web con orbe animato, **voce italiana**
(sintesi + riconoscimento vocali nativi del browser, `it-IT`) e un pannello
che mostra in tempo reale la scatola nera. Comanda lo stesso motore di
automazione, quindi vale lo stesso modello di sicurezza.

```bash
python jarvis/server.py        # avvia il ponte locale su http://127.0.0.1:8787
# apri quell'indirizzo in Chrome/Edge (per la voce serve un browser con Web Speech API)
```

- 🎙️ **Parla**: detta un comando a voce, Jarvis lo esegue e risponde a voce.
- ⌨️ campo di testo: stesso effetto, scritto.
- ⏹ **Ferma/Riavvia**: il kill switch, dall'interfaccia.

### Personalità vocale (`ui/persona.js`)

Jarvis non legge l'output: risponde **in carattere** — tono da maggiordomo-AI,
composto e deferente, con saluto in base all'ora e frasi variate per non
suonare robotico. Il timbro della sintesi è tunato più grave e lento.

- Come ti chiama: `localStorage.setItem('jarvis_appellativo', 'dottore')` (default `signore`).
- **Voice pack premium (opzionale)**: se metti un file `ui/voice/<chiave>.mp3`
  (es. `successo.mp3`, `catastrofico.mp3`), la UI riproduce quel clip al posto
  della sintesi di sistema. Timbro cinematografico come upgrade drop-in, senza
  toccare il codice.

Sicurezza del ponte web:
- il server ascolta **solo su `127.0.0.1`** (non è esposto in rete);
- via HTTP le operazioni **catastrofiche sono negate**: un pulsante web non
  deve poter formattare un disco. Per quelle serve la conferma da terminale.

## Prossimi moduli

Si agganceranno tutti a questa infrastruttura (audit + kill switch + livelli):
pipeline contenuti (base Remotion già nel repo) e trading
MetaTrader/Fusion Market **in demo** con limiti hard.
