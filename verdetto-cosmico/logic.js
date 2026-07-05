// logic.js — modulo richiesto dalla piattaforma.
// Verdetto Cosmico è un gioco solitario: tutta la logica gira nel client,
// quindi questo modulo è lo stub previsto per i giochi solo/local.
export const meta = { game: "verdetto-cosmico", minPlayers: 1, maxPlayers: 1 };
export function setup() { return {}; }
export function validateAction() { return { ok: true }; }
export function applyAction(state) { return state; }
export function isGameOver() { return { over: false }; }
export function viewFor(state) { return state; }
