# Mail per attività CON un sito messo male

> Regola che vale più di tutte: **cita un problema che hai verificato tu**,
> preso da `audit-siti.json`. Un difetto specifico e vero dimostra che hai
> guardato davvero; una frase generica tipo "il suo sito è migliorabile"
> dice solo che stai mandando la stessa mail a duecento persone.
>
> Se l'audit ha dato `NON_ANALIZZABILE`, **apri il sito nel browser e guardalo
> a mano** prima di scrivere. Non scrivere mai basandoti su un'analisi bloccata.

---

## Variante A — sito non usabile da telefono

**Usala quando:** l'audit segnala `NO_VIEWPORT` o `NON_RESPONSIVE`
**È la leva più forte in assoluto:** riguarda circa 7 visitatori su 10.

**Oggetto:** `Il sito di «Nome Attività» dal cellulare`

```
Buongiorno,

ho aperto «www.suosito.it» dal telefono e la pagina esce rimpicciolita:
per leggere qualsiasi cosa bisogna ingrandire con le dita e trascinare
la schermata a destra e sinistra.

Glielo segnalo perché oggi la gran parte delle persone vi cerca dal
cellulare, di solito mentre è fuori. Chi trova una pagina così quasi
sempre la chiude in pochi secondi — e quella visita era un cliente
che stava decidendo se chiamarvi.

Mi chiamo [NOME] e rifaccio siti per attività locali della zona.

Se le fa piacere le preparo un'anteprima di come apparirebbe
«Nome Attività» su un telefono, e gliela mando. La guarda e mi dice se
le interessa: vederla non costa nulla e non la impegna.

Le va?

[FIRMA]
[TELEFONO]
```

---

## Variante B — sito abbandonato

**Usala quando:** l'audit segnala `ABBANDONATO` (copyright vecchio di 3+ anni)

**Oggetto:** `Una cosa sul sito di «Nome Attività»`

```
Buongiorno,

sono capitato su «www.suosito.it» e in fondo alla pagina c'è ancora
scritto «© 2018».

Non è un dettaglio da poco: chi arriva lì pensa che l'attività abbia
chiuso, o che gli orari e i prezzi non siano più quelli. Nel dubbio
non chiama. Ed è un peccato, perché la vostra scheda Google racconta
tutt'altro: «4,8» stelle su «94» recensioni, quindi lavorate e
lavorate bene.

Mi chiamo [NOME] e rifaccio siti per attività della zona.

Le preparo un'anteprima di un sito nuovo per «Nome Attività» e gliela
mando: se le piace ne parliamo, altrimenti pazienza. Guardarla non
costa nulla.

Le interessa?

[FIRMA]
[TELEFONO]
```

---

## Variante C — sito senza HTTPS

**Usala quando:** l'audit segnala `NO_HTTPS`

**Oggetto:** `Chrome segnala il vostro sito come "Non sicuro"`

```
Buongiorno,

le scrivo per una cosa che forse nessuno le ha fatto notare: aprendo
«www.suosito.it» con Chrome, accanto all'indirizzo compare la scritta
"Non sicuro".

Succede perché il sito non usa una connessione protetta. Non è un
problema tecnico grave in sé, ma è la prima cosa che vede chi arriva —
e il messaggio che passa è che l'attività non sia affidabile. Sta
succedendo a ogni singola visita.

Mi chiamo [NOME] e mi occupo di siti per attività locali.

Se vuole le preparo un'anteprima di un sito nuovo per «Nome Attività»,
protetto e utilizzabile da telefono, e gliela mando da vedere. Nessun
costo e nessun impegno.

Le va?

[FIRMA]
[TELEFONO]
```

---

## Variante D — sito lentissimo

**Usala quando:** l'audit segnala `MOLTO_LENTO`, o Lighthouse performance < 30

**Oggetto:** `«www.suosito.it» ci mette «8» secondi ad aprirsi`

```
Buongiorno,

ho cronometrato il caricamento di «www.suosito.it» dal telefono:
«8,2» secondi prima di vedere qualcosa.

Google ha misurato che oltre metà delle persone abbandona una pagina
che ne impiega più di tre. Vuol dire che una buona parte di chi vi
cerca non arriva mai a vedere il sito — e voi non ve ne accorgete,
perché quelle visite non lasciano traccia.

Mi chiamo [NOME] e rifaccio siti per attività locali.

Le preparo un'anteprima di «Nome Attività» e gliela mando: la guarda,
e se le sembra un passo avanti ne parliamo. Vederla non costa niente.

Le interessa?

[FIRMA]
[TELEFONO]
```

---

## Da non fare mai

- **Non elencare più di un problema.** Tre difetti insieme suonano come un
  attacco: chi legge si mette sulla difensiva invece che sulla curiosità.
- **Non nominare chi glielo ha fatto.** Spesso è un parente, un amico o
  il figlio. Criticarlo chiude la conversazione all'istante.
- **Non allegare l'audit tecnico.** Punteggi e sigle non li legge nessuno.
- **Non scrivere "il suo sito è vecchio/brutto".** Descrivi cosa succede a
  chi lo visita, non il tuo giudizio su di lui.

---

## Piè di pagina — obbligatorio

```
—
[NOME COGNOME] · [PARTITA IVA se ce l'hai]
[EMAIL] · [TELEFONO] · [SITO_TUO]

Le scrivo una sola volta a questo indirizzo, reperito fra i contatti
pubblici della sua attività. Se non desidera altre comunicazioni,
risponda "no grazie" e non la contatterò più.
```
