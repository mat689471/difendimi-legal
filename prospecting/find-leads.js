#!/usr/bin/env node
/**
 * find-leads.js — Trova attività locali e le classifica per presenza online.
 *
 * Fonte dati: Google Places API (New). Il campo `websiteUri` dice in modo
 * diretto se un'attività ha un sito: se manca, non ce l'ha. Niente euristiche.
 *
 * Uso:
 *   GOOGLE_MAPS_API_KEY=xxx node prospecting/find-leads.js \
 *     --citta "Modena" --categorie "idraulico,parrucchiere,pizzeria" --max 60
 *
 * Output in prospecting/output/:
 *   leads-<citta>.json  dati completi (recensioni, foto, orari)
 *   leads-<citta>.csv   vista tabellare per il foglio di lavoro
 */

const fs = require('fs');
const path = require('path');

const API_KEY = process.env.GOOGLE_MAPS_API_KEY;
const SEARCH_URL = 'https://places.googleapis.com/v1/places:searchText';
const OUT_DIR = path.join(__dirname, 'output');

// Campi richiesti nella ricerca. Il FieldMask determina il costo: chiedere solo
// il necessario tiene le chiamate nella fascia economica.
const SEARCH_FIELDS = [
  'places.id',
  'places.displayName',
  'places.formattedAddress',
  'places.nationalPhoneNumber',
  'places.websiteUri',
  'places.rating',
  'places.userRatingCount',
  'places.businessStatus',
  'places.googleMapsUri',
  'places.primaryTypeDisplayName',
  'places.location',
].join(',');

// Dettaglio: recensioni testuali, foto e orari servono a costruire il sito.
const DETAIL_FIELDS = [
  'id',
  'displayName',
  'formattedAddress',
  'nationalPhoneNumber',
  'internationalPhoneNumber',
  'websiteUri',
  'rating',
  'userRatingCount',
  'reviews',
  'photos',
  'regularOpeningHours',
  'editorialSummary',
  'googleMapsUri',
  'primaryTypeDisplayName',
].join(',');

function parseArgs(argv) {
  const args = { citta: '', categorie: '', max: 60, minRecensioni: 0 };
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i].replace(/^--/, '');
    if (key in args) args[key] = argv[i + 1];
  }
  args.max = Number(args.max);
  args.minRecensioni = Number(args.minRecensioni);
  return args;
}

async function callPlaces(url, { method = 'GET', body = null, fieldMask }) {
  const res = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Goog-Api-Key': API_KEY,
      'X-Goog-FieldMask': fieldMask,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(`Places API ${res.status}: ${text.slice(0, 400)}`);
  }
  return JSON.parse(text);
}

/** Cerca tutte le attività di una categoria in una città, seguendo la paginazione. */
async function searchCategory(categoria, citta, max) {
  const places = [];
  let pageToken = null;

  do {
    const body = {
      textQuery: `${categoria} a ${citta}`,
      languageCode: 'it',
      regionCode: 'IT',
      pageSize: 20,
    };
    if (pageToken) body.pageToken = pageToken;

    const data = await callPlaces(SEARCH_URL, {
      method: 'POST',
      body,
      fieldMask: `${SEARCH_FIELDS},nextPageToken`,
    });

    places.push(...(data.places || []));
    pageToken = data.nextPageToken || null;

    // Il token diventa valido dopo un istante: piccola pausa fra le pagine.
    if (pageToken) await new Promise((r) => setTimeout(r, 1200));
  } while (pageToken && places.length < max);

  return places.slice(0, max).map((p) => ({ ...p, _categoria: categoria }));
}

/** Recupera recensioni, foto e orari per una singola attività. */
async function fetchDetails(placeId) {
  return callPlaces(`https://places.googleapis.com/v1/places/${placeId}`, {
    fieldMask: DETAIL_FIELDS,
  });
}

/**
 * Costruisce gli URL delle foto. Le immagini di Places sono utilizzabili solo
 * con attribuzione e non vanno ricaricate su un sito di produzione: servono
 * come riferimento visivo per la bozza, poi si chiedono le foto al cliente.
 */
function photoUrls(photos = [], limit = 6) {
  return photos.slice(0, limit).map((ph) => ({
    url: `https://places.googleapis.com/v1/${ph.name}/media?maxWidthPx=1600&key=${API_KEY}`,
    attribuzione: (ph.authorAttributions || []).map((a) => a.displayName).join(', '),
  }));
}

/** Punteggio di priorità: quanto vale la pena contattare questo lead. */
function scorePriorita(lead) {
  let score = 0;
  // Molte recensioni = attività viva, con clienti reali da intercettare.
  if (lead.numeroRecensioni >= 100) score += 40;
  else if (lead.numeroRecensioni >= 40) score += 30;
  else if (lead.numeroRecensioni >= 10) score += 20;
  else score += 5;

  // Voto alto = ha già una reputazione da mettere a valore sul sito.
  if (lead.voto >= 4.5) score += 30;
  else if (lead.voto >= 4.0) score += 20;
  else if (lead.voto >= 3.5) score += 10;

  // Nessun sito = il bisogno è massimo.
  if (!lead.sitoWeb) score += 30;

  // Senza telefono non lo raggiungi: penalizza.
  if (!lead.telefono) score -= 15;

  return Math.max(0, Math.min(100, score));
}

function toCsv(rows) {
  const cols = [
    'priorita', 'categoria', 'nome', 'stato_online', 'voto', 'numeroRecensioni',
    'telefono', 'indirizzo', 'sitoWeb', 'googleMaps', 'placeId',
  ];
  const esc = (v) => {
    const s = v === undefined || v === null ? '' : String(v);
    return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [cols.join(','), ...rows.map((r) => cols.map((c) => esc(r[c])).join(','))].join('\n');
}

async function main() {
  const args = parseArgs(process.argv);

  if (!API_KEY) {
    console.error('Manca GOOGLE_MAPS_API_KEY. Vedi prospecting/README.md');
    process.exit(1);
  }
  if (!args.citta || !args.categorie) {
    console.error('Uso: node prospecting/find-leads.js --citta "Modena" --categorie "idraulico,pizzeria"');
    process.exit(1);
  }

  const categorie = args.categorie.split(',').map((c) => c.trim()).filter(Boolean);
  const perCategoria = Math.max(1, Math.ceil(args.max / categorie.length));
  const visti = new Set();
  const leads = [];

  for (const categoria of categorie) {
    process.stdout.write(`Cerco "${categoria}" a ${args.citta}... `);
    let trovati;
    try {
      trovati = await searchCategory(categoria, args.citta, perCategoria);
    } catch (err) {
      console.log(`errore: ${err.message}`);
      continue;
    }
    console.log(`${trovati.length} risultati`);

    for (const p of trovati) {
      if (visti.has(p.id)) continue;              // stessa attività in più categorie
      visti.add(p.id);
      if (p.businessStatus && p.businessStatus !== 'OPERATIONAL') continue;  // chiusa

      const lead = {
        placeId: p.id,
        nome: p.displayName?.text || '',
        categoria: p._categoria,
        tipo: p.primaryTypeDisplayName?.text || '',
        indirizzo: p.formattedAddress || '',
        telefono: p.nationalPhoneNumber || '',
        sitoWeb: p.websiteUri || '',
        voto: p.rating || 0,
        numeroRecensioni: p.userRatingCount || 0,
        googleMaps: p.googleMapsUri || '',
        coordinate: p.location || null,
        stato_online: p.websiteUri ? 'HA_SITO' : 'SENZA_SITO',
      };

      if (lead.numeroRecensioni < args.minRecensioni) continue;
      lead.priorita = scorePriorita(lead);
      leads.push(lead);
    }
  }

  // I lead senza sito sono quelli per cui costruiamo la bozza: servono i
  // materiali (recensioni da citare, foto, orari). Li arricchiamo solo per loro
  // e per i migliori, per non sprecare chiamate a pagamento.
  const daArricchire = leads
    .filter((l) => l.stato_online === 'SENZA_SITO' && l.priorita >= 50)
    .sort((a, b) => b.priorita - a.priorita)
    .slice(0, 40);

  console.log(`\nArricchisco ${daArricchire.length} lead senza sito (recensioni, foto, orari)...`);
  for (const lead of daArricchire) {
    try {
      const d = await fetchDetails(lead.placeId);
      lead.recensioni = (d.reviews || []).map((r) => ({
        autore: r.authorAttribution?.displayName || '',
        voto: r.rating,
        testo: r.text?.text || r.originalText?.text || '',
        quando: r.relativePublishTimeDescription || '',
      }));
      lead.foto = photoUrls(d.photos);
      lead.orari = d.regularOpeningHours?.weekdayDescriptions || [];
      lead.descrizione = d.editorialSummary?.text || '';
    } catch (err) {
      lead.erroreDettagli = err.message;
    }
  }

  leads.sort((a, b) => b.priorita - a.priorita);

  const senzaSito = leads.filter((l) => l.stato_online === 'SENZA_SITO');
  const conSito = leads.filter((l) => l.stato_online === 'HA_SITO');

  fs.mkdirSync(OUT_DIR, { recursive: true });
  const slug = args.citta.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const jsonPath = path.join(OUT_DIR, `leads-${slug}.json`);
  const csvPath = path.join(OUT_DIR, `leads-${slug}.csv`);
  const sitiPath = path.join(OUT_DIR, `siti-da-verificare-${slug}.txt`);

  fs.writeFileSync(jsonPath, JSON.stringify({ citta: args.citta, generato: new Date().toISOString(), leads }, null, 2));
  fs.writeFileSync(csvPath, toCsv(leads));
  // Lista pronta da passare all'auditor dei siti esistenti.
  fs.writeFileSync(sitiPath, conSito.map((l) => `${l.sitoWeb}\t${l.nome}`).join('\n'));

  console.log(`
─────────────────────────────────────────
  Totale attività trovate : ${leads.length}
  SENZA sito web          : ${senzaSito.length}   <- target "creazione sito"
  CON sito web            : ${conSito.length}   <- passali a audit-site.js
─────────────────────────────────────────
  ${path.relative(process.cwd(), jsonPath)}
  ${path.relative(process.cwd(), csvPath)}
  ${path.relative(process.cwd(), sitiPath)}

Prossimo passo:
  node prospecting/audit-site.js --file ${path.relative(process.cwd(), sitiPath)}
`);
}

main().catch((err) => {
  console.error('Errore:', err.message);
  process.exit(1);
});
