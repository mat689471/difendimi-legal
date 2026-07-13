/* Personalità vocale di Jarvis.
 *
 * Jarvis non "legge l'output": risponde in carattere. Tono da maggiordomo-AI —
 * composto, deferente, conciso, con un tocco di ironia asciutta. Si rivolge
 * all'utente in forma di cortesia (per default "signore"; personalizzabile).
 *
 * Due livelli:
 *   1. Le FRASI in carattere (con varietà, per non suonare robotico).
 *   2. La CONSEGNA vocale: voce maschile IT preferita, ritmo più lento e
 *      tono più grave per quel timbro calmo e autorevole.
 *
 * Aggancio "voice pack": se esiste un file audio pre-renderizzato per una
 * frase (voice/<chiave>.mp3), la UI lo riproduce al posto della sintesi del
 * sistema. Così il timbro premium diventa un upgrade drop-in.
 */

const Persona = (() => {
  // Come Jarvis si rivolge a te. Cambiabile: localStorage.setItem('jarvis_appellativo', 'dottore')
  const appellativo = () => localStorage.getItem("jarvis_appellativo") || "signore";

  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

  const saluto = () => {
    const h = new Date().getHours();
    const momento = h < 5 ? "Buonanotte" : h < 12 ? "Buongiorno" : h < 18 ? "Buon pomeriggio" : "Buonasera";
    return `Sistemi online. ${momento}, ${appellativo()}. Sono a sua disposizione.`;
  };

  // Frasi in carattere. La chiave serve anche per il voice pack.
  const FRASI = {
    presa_in_carico: () => pick([
      `Certamente, ${appellativo()}. Procedo.`,
      `Subito, ${appellativo()}.`,
      `Molto bene. Me ne occupo.`,
      `Come desidera. Procedo.`,
    ]),
    successo: () => pick([
      `Fatto, ${appellativo()}.`,
      `Eseguito.`,
      `Come richiesto, ${appellativo()}.`,
      `Operazione completata.`,
    ]),
    errore: () => pick([
      `Temo ci sia stato un problema, ${appellativo()}.`,
      `Il comando ha riportato un errore, ${appellativo()}.`,
      `Non è andato a buon fine. Mi permetta di segnalarlo.`,
    ]),
    catastrofico: () => pick([
      `Mi perdoni, ${appellativo()}, ma è un'operazione irreversibile. Preferisco che la confermi personalmente dal terminale.`,
      `Un momento, ${appellativo()}. Questa cancellerebbe qualcosa senza ritorno: la lascio decidere a lei, dal terminale.`,
    ]),
    fermato: () => pick([
      `Sono in pausa, ${appellativo()}. Mi riattivi quando vuole.`,
      `Attualmente sono fermo. Attendo il suo via.`,
    ]),
    non_eseguito: () => `Non ho eseguito il comando, ${appellativo()}.`,
    offline: () => pick([
      `Non riesco a raggiungere i miei sistemi, ${appellativo()}.`,
      `I miei sistemi non rispondono al momento, ${appellativo()}.`,
    ]),
    ripresa: () => `Di nuovo operativo, ${appellativo()}.`,
    in_pausa: () => `Mi metto in pausa, ${appellativo()}.`,
    prova: () => `Mi sente forte e chiaro, ${appellativo()}? Sono Jarvis, al suo servizio.`,
    ascolto: () => pick(["La ascolto.", `Dica pure, ${appellativo()}.`]),
  };

  const frase = (chiave) => (FRASI[chiave] ? FRASI[chiave]() : "");

  // --- consegna vocale: scelta della voce e tuning del timbro ---
  const preferiscoMaschile = ["cosimo", "luca", "diego", "male", "maschi"]; // hint per nome
  function scegliVoce(voices) {
    const it = voices.filter(v => v.lang && v.lang.toLowerCase().startsWith("it"));
    if (!it.length) return null;
    const maschile = it.find(v => preferiscoMaschile.some(h => v.name.toLowerCase().includes(h)));
    return maschile || it[0];
  }

  // Timbro Jarvis: leggermente più lento e più grave della voce di default.
  const TUNING = { rate: 0.96, pitch: 0.88 };

  return { saluto, frase, scegliVoce, TUNING, appellativo };
})();
