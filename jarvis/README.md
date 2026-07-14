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
- **Voice pack premium (incluso)**: in `ui/voice/` ci sono 10 clip generati
  con una voce maschile italiana (avvio, successo, errore, catastrofico,
  fermato, ripresa, in pausa, offline, non eseguito, prova). La UI li riproduce
  al posto della sintesi di sistema; i contenuti dinamici (output dei comandi)
  restano in sintesi. Per rigenerarli con un'altra voce basta sostituire i file
  `ui/voice/<chiave>.mp3` — nessuna modifica al codice.

Sicurezza del ponte web — **Jarvis risponde solo a te**:
- il server ascolta **solo su `127.0.0.1`** (non è esposto in rete);
- ogni chiamata richiede il **tuo token segreto**, generato alla prima
  esecuzione e stampato nel terminale come parte dell'URL. Solo chi ha quel
  token (tu) può aprire l'interfaccia e dare comandi;
- controllo dell'header `Host` contro il **DNS-rebinding** (un sito malevolo
  che prova a comandare Jarvis dal tuo browser);
- via HTTP le operazioni **catastrofiche sono negate**: un pulsante web non
  deve poter formattare un disco. Per quelle serve la conferma da terminale.

## Pipeline contenuti

Genera video social a partire da un **brief** (JSON). Il contenuto del video
Remotion è ora guidato dai dati: cambi il brief, cambia il video.

```bash
python -m jarvis.content jarvis/content/brief.example.json            # prepara e renderizza
python -m jarvis.content jarvis/content/brief.example.json --no-render # solo props + social
```

La pipeline:
1. converte il brief nei props del video (`remotion/props/<slug>.json`);
2. renderizza **tramite Jarvis** (quindi con audit log e kill switch);
3. genera il **pacchetto social** (descrizione + hashtag) in
   `remotion/out/<slug>.social.txt`.

La **pubblicazione** su YouTube/social non è automatica: richiede le tue
credenziali e la tua approvazione (l'automazione del posting viola le ToS di
molte piattaforme). La pipeline prepara tutto; l'ultimo clic è tuo.

## Trading (demo-first)

Modulo `jarvis/trading`: opera con **limiti hard** e sotto lo stesso audit log
e kill switch del resto di Jarvis. Regola d'oro sulla progressione:

`paper` (simulato) → `demo` (conto demo reale Fusion Market) → `live` (soldi veri).

```bash
python -m jarvis.trading   # demo: TrendRsi + SL/TP + sizing sul rischio, 0 euro reali
```

Sicurezza:
- **Limiti hard** (in `trading/config.yaml`): volume per ordine, posizioni
  aperte, volume totale, **perdita giornaliera** oltre cui Jarvis smette di
  aprire. Nessun ordine passa senza l'ok del risk manager.
- **`live` = doppio interruttore**: serve `mode: live` **e** `allow_live: true`,
  **e** la conferma manuale di *ogni* ordine. Di default entrambi off.
- Una **strategia non esegue**: propone segnali; l'esecuzione (con i limiti)
  resta al motore. Una strategia sbagliata non può sforare i limiti hard.

Strumenti da trading serio:
- **Stop-loss / take-profit** sugli ordini: `engine.update_market(symbol, price)`
  fa scorrere il prezzo e chiude in automatico le posizioni che li toccano,
  registrando P&L e audit (così anche lo stop rientra nel conteggio della
  perdita giornaliera).
- **Position sizing sul rischio** (`size_for_risk`): dimensiona il volume perché
  la perdita allo stop sia una piccola % del conto — non rischiare mai troppo.
- **Strategie**: `SmaCrossover` (didattica), `RsiReversion` (mean-reversion),
  `TrendRsi` (pullback filtrato dal trend, default più conservativo). Il
  risultato dipende **sempre** dalle condizioni di mercato.

Collegamento reale **MT5/Fusion Market** (`mt5_adapter.py`): implementato
(order_send, positions_get, chiusura, SL/TP, equity) ma da usare consapevolmente
— richiede il pacchetto `MetaTrader5` (solo Windows, terminale aperto), le tue
credenziali **demo**, e rifiuta i server non-demo salvo `live=True` esplicito.
Non è coperto dai test automatici: va provato sul tuo conto demo.
