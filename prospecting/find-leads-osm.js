#!/usr/bin/env node
/**
 * find-leads-osm.js — Trova attività senza sito web usando OpenStreetMap.
 *
 * Alternativa gratuita a find-leads.js: nessuna chiave, nessuna carta di
 * credito, nessun costo. In cambio i dati di contatto sono molto più poveri.
 *
 * Cosa dà bene:   nome, indirizzo, categoria, e soprattutto se hanno un sito
 * Cosa dà male:   il telefono c'è in circa 1 caso su 5, l'email quasi mai
 *
 * Per questo ogni lead esce con un link diretto a Google Maps: apri, leggi il
 * numero, incollalo nel CSV. È lavoro manuale, ma su 40 lead è meno di un'ora
 * e non costa niente.
 *
 * Uso:
 *   node prospecting/find-leads-osm.js --citta "Modena" --preset artigiani
 */

const fs = require('fs');
const path = require('path');

const OUT_DIR = path.join(__dirname, 'output');

// Mirror pubblici in ordine di preferenza: se il primo limita, si passa al
// successivo. Sono servizi offerti gratuitamente, quindi una query alla volta.
const MIRROR = [
  'https://overpass-api.de/api/interpreter',
  'https://overpass.kumi.systems/api/interpreter',
  'https://overpass.private.coffee/api/interpreter',
];

/**
 * Categorie tradotte nei tag OpenStreetMap. La struttura dei tag OSM non
 * coincide con le categorie commerciali: un idraulico è `craft=plumber`,
 * un ristorante è `amenity=restaurant`, un parrucchiere è `shop=hairdresser`.
 */
const PRESET = {
  artigiani: [
    ['craft', 'plumber|electrician|carpenter|painter|hvac|metal_construction|roofer|locksmith|glaziery'],
  ],
  ristorazione: [
    ['amenity', 'restaurant|cafe|bar|fast_food|ice_cream|pub'],
    ['shop', 'bakery|pastry|confectionery'],
  ],
  benessere: [
    ['shop', 'hairdresser|beauty|massage|nail_salon'],
    ['leisure', 'fitness_centre'],
  ],
  professionisti: [
    ['office', 'lawyer|accountant|estate_agent|insurance|architect'],
    ['amenity', 'dentist|veterinary|doctors'],
    ['healthcare', 'physiotherapist|psychotherapist'],
  ],
  negozi: [
    ['shop', 'optician|hardware|florist|jewelry|butcher|greengrocer|clothes|shoes|furniture|bicycle|sports'],
  ],
};
PRESET.tutto = Object.values(PRESET).flat();

function parseArgs(argv) {
  const args = { citta: '', preset: 'artigiani', max: 500 };
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i].replace(/^--/, '');
    if (key in args) args[key] = argv[i + 1];
  }
  args.max = Number(args.max);
  return args;
}

/** Costruisce la query Overpass QL per una città e un gruppo di tag. */
function buildQuery(citta, coppie, max) {
  const blocchi = coppie.map(([k, v]) => `nwr["${k}"~"${v}"](area.a);`).join('');
  return `[out:json][timeout:180];`
    + `area["name"="${citta}"]["admin_level"~"8|7|6"]->.a;`
    + `(${blocchi});`
    + `out center tags ${max};`;
}

const attendi = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Interroga i mirror Overpass. Sono server pubblici gratuiti sotto carico
 * costante: un 500 o un reset è quasi sempre passeggero, non un guasto. Per
 * questo ogni mirror viene ritentato prima di passare al successivo — senza,
 * una singola sfortuna farebbe fallire l'intera ricerca.
 */
async function interroga(query) {
  const TENTATIVI = 3;
  let ultimoErrore;

  for (const url of MIRROR) {
    const host = new URL(url).hostname;

    for (let n = 1; n <= TENTATIVI; n++) {
      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ data: query }),
        });
        const testo = await res.text();

        // Il limite è per indirizzo IP e si libera da solo dopo qualche minuto.
        if (res.status === 429 || /rate_limited/i.test(testo)) {
          ultimoErrore = 'limite di richieste raggiunto';
          console.log(`  ${host}: limite raggiunto`);
          break;                                   // inutile insistere: cambia mirror
        }
        if (!res.ok) {
          ultimoErrore = `HTTP ${res.status}`;
          if (n < TENTATIVI) {
            console.log(`  ${host}: HTTP ${res.status}, ritento fra ${n * 5}s (${n}/${TENTATIVI - 1})`);
            await attendi(n * 5000);
            continue;
          }
          break;
        }

        const dati = JSON.parse(testo);
        console.log(`  ${host}: ${dati.elements?.length || 0} elementi`);
        return dati.elements || [];
      } catch (err) {
        ultimoErrore = err.message;
        if (n < TENTATIVI) {
          console.log(`  ${host}: ${err.message}, ritento fra ${n * 5}s (${n}/${TENTATIVI - 1})`);
          await attendi(n * 5000);
        }
      }
    }
  }

  throw new Error(
    `nessun mirror ha risposto (${ultimoErrore}).\n`
    + '  I server Overpass sono gratuiti e a volte sovraccarichi: riprova fra 5-10 minuti.\n'
    + '  Se il problema è il limite di richieste, si libera da solo.'
  );
}

const primo = (tags, ...chiavi) => chiavi.map((k) => tags[k]).find(Boolean) || '';

function normalizza(el, citta) {
  const t = el.tags || {};
  const categoria = primo(t, 'craft', 'shop', 'amenity', 'office', 'healthcare', 'leisure');
  const via = [t['addr:street'], t['addr:housenumber']].filter(Boolean).join(' ');

  // Il link a Google Maps è ciò che rende recuperabile il telefono mancante:
  // una ricerca già compilata con nome e indirizzo.
  const query = encodeURIComponent([t.name, via, citta].filter(Boolean).join(' '));

  return {
    nome: t.name,
    categoria,
    indirizzo: via,
    citta: t['addr:city'] || citta,
    telefono: primo(t, 'phone', 'contact:phone', 'mobile'),
    email: primo(t, 'email', 'contact:email'),
    sitoWeb: primo(t, 'website', 'contact:website'),
    facebook: primo(t, 'contact:facebook', 'facebook'),
    orari: t.opening_hours || '',
    cercaSuGoogle: `https://www.google.com/maps/search/?api=1&query=${query}`,
    osm: `https://www.openstreetmap.org/${el.type}/${el.id}`,
  };
}

function toCsv(righe) {
  const cols = ['nome', 'categoria', 'indirizzo', 'citta', 'telefono', 'email',
    'facebook', 'orari', 'cercaSuGoogle', 'osm'];
  const esc = (v) => {
    const s = v == null ? '' : String(v);
    return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [cols.join(','), ...righe.map((r) => cols.map((c) => esc(r[c])).join(','))].join('\n');
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.citta) {
    console.error('Uso: node prospecting/find-leads-osm.js --citta "Modena" --preset artigiani');
    console.error(`Preset: ${Object.keys(PRESET).join(', ')}`);
    process.exit(1);
  }
  if (!PRESET[args.preset]) {
    console.error(`Preset sconosciuto. Disponibili: ${Object.keys(PRESET).join(', ')}`);
    process.exit(1);
  }

  console.log(`Cerco "${args.preset}" a ${args.citta} su OpenStreetMap...`);
  const elementi = await interroga(buildQuery(args.citta, PRESET[args.preset], args.max));

  const visti = new Set();
  const tutte = elementi
    .filter((e) => e.tags?.name)
    .map((e) => normalizza(e, args.citta))
    .filter((l) => {
      const chiave = `${l.nome}|${l.indirizzo}`.toLowerCase();
      if (visti.has(chiave)) return false;      // stessa attività mappata più volte
      visti.add(chiave);
      return true;
    });

  const senzaSito = tutte.filter((l) => !l.sitoWeb);
  const conSito = tutte.filter((l) => l.sitoWeb);

  // Chi ha già telefono o indirizzo è lavorabile subito: mettilo in cima.
  senzaSito.sort((a, b) =>
    (b.telefono ? 2 : 0) + (b.indirizzo ? 1 : 0) - ((a.telefono ? 2 : 0) + (a.indirizzo ? 1 : 0)));

  fs.mkdirSync(OUT_DIR, { recursive: true });
  const slug = `${args.citta}-${args.preset}`.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const csvPath = path.join(OUT_DIR, `osm-${slug}.csv`);
  const sitiPath = path.join(OUT_DIR, `osm-siti-${slug}.txt`);

  fs.writeFileSync(csvPath, toCsv(senzaSito));
  fs.writeFileSync(sitiPath, conSito.map((l) => `${l.sitoWeb}\t${l.nome}`).join('\n'));

  const conTel = senzaSito.filter((l) => l.telefono).length;

  console.log(`
─────────────────────────────────────────
  Attività trovate   : ${tutte.length}
  SENZA sito web     : ${senzaSito.length}
    già con telefono : ${conTel}
    da completare    : ${senzaSito.length - conTel}  <- apri "cercaSuGoogle" e copia il numero
  CON sito web       : ${conSito.length}
─────────────────────────────────────────
  ${path.relative(process.cwd(), csvPath)}
  ${path.relative(process.cwd(), sitiPath)}

Prossimi passi:
  1. Apri il CSV, ordina per "telefono" e parti da chi ce l'ha già.
  2. Per gli altri clicca "cercaSuGoogle": si apre la scheda, copi il numero.
  3. Analizza i siti esistenti:
     node prospecting/audit-site.js --file ${path.relative(process.cwd(), sitiPath)}
`);
}

main().catch((err) => {
  console.error('Errore:', err.message);
  process.exit(1);
});
