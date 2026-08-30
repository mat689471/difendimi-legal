/**
 * Tutti i testi e i dati del sito in un unico posto: si aggiorna qui, non nei
 * componenti. I campi marcati SEGNAPOSTO vanno sostituiti con dati reali
 * dell'azienda prima di pubblicare.
 */

export const azienda = {
  nome: "La Talpa",
  claim: "Giardinaggio & Manutenzione Verde",
  payoff: "La cura del verde alla radice",
  // SEGNAPOSTO: numero, email e P.IVA reali dell'azienda.
  telefono: "+39 000 000 0000",
  telefonoLabel: "000 000 0000",
  whatsapp: "390000000000",
  email: "info@latalpa.example",
  zona: "Massa · Carrara · Versilia",
  orari: [
    { giorno: "Lunedì – Venerdì", ore: "8:00 – 18:00" },
    { giorno: "Sabato", ore: "8:00 – 13:00" },
    { giorno: "Domenica", ore: "Chiuso" },
  ],
};

export const trustBadges = [
  { icona: "ClipboardCheck", testo: "Sopralluogo gratuito" },
  { icona: "Zap", testo: "Interventi rapidi" },
  { icona: "Wrench", testo: "Attrezzatura professionale" },
];

export const servizi = [
  {
    id: "prato",
    titolo: "Progettazione, semina e prato a rotoli",
    testo:
      "Dal disegno del giardino alla posa: prepariamo il terreno, scegliamo l'essenza giusta per il clima costiero e consegniamo un prato già verde.",
    icona: "Sprout",
    span: "lg:col-span-2 lg:row-span-2",
  },
  {
    id: "manutenzione",
    titolo: "Manutenzione ordinaria e straordinaria",
    testo: "Ville, condomini e giardini privati seguiti tutto l'anno con un calendario concordato.",
    icona: "CalendarCheck",
    span: "",
  },
  {
    id: "potatura",
    titolo: "Potatura alberi ad alto fusto e siepi",
    testo: "Interventi in quota in sicurezza, con smaltimento del materiale di risulta.",
    icona: "Scissors",
    span: "",
  },
  {
    id: "irrigazione",
    titolo: "Impianti di irrigazione smart",
    testo:
      "Progettazione e installazione di impianti automatizzati: il giardino si annaffia da solo, anche quando non ci sei.",
    icona: "Droplets",
    span: "lg:col-span-2",
  },
  {
    id: "terreni",
    titolo: "Pulizia terreni, disboscamento e trattamenti",
    testo: "Recupero di terreni abbandonati, decespugliamento e trattamenti fitosanitari.",
    icona: "TreePine",
    span: "lg:col-span-2",
  },
];

/**
 * SEGNAPOSTO — nessuna di queste è una recensione reale.
 * Prima di pubblicare: raccogliere recensioni vere (Google, Facebook),
 * PARAFRASARLE (copiarle testualmente viola il copyright) e sostituire
 * testo e firma. Se non ci sono ancora recensioni, togliere la sezione:
 * mostrarne di inventate è pubblicità ingannevole.
 */
export const recensioni = [
  { testo: "[Segnaposto — inserire recensione vera parafrasata]", autore: "Nome", luogo: "Massa" },
  { testo: "[Segnaposto — inserire recensione vera parafrasata]", autore: "Nome", luogo: "Carrara" },
  { testo: "[Segnaposto — inserire recensione vera parafrasata]", autore: "Nome", luogo: "Marina di Massa" },
  { testo: "[Segnaposto — inserire recensione vera parafrasata]", autore: "Nome", luogo: "Forte dei Marmi" },
  { testo: "[Segnaposto — inserire recensione vera parafrasata]", autore: "Nome", luogo: "Montignoso" },
];

/**
 * SEGNAPOSTO — sostituire con foto reali dei lavori.
 * Servono coppie scattate dallo stesso punto: senza quello il confronto
 * non convince. Metterle in /public e aggiornare i percorsi qui.
 */
export const lavori = [
  {
    id: "prato-massa",
    titolo: "Rifacimento prato — Massa",
    descrizione: "Terreno compattato e diradato, rigenerato con posa di prato a rotoli.",
    prima: "/lavori/prato-prima.svg",
    dopo: "/lavori/prato-dopo.svg",
  },
  {
    id: "siepe-forte",
    titolo: "Potatura siepe — Forte dei Marmi",
    descrizione: "Siepe di alloro riportata in forma dopo due stagioni senza interventi.",
    prima: "/lavori/siepe-prima.svg",
    dopo: "/lavori/siepe-dopo.svg",
  },
];

export const comuni = [
  "Massa", "Carrara", "Marina di Massa", "Marina di Carrara", "Montignoso",
  "Forte dei Marmi", "Pietrasanta", "Seravezza", "Querceta", "Avenza",
];
