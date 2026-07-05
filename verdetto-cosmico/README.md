# 🛰️ Verdetto Cosmico

Un gioco a carte per smartphone e desktop tratto dal dossier **«Vita nell'universo»**.
Il giocatore veste i panni di un **revisore scientifico**: legge un caso reale
(una missione spaziale, un reperto antico, un segnale radio, un avvistamento UFO)
e deve assegnargli il giusto **livello di prova**.

## I quattro verdetti

| | Livello | Significato |
|---|---|---|
| 🟢 **A** | PROVATO | Osservato e ripetuto, con consenso scientifico |
| 🔵 **B** | INDIZIO | Dato reale ma non conclusivo |
| 🟣 **C** | IPOTESI | Idea testabile che guida la ricerca |
| 🔴 **D** | NON VERIFICATO | Manca una prova controllabile |

Ogni risposta rivela la spiegazione tratta dal dossier: è così che si impara a
distinguere una **prova** da una **suggestione**. Il gioco contiene **44 casi
reali** in 8 fascicoli (Origine della vita, Marte, Lune oceaniche, Esopianeti,
SETI, UAP/UFO, Archivi antichi, Cosmo).

## Come si gioca
- 3 vite, punteggio con moltiplicatore di serie (🔥), gradi da *Curioso* a *Direttore di ricerca*.
- **Sfida del giorno**: 10 casi uguali per tutti, un tentativo al giorno.
- Comandi: tocco su smartphone, tasti **1–4** su tastiera. Progressi salvati sul dispositivo.

## Due versioni incluse

| File | A cosa serve |
|---|---|
| `gioca-offline.html` | **File singolo.** Aprilo con un doppio clic o mandalo a chiunque: funziona da solo, senza internet e senza server. |
| `index.html` + `data.js` + `strings.js` + `logic.js` | Versione modulare per la **pubblicazione online** (GitHub Pages, Netlify, itch.io…). Va servita da un server web (i moduli non si caricano da `file://`). |

## Pubblicarlo online gratis (link giocabile da cellulare)

**GitHub Pages** (gratis):
1. Su GitHub → *Settings → Pages*.
2. *Source*: `Deploy from a branch`, scegli il branch e la cartella root.
3. Il gioco sarà su `https://<utente>.github.io/difendimi-legal/verdetto-cosmico/`.

In alternativa trascina la cartella su **Netlify Drop** (netlify.com/drop) o carica
`gioca-offline.html` su **itch.io** come gioco HTML.

## 💜 Monetizzazione (attivazione)

Il gioco è pronto per un primo guadagno leggero. Nella schermata **«Sostieni»**
c'è già un pulsante donazioni. Per attivarlo, apri `index.html` (e/o
`gioca-offline.html`) e cerca in alto nello `<script>`:

```js
const DONATE_URL = "";   // ← incolla qui il tuo link
```

Incolla il tuo link **Ko-fi**, **BuyMeACoffee** o **PayPal.me** (es.
`"https://ko-fi.com/tuonome"`). Fatto: chi vuole sostenerti aprirà quel link.

Idee di guadagno, dalla più semplice:
1. **Donazioni** (Ko-fi/BuyMeACoffee) — zero costi, attivi in 2 minuti (già predisposto).
2. **itch.io "paga quanto vuoi"** — pubblichi `gioca-offline.html` e accetti offerte libere.
3. **Pubblicità** — ospita su un tuo sito con Google AdSense, o usa un portale di
   giochi HTML (es. GameDistribution/Poki) che paga per le partite.
4. **Fascicoli extra a pagamento** — lo scheletro è già pronto (schermata «Sostieni»
   → *Fascicoli extra*): aggiungi nuovi casi in `data.js` e vendili come pacchetti.
5. **Traffico virale** — i casi a sorpresa (Roswell, Anticitera, Wow! signal…) sono
   fatti per essere condivisi: pubblica clip/quiz sui social con il link al gioco.

## Fonte
Tutti i casi derivano dal dossier di ricerca **«Vita nell'universo»**
(fonti chiuse al 5 luglio 2026). Il gioco mantiene la distinzione tra prove,
indizi, ipotesi e affermazioni non verificate — nessuna affermazione è presentata
come prova senza il suo livello reale.
