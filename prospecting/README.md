# Kit di prospezione — siti web per attività locali

Trova attività locali, distingue chi non ha un sito da chi ce l'ha messo male,
e raccoglie il materiale per costruire l'anteprima da mostrargli.

```
find-leads.js  ──▶  leads-<città>.json   ──▶  chi NON ha un sito
     │                                          (materiale per la bozza)
     └──────────▶  siti-da-verificare.txt
                          │
                   audit-site.js  ──▶  audit-siti.json  ──▶  chi ha un sito da rifare
                                                              (con i difetti da citare)
```

---

## Leggi prima questo: da dove arrivano le email

**Google Places non restituisce indirizzi email. Nessuna API pubblica lo fa.**
È il limite vero di questo lavoro e conviene saperlo prima di partire, non dopo.

Quindi, in pratica:

| Situazione | Come lo contatti |
|---|---|
| **Ha un sito** (anche brutto) | L'email quasi sempre è nella pagina contatti o nel footer. È il caso facile. |
| **Non ha un sito** | Spesso **non ha nemmeno un'email aziendale.** Il canale reale è il **telefono o WhatsApp**, e il numero ce l'hai già dal file. |

Da qui una conseguenza controintuitiva ma importante: i lead "senza sito", che
sono quelli col bisogno più forte, sono anche quelli che **per mail non
raggiungerai**. Per loro le tracce in `01-senza-sito.md` funzionano lo stesso,
ma vanno accorciate e usate come messaggio WhatsApp o come traccia telefonica.

Dove trovare comunque un'email, in ordine di resa:
1. La loro pagina Facebook o Instagram (nella sezione contatti, spesso c'è)
2. Il sito, se ce l'hanno (footer e pagina contatti)
3. La visura camerale, se cerchi la PEC — ma **alla PEC non si manda pubblicità**:
   è per comunicazioni formali, usarla per proporre servizi ti brucia il nome.

---

## Configurazione

### 1. Chiave Google Maps (obbligatoria)

**Serve una carta di credito.** Google chiede un account di fatturazione
attivo prima di rilasciare la chiave, anche se resti nel gratuito. Non è
un abbonamento e non ti addebita nulla finché stai sotto le soglie, ma la
carta va inserita: se non vuoi farlo, questi script non li puoi usare.

1. Vai su [console.cloud.google.com](https://console.cloud.google.com/) e accedi col tuo account Google
2. In alto, dal menu dei progetti, **Nuovo progetto** → dagli un nome → **Crea**
3. Menu ☰ → **Fatturazione** → collega un account di fatturazione (qui inserisci la carta)
4. Menu ☰ → **API e servizi** → **Libreria** → cerca **Places API (New)** → **Abilita**
5. Menu ☰ → **API e servizi** → **Credenziali** → **Crea credenziali** → **Chiave API**
6. Copia la chiave, poi **Modifica chiave** → in *Restrizioni API* scegli
   **Limita chiave** e seleziona solo **Places API (New)** → **Salva**

Il passo 6 non saltarlo: una chiave senza restrizioni, se finisce in giro,
può essere usata da altri su qualsiasi servizio Google e la fattura è tua.

```bash
export GOOGLE_MAPS_API_KEY="la-tua-chiave"
```

#### Quanto costa davvero

Da marzo 2025 Google ha **eliminato il credito unico da 200 $/mese** e lo ha
sostituito con soglie gratuite separate per tipo di chiamata, che si azzerano
ogni primo del mese e non si accumulano:

| Fascia | Gratis al mese |
|---|---|
| Essentials | ~10.000 chiamate |
| Pro | ~5.000 chiamate |
| Enterprise | ~1.000 chiamate |

Ogni richiesta **viene fatturata alla fascia più alta fra i campi che chiede**.
Questo è il meccanismo da capire, ed è il motivo per cui gli script chiedono
solo i campi necessari:

- La **ricerca** (`find-leads.js`, campi `rating`, `websiteUri`, ecc.) ricade
  in fascia **Pro**. Con ~5.000 chiamate gratuite e 20 risultati per chiamata,
  è tantissimo: non la esaurirai.
- L'**arricchimento** con le recensioni ricade in fascia **Enterprise**, la più
  cara e con solo ~1.000 chiamate gratuite. Per questo `find-leads.js` lo fa
  **solo sui migliori 40 lead senza sito**, non su tutti.

Le tariffe cambiano: la tabella qui sopra è una guida, il dato buono è quello
nella tua console.

#### Metti un tetto, non solo un avviso

Un avviso di budget ti manda una mail *dopo* che hai speso. Quello che ferma
davvero la spesa è il limite di quota:

Menu ☰ → **API e servizi** → **Places API (New)** → scheda **Quote** →
imposta un massimo di richieste al giorno (per iniziare, 500/giorno è
abbondante e ti rende impossibile prendere una brutta sorpresa).

Fallo **prima** della prima ricerca, non dopo.

### 2. Chiave PageSpeed (facoltativa)

Serve solo ad aggiungere i punteggi Lighthouse. Senza, l'audit funziona
comunque con le sue verifiche interne.

```bash
export PAGESPEED_API_KEY="la-tua-chiave"
```

---

## Uso

### Trovare i lead

```bash
node prospecting/find-leads.js --citta "Modena" --preset tutto --max 200 --minRecensioni 5
```

Opzioni:

| Opzione | Cosa fa |
|---|---|
| `--citta` | Città o zona da battere |
| `--preset` | Gruppo di categorie pronto (sotto) |
| `--categorie` | In alternativa: categorie tue, separate da virgola |
| `--max` | Tetto di risultati totali (contiene i costi) |
| `--minRecensioni` | Scarta le schede quasi vuote |

### Preset disponibili

| Preset | Copre |
|---|---|
| `artigiani` | Idraulici, elettricisti, fabbri, imbianchini, falegnami, condizionamento, antennisti, serramentisti, traslochi |
| `ristorazione` | Ristoranti, pizzerie, trattorie, osterie, bar, gelaterie, pasticcerie, agriturismi, sushi |
| `benessere` | Parrucchieri, barbieri, centri estetici, palestre, massaggi, nail center |
| `professionisti` | Commercialisti, avvocati, dentisti, fisioterapisti, geometri, architetti, veterinari |
| `negozi` | Ottiche, ferramenta, fiorai, gioiellerie, abbigliamento, panifici, macellerie, enoteche |
| `tutto` | Tutti e cinque i gruppi (42 categorie) |

### Una raccomandazione su `tutto`

`--preset tutto` fa 42 ricerche e può restituire diverse centinaia di attività:
consuma quota API e ti lascia una lista che non riuscirai a lavorare davvero.
**Conviene partire da un preset solo.** `artigiani` è il migliore per cominciare:
è il gruppo dove la percentuale di attività senza sito è più alta, il budget
c'è, e la decisione la prende una persona sola senza riunioni.

Quando quel gruppo è esaurito, passa al successivo. Meglio 40 lead lavorati
bene che 400 lasciati a metà — e le mail funzionano solo se le personalizzi
una per una.

Produce in `output/`:
- **`leads-<città>.json`** — tutto: recensioni testuali, foto, orari, priorità
- **`leads-<città>.csv`** — da aprire in Excel o Google Sheets come foglio di lavoro
- **`siti-da-verificare-<città>.txt`** — pronto per il passo successivo

### Analizzare i siti esistenti

```bash
node prospecting/audit-site.js --file prospecting/output/siti-da-verificare-modena.txt
```

Oppure uno solo:

```bash
node prospecting/audit-site.js --url https://esempio.it
```

Ogni sito riceve un punteggio da 0 a 100 e un verdetto:

| Verdetto | Significato |
|---|---|
| 🔴 `DA_RIFARE_SUBITO` | Il sito sta danneggiando l'attività. Lead migliore. |
| 🟠 `DA_RIFARE` | Problemi seri su mobile o visibilità. |
| 🟡 `DA_MIGLIORARE` | Funziona ma perde occasioni. |
| 🟢 `OK` | Sito in buono stato: **non scrivergli**, ci fai figuraccia. |
| ⚪ `NON_ANALIZZABILE` | Il server ha bloccato l'analisi. **Guardalo a mano nel browser** prima di scrivere. |

Quel `NON_ANALIZZABILE` non è un dettaglio: molti siti moderni rispondono
`403` agli strumenti automatici. Trattarli come rotti significherebbe scrivere
a un'azienda dicendole che il suo sito è da rifare quando invece è ottimo.

### Come si calcola la priorità

`find-leads.js` assegna 0-100 a ogni lead: recensioni numerose (attività viva,
con clienti veri), voto alto (reputazione già costruita da mettere a valore),
assenza di sito (bisogno massimo). Chi non ha un telefono raggiungibile viene
penalizzato. **Parti dai punteggi più alti**: sono attività che già lavorano
bene e a cui manca solo la vetrina.

---

## Sulle foto di Google

Gli URL in `foto` puntano alle immagini di Google Places. Sono utilizzabili
**solo come riferimento visivo mentre prepari la bozza**: non vanno ricaricate
sul sito finale, perché sono soggette alle condizioni d'uso di Google e spesso
sono di clienti che le hanno scattate. Nel momento in cui il cliente dice sì,
**chiedigli le sue foto** — e se non ne ha di decenti, quello è un servizio in
più da vendergli, non un ostacolo.

---

## Sulle regole delle comunicazioni commerciali

Scrivere a un'attività per proporle un servizio è normale attività commerciale.
Perché resti tale, in Italia conviene tenersi a tre cose:

1. **Scrivi agli indirizzi aziendali** (`info@`, `contatti@`), non a indirizzi
   personali di dipendenti.
2. **Identificati sempre**: nome, cognome, partita IVA se ce l'hai, recapiti veri.
   È anche ciò che distingue la tua mail dallo spam agli occhi di chi la legge.
3. **Dai una via d'uscita immediata e rispettala.** Se uno risponde "no grazie",
   sparisce dalla lista per sempre. Segnalo sul foglio.

Il piè di pagina in fondo a ogni modello copre i punti 2 e 3. **Non toglierlo.**
Alla PEC non scrivere: vedi sopra.

---

## Foglio di lavoro

Apri il CSV in Google Sheets e aggiungi queste colonne a mano:

| Colonna | Valori |
|---|---|
| `email_trovata` | l'indirizzo, o vuoto se non c'è |
| `canale` | `EMAIL` · `WHATSAPP` · `TELEFONO` |
| `stato` | `DA_CONTATTARE` · `CONTATTATO` · `RISPOSTO` · `ANTEPRIMA_INVIATA` · `CLIENTE` · `NON_INTERESSATO` · `RICONTATTARE` |
| `data_contatto` | quando hai scritto |
| `note` | cosa ti ha risposto |

Regola d'oro: **`NON_INTERESSATO` è definitivo.** Non riscrivere mai a chi
ha detto no. In una città media il passaparola fra commercianti è rapidissimo,
e la reputazione di quello che insiste te la porti dietro per anni.

---

## File

```
prospecting/
├── find-leads.js                    ricerca attività + classificazione
├── audit-site.js                    analisi dei siti esistenti
├── emails/
│   ├── 01-senza-sito.md             3 varianti + piè di pagina
│   ├── 02-sito-da-rifare.md         4 varianti per difetto rilevato
│   ├── 03-follow-up-e-risposte.md   solleciti, anteprima, obiezioni
│   └── 04-listino-e-canone.md       le due formule, trattativa, regole contrattuali
└── output/                          generato dagli script (non versionato)
```
