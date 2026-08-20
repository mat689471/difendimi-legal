#!/usr/bin/env node
/**
 * audit-site.js — Misura quanto è messo male il sito di un'attività.
 *
 * Serve a distinguere in modo oggettivo "sito vecchio ma dignitoso" da
 * "sito da rifare", per non presentarsi da un cliente dicendo che il suo sito
 * fa schifo senza poterlo dimostrare. Ogni problema rilevato diventa una riga
 * concreta da citare nella mail.
 *
 * Uso:
 *   node prospecting/audit-site.js --url https://esempio.it
 *   node prospecting/audit-site.js --file prospecting/output/siti-da-verificare-modena.txt
 *
 * Con PAGESPEED_API_KEY aggiunge i punteggi reali di Google Lighthouse.
 */

const fs = require('fs');
const path = require('path');

const OUT_DIR = path.join(__dirname, 'output');
const PSI_KEY = process.env.PAGESPEED_API_KEY || '';
// Un User-Agent da bot fa scattare le protezioni e restituisce pagine di errore
// che verrebbero scambiate per il sito vero. Ci presentiamo come un browser reale.
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

function parseArgs(argv) {
  const args = { url: '', file: '', psi: PSI_KEY ? 'si' : 'no' };
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i].replace(/^--/, '');
    if (key in args) args[key] = argv[i + 1];
  }
  return args;
}

async function fetchPage(url) {
  const started = Date.now();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const res = await fetch(url, {
      redirect: 'follow',
      signal: controller.signal,
      headers: { 'User-Agent': UA },
    });
    const html = await res.text();
    return {
      ok: true,
      status: res.status,
      finalUrl: res.url,
      html,
      ms: Date.now() - started,
      bytes: Buffer.byteLength(html),
    };
  } catch (err) {
    return { ok: false, errore: err.name === 'AbortError' ? 'timeout (>20s)' : err.message };
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Ogni controllo restituisce un problema con un peso. Il peso riflette quanto
 * quel difetto costa in clienti persi, non quanto è brutto da vedere.
 */
function sembraPaginaDiBlocco(html, status) {
  if (status === 403 || status === 429) return true;
  const h = html.toLowerCase();
  return /access denied|attention required|cloudflare|just a moment|checking your browser|richiesta bloccata|captcha/.test(h)
    && html.length < 40000;
}

function analizzaHtml({ html, finalUrl, ms, bytes }) {
  const problemi = [];
  const h = html.toLowerCase();
  const add = (peso, codice, messaggio) => problemi.push({ peso, codice, messaggio });

  // --- Sicurezza: il browser mostra "Non sicuro" accanto al nome dell'attività.
  if (!finalUrl.startsWith('https://')) {
    add(25, 'NO_HTTPS', 'Il sito non usa HTTPS: Chrome lo segnala come "Non sicuro" ai visitatori');
  }

  // --- Mobile: senza viewport il sito esce rimpicciolito sul telefono.
  const viewport = /<meta[^>]+name=["']?viewport["']?[^>]*>/i.test(html);
  if (!viewport) {
    add(30, 'NO_VIEWPORT', 'Nessun meta viewport: sul cellulare il sito appare miniaturizzato e illeggibile');
  }

  // --- Responsive: nessuna media query e nessun framework moderno.
  const hasMediaQuery = /@media[^{]*\((min|max)-width/i.test(html);
  const hasFramework = /(tailwind|bootstrap|foundation|bulma)/i.test(h);
  if (!hasMediaQuery && !hasFramework && !viewport) {
    add(20, 'NON_RESPONSIVE', 'Nessun adattamento a schermi piccoli: layout fisso da desktop');
  }

  // --- Tecnologie morte.
  if (/<frameset|<frame\s/i.test(html)) add(25, 'FRAMES', 'Usa i frame HTML, tecnologia abbandonata da oltre 15 anni');
  if (/\.swf|shockwave-flash|<embed[^>]+flash/i.test(h)) add(30, 'FLASH', 'Contiene Adobe Flash: non funziona più su nessun browser dal 2021');
  if (/<marquee|<blink|<center|<font\s/i.test(h)) add(15, 'TAG_OBSOLETI', 'Usa tag HTML obsoleti (font, center, marquee): impaginazione anni 2000');

  // --- Layout a tabelle: molte <table> senza intestazioni = griglia di impaginazione.
  const tables = (h.match(/<table/g) || []).length;
  const th = (h.match(/<th[\s>]/g) || []).length;
  if (tables >= 3 && th === 0) {
    add(20, 'LAYOUT_TABELLE', `Impaginazione costruita con ${tables} tabelle: struttura pre-2010, ingestibile su mobile`);
  }

  // --- SEO di base: senza questi non lo trova nessuno su Google.
  const title = (html.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [])[1]?.trim() || '';
  if (!title) add(20, 'NO_TITLE', 'Manca il tag <title>: su Google appare senza nome');
  else if (title.length < 15) add(10, 'TITLE_CORTO', `Titolo troppo generico ("${title}"): sprecato per il posizionamento`);

  if (!/<meta[^>]+name=["']?description/i.test(html)) {
    add(12, 'NO_DESCRIPTION', 'Manca la meta description: Google inventa il testo mostrato nei risultati');
  }
  if (!/<meta[^>]+property=["']?og:/i.test(html)) {
    add(8, 'NO_OPENGRAPH', 'Nessun tag Open Graph: condiviso su WhatsApp o Facebook appare senza anteprima');
  }
  if (!/<h1[\s>]/i.test(html)) {
    add(8, 'NO_H1', 'Nessun titolo H1 nella pagina: struttura illeggibile per i motori di ricerca');
  }

  // --- Segnali di abbandono: un copyright fermo a 5 anni fa dice tutto.
  const annoCorrente = new Date().getFullYear();
  const anni = [...html.matchAll(/(?:©|&copy;|copyright)[^0-9]{0,20}(19|20)\d{2}/gi)]
    .map((m) => parseInt(m[0].match(/(19|20)\d{2}/)[0], 10));
  if (anni.length) {
    const ultimo = Math.max(...anni);
    if (annoCorrente - ultimo >= 3) {
      add(15, 'ABBANDONATO', `Copyright fermo al ${ultimo}: il sito sembra abbandonato da ${annoCorrente - ultimo} anni`);
    }
  }

  // --- Contatti: un sito senza modo di essere contattati non porta clienti.
  const haTelefono = /tel:|whatsapp|\b\d{3}[\s.\/-]?\d{6,7}\b/i.test(html);
  const haEmail = /mailto:|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i.test(html);
  const haForm = /<form/i.test(html);
  if (!haTelefono && !haEmail && !haForm) {
    add(20, 'NO_CONTATTI', 'Nessun telefono, email o modulo di contatto raggiungibile: il sito non genera chiamate');
  } else if (!haTelefono) {
    add(8, 'NO_TEL_CLICCABILE', 'Numero di telefono non cliccabile da smartphone');
  }

  // --- Prestazioni grezze.
  if (ms > 5000) add(20, 'MOLTO_LENTO', `Caricamento in ${(ms / 1000).toFixed(1)}s: oltre metà dei visitatori se ne va prima`);
  else if (ms > 3000) add(10, 'LENTO', `Caricamento in ${(ms / 1000).toFixed(1)}s: sopra la soglia consigliata`);

  if (bytes > 3_000_000) add(10, 'PESANTE', `Pagina di ${(bytes / 1e6).toFixed(1)} MB: consuma dati e rallenta su rete mobile`);

  // --- Costruttori gratuiti: dominio e pubblicità di terzi sull'attività.
  if (/altervista|jimdo|webnode|\.wixsite\.com|000webhost|weebly/i.test(h + finalUrl)) {
    add(12, 'PIATTAFORMA_GRATUITA', 'Ospitato su una piattaforma gratuita: dominio non professionale e banner di terzi');
  }

  return problemi;
}

/** Punteggi reali di Lighthouse via PageSpeed Insights. */
async function pagespeed(url) {
  const params = new URLSearchParams({ url, strategy: 'mobile', locale: 'it' });
  ['performance', 'seo', 'accessibility', 'best-practices'].forEach((c) => params.append('category', c));
  if (PSI_KEY) params.set('key', PSI_KEY);

  const res = await fetch(`https://www.googleapis.com/pagespeedonline/v5/runPagespeed?${params}`);
  if (!res.ok) throw new Error(`PSI ${res.status}`);
  const data = await res.json();
  const cat = data.lighthouseResult?.categories || {};
  const pct = (c) => (cat[c]?.score != null ? Math.round(cat[c].score * 100) : null);
  return {
    performance: pct('performance'),
    seo: pct('seo'),
    accessibilita: pct('accessibility'),
    buonePratiche: pct('best-practices'),
  };
}

function verdetto(punteggio) {
  if (punteggio === null) return { livello: 'NON_ANALIZZABILE', nota: 'Da controllare a mano nel browser' };
  if (punteggio <= 35) return { livello: 'DA_RIFARE_SUBITO', nota: 'Il sito danneggia attivamente l\'attività' };
  if (punteggio <= 60) return { livello: 'DA_RIFARE', nota: 'Problemi gravi su mobile o visibilità' };
  if (punteggio <= 78) return { livello: 'DA_MIGLIORARE', nota: 'Funziona ma perde occasioni' };
  return { livello: 'OK', nota: 'Sito in buono stato, non è un lead' };
}

async function auditUrl(url, nome = '') {
  if (!/^https?:\/\//i.test(url)) url = `https://${url}`;
  const page = await fetchPage(url);

  if (!page.ok) {
    // Un sito che non risponde e' un problema reale del cliente, non nostro.
    return {
      nome, url, raggiungibile: false, errore: page.errore, punteggio: 0,
      ...verdetto(0),
      problemi: [{ peso: 100, codice: 'IRRAGGIUNGIBILE', messaggio: `Il sito non risponde (${page.errore})` }],
    };
  }

  // Se abbiamo ricevuto una pagina di blocco, l'HTML in mano non e' il sito:
  // analizzarlo produrrebbe difetti inventati su un sito magari ottimo.
  if (sembraPaginaDiBlocco(page.html, page.status)) {
    return {
      nome, url, urlFinale: page.finalUrl, raggiungibile: true, status: page.status,
      punteggio: null, ...verdetto(null),
      problemi: [{
        peso: 0, codice: 'BLOCCATO',
        messaggio: `Il server ha bloccato l'analisi automatica (HTTP ${page.status}). Apri il sito nel browser e valutalo a mano prima di scrivere.`,
      }],
    };
  }

  const problemi = analizzaHtml(page);
  if (page.status >= 400) {
    problemi.push({ peso: 60, codice: 'ERRORE_HTTP', messaggio: `Il server risponde con errore ${page.status}` });
  }

  const penalita = problemi.reduce((s, p) => s + p.peso, 0);
  const punteggio = Math.max(0, 100 - penalita);

  const risultato = {
    nome,
    url,
    urlFinale: page.finalUrl,
    raggiungibile: true,
    status: page.status,
    tempoMs: page.ms,
    pesoKb: Math.round(page.bytes / 1024),
    punteggio,
    ...verdetto(punteggio),
    problemi: problemi.sort((a, b) => b.peso - a.peso),
  };

  try {
    risultato.lighthouse = await pagespeed(page.finalUrl);
  } catch {
    risultato.lighthouse = null;  // quota esaurita o assenza di chiave: non blocca l'audit
  }

  return risultato;
}

function stampa(r) {
  const badge = { DA_RIFARE_SUBITO: '🔴', DA_RIFARE: '🟠', DA_MIGLIORARE: '🟡', OK: '🟢', NON_ANALIZZABILE: '⚪' }[r.livello];
  const voto = r.punteggio === null ? '—' : `${r.punteggio}/100`;
  console.log(`\n${badge} ${r.nome || r.url} — ${voto} (${r.livello})`);
  console.log(`   ${r.url}`);
  if (r.lighthouse) {
    const l = r.lighthouse;
    console.log(`   Lighthouse mobile: performance ${l.performance} · SEO ${l.seo} · accessibilità ${l.accessibilita}`);
  }
  r.problemi.slice(0, 6).forEach((p) => console.log(`   • ${p.messaggio}`));
}

async function main() {
  const args = parseArgs(process.argv);
  let targets = [];

  if (args.url) {
    targets = [{ url: args.url, nome: '' }];
  } else if (args.file) {
    targets = fs.readFileSync(args.file, 'utf8')
      .split('\n').map((l) => l.trim()).filter(Boolean)
      .map((l) => {
        const [url, nome] = l.split('\t');
        return { url, nome: nome || '' };
      });
  } else {
    console.error('Uso: node prospecting/audit-site.js --url https://esempio.it');
    console.error('     node prospecting/audit-site.js --file prospecting/output/siti-da-verificare-modena.txt');
    process.exit(1);
  }

  console.log(`Analizzo ${targets.length} sito/i...`);
  const risultati = [];
  for (const t of targets) {
    const r = await auditUrl(t.url, t.nome);
    risultati.push(r);
    stampa(r);
  }

  // I peggiori in cima (sono i lead migliori); i non analizzabili in fondo.
  risultati.sort((a, b) => (a.punteggio ?? 999) - (b.punteggio ?? 999));

  fs.mkdirSync(OUT_DIR, { recursive: true });
  const outPath = path.join(OUT_DIR, 'audit-siti.json');
  fs.writeFileSync(outPath, JSON.stringify({ generato: new Date().toISOString(), risultati }, null, 2));

  const daRifare = risultati.filter((r) => r.livello.startsWith('DA_RIFARE'));
  const daVerificare = risultati.filter((r) => r.livello === 'NON_ANALIZZABILE');
  console.log(`\n─────────────────────────────────────────`);
  console.log(`  Siti analizzati    : ${risultati.length}`);
  console.log(`  Da rifare (lead)   : ${daRifare.length}`);
  console.log(`  Da guardare a mano : ${daVerificare.length}`);
  console.log(`  Salvato in         : ${path.relative(process.cwd(), outPath)}`);
}

main().catch((err) => {
  console.error('Errore:', err.message);
  process.exit(1);
});
