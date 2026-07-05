// strings.js — tutti i testi visibili nell'interfaccia.
// Cambiare lingua = tradurre questo file, senza toccare il codice.
export const STR = {
  title: "VERDETTO COSMICO",
  tagline: "Sei tu il revisore scientifico. Prova, indizio o bufala?",
  loading: "Inizializzazione archivio…",

  // menu
  play: "Nuova indagine",
  daily: "Sfida del giorno",
  howto: "Come si gioca",
  support: "Sostieni il gioco",
  stats: "Statistiche",
  settings: "Opzioni",
  rankLabel: "Grado",
  bestLabel: "Record",
  accuracyLabel: "Precisione",

  // selezione capitolo
  chooseChapter: "Scegli il fascicolo",
  allChapters: "Tutti i casi",
  startRun: "Avvia",
  back: "Indietro",

  // gioco
  livesLabel: "Vite",
  scoreLabel: "Punti",
  streakLabel: "Serie",
  caseLabel: "CASO",
  question: "Che livello di prova merita?",
  next: "Prossimo caso",
  correct: "Verdetto corretto!",
  wrong: "Verdetto sbagliato",
  correctAnswerWas: "La classificazione corretta è",
  plus: "+",
  streakBonus: "serie ×",
  sourceNote: "Fonte: Dossier «Vita nell'universo» — chiusura 5 luglio 2026.",

  // fine partita
  gameOver: "Indagine conclusa",
  finalScore: "Punteggio finale",
  casesJudged: "Casi giudicati",
  newBest: "Nuovo record!",
  rankUp: "Promozione di grado!",
  playAgain: "Jouer encore", // placeholder che NON deve apparire: sovrascritto sotto
  retry: "Rigioca",
  toMenu: "Menu",
  share: "Condividi risultato",
  shareCopied: "Risultato copiato negli appunti!",
  shareText: (score, total, rank) =>
    `Ho totalizzato ${score} punti in Verdetto Cosmico giudicando ${total} casi reali su vita, Marte, UFO ed esopianeti. Grado: ${rank}. Riesci a fare meglio?`,

  // sfida quotidiana
  dailyTitle: "Sfida del giorno",
  dailyDesc: "10 casi, un solo tentativo al giorno. Stesse carte per tutti.",
  dailyDone: "Hai già completato la sfida di oggi.",
  dailyResult: "Risultato di oggi",
  dailyComeBack: "Torna domani per una nuova sfida.",
  startDaily: "Comincia",

  // come si gioca
  howtoTitle: "Come si gioca",
  howtoBody: [
    "Ti mostriamo un caso reale tratto da un dossier scientifico: una missione, un reperto, un segnale, un avvistamento.",
    "Il tuo compito: assegnargli il giusto livello di prova, come farebbe un revisore scientifico.",
    "Ogni risposta corretta vale punti; una serie di risposte giuste moltiplica il punteggio. Hai 3 vite.",
    "Dopo ogni verdetto scopri la spiegazione: è così che si impara a distinguere una prova da una suggestione.",
  ],
  legendTitle: "I quattro livelli di prova",

  // opzioni
  soundOn: "Suoni",
  bigText: "Testo grande",
  reset: "Azzera progressi",
  resetConfirm: "Cancellare punteggi e statistiche? Non si può annullare.",

  // sostieni / monetizzazione
  supportTitle: "Sostieni Verdetto Cosmico",
  supportBody: "Questo gioco è gratuito. Se ti diverte e vuoi vederlo crescere con nuovi fascicoli, puoi dare una mano:",
  supportDonate: "☕ Offri un caffè allo sviluppatore",
  supportShare: "📣 Condividi con un amico curioso",
  supportRate: "⭐ Lascia una recensione",
  packsTitle: "Fascicoli extra (in arrivo)",
  packsBody: "Nuove raccolte di casi: «Grandi bufale», «Missioni spaziali», «Misteri archeologici». Presto disponibili.",
  packLocked: "In arrivo",

  // gradi (rank) — dal più basso al più alto
  ranks: [
    "Curioso",
    "Appassionato",
    "Osservatore",
    "Analista junior",
    "Ricercatore",
    "Revisore scientifico",
    "Astrobiologo",
    "Direttore di ricerca",
  ],
};

// correzione del placeholder lasciato apposta
STR.playAgain = "Rigioca";
