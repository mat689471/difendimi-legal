# ContentFlow — piano SaaS (automazione contenuti per aziende)

> Nome di lavoro: **ContentFlow** (cambialo quando vuoi).
> Prodotto: una piattaforma dove un'azienda si iscrive, paga un abbonamento, e
> ottiene contenuti social pronti (video verticali + testo + hashtag) generati
> in automatico dall'IA, riusando la pipeline Remotion che esiste già in questo
> repo.
>
> Questo documento è un **piano onesto**: architettura, costi *reali*, cosa
> devi procurarti tu, i passi legali, e un MVP concreto. Nessuna promessa da
> "100% di margine".

---

## 1. Il prodotto in una frase

Un'azienda collega il suo brand (logo, colori, tono, argomenti), e ogni
settimana riceve N video social pronti da pubblicare. Zero editing, zero
designer. Paga un canone mensile.

**A chi si vende (nicchia consigliata):** non "tutte le aziende" — troppo
vago. Parti da UNA nicchia che conosci. Dato che hai *difendimi-legal*, un
angolo forte è **studi legali / professionisti / commercialisti**: gente con
budget, poco tempo, e zero voglia di fare video. Nicchia = messaggio chiaro =
si vende. Allargherai dopo.

---

## 2. Architettura (mappata sullo stack della foto)

```
                 Cliente (browser)
                        │
              ┌─────────▼─────────┐
              │  Next.js su Vercel │  landing + dashboard + API
              └───┬───────────┬────┘
                  │           │
        Clerk (auth)   Stripe (abbonamenti)
                  │           │
        ┌─────────▼───────────▼─────────┐
        │        Supabase (Postgres)     │  utenti, brand, job, contenuti
        │        Upstash (Redis, coda)   │  coda dei job di generazione
        └─────────┬───────────┬──────────┘
                  │           │
        Claude API (testi)   Worker di render
                  │           │
        Pinecone (memoria    Remotion (il video)  ← già nel repo
        brand/argomenti)      su render service
                  │
        Resend (email)   Sentry + PostHog (monitoraggio)
```

- **Next.js/Vercel** — sito + dashboard + API.
- **Clerk** — registrazione/login clienti.
- **Stripe** — abbonamenti mensili (Billing), fatture, prova gratuita.
- **Supabase** — database (clienti, brand, contenuti generati, log).
- **Upstash (Redis)** — coda dei job: la generazione video è lenta, non la fai
  nella richiesta HTTP.
- **Claude API** — genera script, didascalie, hashtag (è il "cervello").
- **Pinecone** — memoria per brand: argomenti, esempi, tono di voce del cliente.
- **Remotion** — rende il video (riusiamo `remotion/` di questo repo, reso
  data-driven dalla pipeline `jarvis/content`).
- **Resend** — email ("i tuoi 5 video sono pronti").
- **Sentry/PostHog** — errori + analytics. *Jarvis li usa per RILEVARE e
  PROPORRE fix; il push in produzione resta con la tua conferma.*

---

## 3. Costi reali (la parte che la foto semplifica troppo)

### Fissi (mensili), quando sei commerciale
| Servizio | Free tier | Quando inizi a pagare | Costo tipico |
|---|---|---|---|
| Vercel | Hobby = **non commerciale** | Un SaaS a pagamento richiede **Pro** | ~$20/mese |
| Supabase | 500 MB DB, si sospende se inattivo | quando cresci | $0 → $25/mese |
| Clerk | fino a ~10k utenti attivi | oltre | $0 a lungo |
| Upstash | free generoso | ad alto volume | $0 → ~$10 |
| Pinecone | starter limitato | oltre | $0 → pay-as-you-go |
| Resend | 3.000 email/mese | oltre | $0 → $20 |
| Sentry/PostHog | free generoso | oltre | $0 a lungo |
| **Totale fisso realistico** | | | **~$20–45/mese** |

> ⚠️ Correzione onesta alla foto: **Vercel "Free" vale per progetti personali,
> non per un SaaS commerciale.** Mettere in conto ~$20/mese di Pro.

### Variabili (per cliente / per contenuto) — **il vero costo**
Questo è ciò che la foto ignora del tutto:
- **Claude (token)** per generare script+didascalie: ~€0,02–0,10 a video.
- **Render del video** (Remotion): il render è pesante e **non gira gratis** su
  una funzione serverless standard (timeout). Servono **Remotion Lambda (AWS)**
  o un piccolo worker dedicato: ~€0,05–0,20 a video.
- **Stripe**: ~1,5% + €0,25 a transazione (carte EU).

### Esempio di unit economics (onesto)
Cliente paga **€49/mese** per **30 video/mese**:
- Claude: 30 × ~€0,06 = **€1,80**
- Render: 30 × ~€0,15 = **€4,50**
- Stripe: **~€0,99**
- **Costo diretto ≈ €7,3** → **margine lordo ≈ 85%** (≈ €41,7)

Sembra ottimo — **ma** poi togli:
- **IVA 22%**: di €49 incassati, ~€40 sono tuoi (se sei in regime IVA ordinario).
- **Le tue ore**: supporto, vendite, fix. Questo è il costo vero e invisibile.
- **Tasse sul reddito**.

**Conclusione onesta:** il margine *sul prodotto* è alto (buona notizia,
tipico del SaaS). Ma "100% / costi zero" è falso: il collo di bottiglia non
sono i €7 di infrastruttura, sono **i clienti e il tuo tempo**.

---

## 4. Cosa devi procurarti TU (io scrivo il codice, non posso creare gli account)

- [ ] Account: Vercel, Supabase, Clerk, Stripe, Pinecone, Upstash, Resend,
      Sentry, PostHog, Cloudflare, Namecheap (dominio).
- [ ] Chiavi API di ciascuno (le metti in variabili d'ambiente, **mai** nel codice).
- [ ] **Partita IVA** (per incassare con Stripe serve un'entità reale).
- [ ] Account AWS se usiamo Remotion Lambda per il render.

## 5. Passi legali (Italia/UE) — non opzionali

- **Partita IVA** + regime fiscale (forfettario vs ordinario: senti un
  commercialista — con clienti UE cambia la gestione IVA/OSS).
- **GDPR**: tratti dati di aziende clienti → sei **responsabile del trattamento**.
  Servono privacy policy, DPA (accordo sul trattamento dati), base giuridica.
- **Termini di servizio** e policy di rimborso.
- Stripe richiede dati fiscali reali per pagarti.

> Non è burocrazia da rimandare: è la differenza tra un business e un problema.

---

## 6. MVP — la cosa più piccola che un cliente pagherebbe

Non costruire l'impero. Costruisci questo, in ordine:

1. **Landing** con una promessa chiara + pulsante "Prova gratis".
2. **Auth** (Clerk): registrazione/login.
3. **Onboarding brand**: il cliente inserisce logo, colori, 5 argomenti, tono.
4. **Generazione**: un pulsante "Genera 5 video" → coda → Claude scrive →
   Remotion rende → i video compaiono nella dashboard.
5. **Download / anteprima** dei video + testo + hashtag pronti.
6. **Stripe**: prova gratuita di 7 giorni, poi €X/mese.
7. **Email** (Resend): "i tuoi video sono pronti".

Tutto il resto (team, ruoli, API pubbliche, white-label…) viene DOPO i primi
clienti paganti. Non prima.

---

## 7. Roadmap

- **Fase 0 — validazione (prima del codice):** parla con 5–10 potenziali
  clienti della nicchia. Chiedi: "pagheresti €X/mese per questo?" Se nessuno
  dice sì, il codice non serve. *Questo è il passo più importante e non richiede
  una riga di codice.*
- **Fase 1 — MVP (codice):** i 7 punti sopra. Lo scaffoldo io.
- **Fase 2 — primi clienti:** onboarding manuale, molto supporto, tanti fix.
- **Fase 3 — automazione & scala:** solo quando l'MVP regge e qualcuno paga.

---

## 8. Dove fallisce (perché tu lo sappia)

- **Non trovi clienti** → è il rischio n°1, non il codice.
- **Il render costa più del previsto** ad alto volume → va misurato presto.
- **Qualità dei video** non abbastanza buona da giustificare il prezzo → serve
  iterazione sul creativo, non solo sul codice.
- **GDPR/fisco ignorati** → problemi seri più avanti.

---

## 9. Come si lega a Jarvis

Jarvis (questo repo) resta l'**assistente che ti aiuta a costruire e gestire**
ContentFlow: scrive il codice, monitora (Sentry/PostHog), *propone* i fix. Ma
ContentFlow è un **prodotto separato** con la sua vita. E — coerente con tutto
il resto — le azioni irreversibili in produzione (deploy, refund, cancellazioni)
passano dalla tua conferma. Il Guardiano vale anche qui.

---

*Prossimo passo consigliato: la Fase 0 (parlare coi clienti) in parallelo allo
scaffold dell'MVP. Dimmi "scaffold" e creo lo scheletro Next.js in `saas/app/`.*
