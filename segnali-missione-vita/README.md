# 🛰️ Segnali · Missione Vita

Un'**avventura esplorabile** (RPG dall'alto) tratta dal dossier «Vita nell'universo».
Non è un quiz: controlli un **personaggio** che si muove in un mondo di gioco.

Vesti i panni della **Dott.ssa Nova**, xenobiologa a bordo della base di ricerca
*Kepler*. Esplora il corridoio e i sei laboratori, **parla con l'equipaggio**
(sette personaggi con nome e ruolo), **esamina i reperti** e raccogli le 6 prove
per il briefing finale del Comandante.

## Come si gioca
- **Muoviti**: joystick a sinistra (touch) oppure **WASD** / frecce (tastiera). Gamepad supportato.
- **Interagisci**: avvicinati a una persona o a una console luminosa (appare «!») e premi **AZIONE** (o **Spazio**).
- **Obiettivo**: analizza i 6 reperti nei laboratori (Marte, Oceani, SETI, Archivio, UAP, Origini), poi torna dal Comandante.
- Ogni reperto entra nel diario con il suo **livello di prova** reale: 🟢 Provato · 🔵 Indizio · 🟣 Ipotesi · 🔴 Non verificato.

## L'equipaggio
Cap. Adler (Comandante) · Dott.ssa Vega (Marte) · Dott.ssa Mila (Oceani) ·
Dott. Orin (SETI) · Archiv. Sela (Archivio) · Tecn. Rho (UAP) · Dott.ssa Iris (Origini).

## Un solo file, offline
`index.html` è **autonomo**: personaggi e mondo sono disegnati in pixel-art via codice,
nessuna immagine esterna. Si apre con un doppio clic (anche da smartphone) e funziona
senza internet e senza server.

## Pubblicarlo online (link giocabile da cellulare)
- **GitHub Pages**: *Settings → Pages → Deploy from a branch* → il gioco sarà su
  `https://<utente>.github.io/difendimi-legal/segnali-missione-vita/`.
- Oppure trascina la cartella su **Netlify Drop**, o carica `index.html` su **itch.io** come gioco HTML.

## Estenderlo
- Dialoghi e reperti sono raccolti in fondo al file, nell'oggetto `window.DLG`: modificarli
  o tradurli non tocca la logica di gioco.
- Aggiungere una stanza = aggiungere una voce in `defsTop`/`defsbot` (in `build()`) e i
  relativi contenuti. Nuovi personaggi = una riga in `CREW`.

## Fonte
Tutti i contenuti derivano dal dossier di ricerca «Vita nell'universo» (fonti chiuse al
5 luglio 2026): la distinzione tra prove, indizi, ipotesi e affermazioni non verificate è
mantenuta come cuore del gioco.
