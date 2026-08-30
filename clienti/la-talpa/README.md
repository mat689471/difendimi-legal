# La Talpa — sito

Frontend Next.js 14 (App Router) + Tailwind + Framer Motion + Lucide.

```bash
npm install
npm run dev     # http://localhost:3000
npm run build
```

## Struttura

```
app/          layout, pagina, stili globali
components/   una sezione per file
lib/content.ts  TUTTI i testi e i dati: si modifica qui, non nei componenti
public/lavori/  immagini prima/dopo
```

---

## Da completare prima di pubblicare

Sono i punti dove servono dati reali dell'azienda. Ognuno è marcato
`SEGNAPOSTO` o `DA INSERIRE` anche nel codice.

| Cosa | Dove |
|---|---|
| Telefono, WhatsApp, email, P.IVA | `lib/content.ts` → `azienda` |
| Recensioni vere **parafrasate** | `lib/content.ts` → `recensioni` |
| Foto reali prima/dopo | `public/lavori/` + percorsi in `lavori` |
| Numero e media recensioni reali | `components/hero.tsx` |
| P.IVA, privacy e cookie policy | `components/site-footer.tsx` |
| **Invio del modulo** | `components/quote-wizard.tsx` |

### Le recensioni

Quelle presenti sono segnaposto, non recensioni di persone reali.
Vanno sostituite con recensioni vere **parafrasate** — copiarle testualmente
viola il copyright di chi le ha scritte. Se l'azienda non ne ha ancora,
si toglie la sezione: mostrarne di inventate è pubblicità ingannevole.

### Il modulo preventivo

Oggi il wizard valida i dati e mostra la conferma, **ma non invia nulla**.
Prima della pubblicazione serve collegare un destinatario (route handler
Next.js, Formspree o invio email) e gestire caricamento ed errore di rete.
Raccogliendo nome, telefono ed email servono anche informativa privacy e
consenso nel passo finale.

### Le foto

In `public/lavori/` ci sono quattro SVG segnaposto, utili solo a far vedere
il comparatore funzionante. Le foto vere vanno scattate **dallo stesso punto
e con la stessa inquadratura** prima e dopo: è l'unica cosa che rende
credibile il confronto. Da esportare in WebP, larghezza 1600px.

---

## Scelte tecniche

**Il comparatore prima/dopo è un `input[type=range]`.** Le WCAG 2.2 impongono
un'alternativa al trascinamento: un range nativo dà frecce, Home/End, tap e
drag senza gestori di puntatore fatti a mano e con il supporto screen reader
già incluso.

**Il marquee spazia con il margine delle schede, non con `gap`.** Con il gap
le due metà del nastro non misurano uguale, la traslazione del 50% non chiude
il ciclo e a ogni giro si vede uno scatto. Si ferma al passaggio del mouse,
quando il fuoco da tastiera vi entra, e con il pulsante di pausa.

**L'alone delle card servizi scrive variabili CSS**, non stato React: nessun
re-render mentre il mouse si muove.

**Le foglie dell'hero hanno posizioni fisse.** Un `Math.random()` genererebbe
markup diverso fra server e client, con errore di idratazione.

**`prefers-reduced-motion` è rispettato ovunque**, sia via `useReducedMotion`
di Framer Motion sia in CSS.

## Colori

Contrasti verificati su sfondo `#F7F5F1`:
`ink` 14.9:1 · `forest` 10.2:1 · `soil` 12.7:1 · `clay` 6.0:1 · `bronze` 4.6:1.

**`gold` (#B08D4F) sta a 2.85:1: è solo decorativo.** Mai testo, mai bordo che
debba comunicare uno stato. Per il testo caldo si usa `clay` (#6B5B4B).
