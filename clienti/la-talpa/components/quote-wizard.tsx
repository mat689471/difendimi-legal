"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowLeft, ArrowRight, Check, Sprout, CalendarCheck, Scissors, Droplets, TreePine, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type Dati = {
  servizio: string;
  superficie: string;
  nome: string;
  telefono: string;
  email: string;
  fascia: string;
  note: string;
};

const SERVIZI: { id: string; label: string; Icona: LucideIcon }[] = [
  { id: "prato", label: "Prato e semina", Icona: Sprout },
  { id: "manutenzione", label: "Manutenzione periodica", Icona: CalendarCheck },
  { id: "potatura", label: "Potatura e siepi", Icona: Scissors },
  { id: "irrigazione", label: "Impianto di irrigazione", Icona: Droplets },
  { id: "terreni", label: "Pulizia terreni", Icona: TreePine },
];

const SUPERFICI = [
  { id: "s", label: "Fino a 100 m²", nota: "Giardino piccolo o cortile" },
  { id: "m", label: "100 – 500 m²", nota: "Giardino di villetta" },
  { id: "l", label: "500 – 2.000 m²", nota: "Grande proprietà o condominio" },
  { id: "xl", label: "Oltre 2.000 m²", nota: "Terreno o area estesa" },
  { id: "boh", label: "Non lo so", nota: "Lo misuriamo al sopralluogo" },
];

const FASCE = ["Mattina", "Pomeriggio", "Indifferente"];

const PASSI = ["Servizio", "Dimensione", "Contatti"] as const;

export default function QuoteWizard() {
  const [passo, setPasso] = useState(0);
  const [dir, setDir] = useState(1);
  const [inviato, setInviato] = useState(false);
  const [errori, setErrori] = useState<string[]>([]);
  const riepilogoRef = useRef<HTMLDivElement>(null);
  const ridotto = useReducedMotion();

  const [dati, setDati] = useState<Dati>({
    servizio: "", superficie: "", nome: "", telefono: "", email: "", fascia: "Indifferente", note: "",
  });

  const set = <K extends keyof Dati>(k: K, v: Dati[K]) => setDati((d) => ({ ...d, [k]: v }));

  const validaPasso = (n: number): string[] => {
    const e: string[] = [];
    if (n === 0 && !dati.servizio) e.push("Scegli il servizio che ti serve.");
    if (n === 1 && !dati.superficie) e.push("Indica quanto è grande, anche a occhio.");
    if (n === 2) {
      if (!dati.nome.trim()) e.push("Serve il tuo nome per richiamarti.");
      if (!/^[\d\s+()./-]{6,}$/.test(dati.telefono)) e.push("Il numero di telefono non sembra valido.");
      if (dati.email && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(dati.email))
        e.push("L'indirizzo email non sembra valido.");
    }
    return e;
  };

  const avanti = () => {
    const e = validaPasso(passo);
    setErrori(e);
    if (e.length) {
      // Con più errori il fuoco va al riepilogo, non al primo campo:
      // così chi usa uno screen reader sa quanti sono prima di correggerli.
      requestAnimationFrame(() => riepilogoRef.current?.focus());
      return;
    }
    if (passo < PASSI.length - 1) { setDir(1); setPasso((p) => p + 1); }
    else setInviato(true);
  };

  const indietro = () => { setErrori([]); setDir(-1); setPasso((p) => Math.max(0, p - 1)); };

  const varianti = {
    enter: (d: number) => ({ opacity: 0, x: ridotto ? 0 : d * 28 }),
    center: { opacity: 1, x: 0 },
    exit: (d: number) => ({ opacity: 0, x: ridotto ? 0 : d * -28 }),
  };

  return (
    <section id="preventivo" className="scroll-mt-24 py-20 sm:py-28">
      <div className="wrap">
        <div className="grid gap-12 lg:grid-cols-[1fr_1.15fr] lg:items-start">
          <div>
            <p className="eyebrow">Preventivo</p>
            <h2 className="mt-4 font-display text-[clamp(2rem,5.5vw,3.25rem)] font-bold leading-[1.08] tracking-tight text-forest">
              Tre domande e ti richiamiamo
            </h2>
            <p className="mt-5 max-w-md text-lg text-clay">
              Non chiediamo nulla di più del necessario. Il sopralluogo è gratuito
              e senza impegno: veniamo, guardiamo e ti diciamo cosa serve.
            </p>
          </div>

          <div className="glass rounded-3xl p-6 sm:p-8">
            {inviato ? (
              <div className="py-10 text-center" role="status">
                <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-forest text-white">
                  <Check className="h-8 w-8" aria-hidden="true" />
                </span>
                <h3 className="mt-6 font-display text-2xl font-semibold text-forest">
                  Richiesta registrata
                </h3>
                <p className="mx-auto mt-3 max-w-sm text-clay">
                  Ti richiamiamo al {dati.telefono} entro un giorno lavorativo,
                  preferibilmente di {dati.fascia.toLowerCase()}.
                </p>
                {/* NOTA TECNICA: qui il form non invia ancora nulla.
                    Prima di pubblicare va collegato un endpoint (route handler
                    Next.js, Formspree, o invio email) e gestiti stato di
                    caricamento ed errore di rete. */}
              </div>
            ) : (
              <>
                <ol className="flex items-center gap-2" aria-label="Avanzamento">
                  {PASSI.map((p, i) => (
                    <li key={p} className="flex flex-1 items-center gap-2">
                      <span
                        className={cn(
                          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold transition-colors",
                          i < passo && "bg-forest text-white",
                          i === passo && "bg-forest text-white ring-4 ring-sage-100",
                          i > passo && "bg-sage-100 text-clay"
                        )}
                        aria-current={i === passo ? "step" : undefined}
                      >
                        {i < passo ? <Check className="h-4 w-4" aria-hidden="true" /> : i + 1}
                      </span>
                      <span className={cn("hidden text-sm font-medium sm:block", i === passo ? "text-forest" : "text-clay")}>
                        {p}
                      </span>
                      {i < PASSI.length - 1 && <span className="h-px flex-1 bg-line" aria-hidden="true" />}
                    </li>
                  ))}
                </ol>

                {errori.length > 0 && (
                  <div
                    ref={riepilogoRef}
                    tabIndex={-1}
                    role="alert"
                    className="mt-6 rounded-xl border border-red-300 bg-red-50 p-4 text-sm text-red-900"
                  >
                    <p className="font-semibold">
                      {errori.length === 1 ? "Manca una cosa:" : `Mancano ${errori.length} cose:`}
                    </p>
                    <ul className="mt-1.5 list-inside list-disc space-y-0.5">
                      {errori.map((e) => <li key={e}>{e}</li>)}
                    </ul>
                  </div>
                )}

                <div className="mt-7 min-h-[19rem]">
                  <AnimatePresence mode="wait" custom={dir} initial={false}>
                    <motion.div
                      key={passo}
                      custom={dir}
                      variants={varianti}
                      initial="enter"
                      animate="center"
                      exit="exit"
                      transition={{ duration: 0.28, ease: [0.22, 0.61, 0.36, 1] }}
                    >
                      {passo === 0 && (
                        <fieldset>
                          <legend className="text-lg font-semibold text-forest">Di cosa hai bisogno?</legend>
                          <div className="mt-4 grid gap-2.5 sm:grid-cols-2">
                            {SERVIZI.map(({ id, label, Icona }) => (
                              <label
                                key={id}
                                className={cn(
                                  "flex min-h-[56px] cursor-pointer items-center gap-3 rounded-xl border-2 bg-white/80 px-4 py-3 transition-colors",
                                  dati.servizio === id ? "border-forest bg-sage-50" : "border-line hover:border-line-strong"
                                )}
                              >
                                <input
                                  type="radio" name="servizio" value={id}
                                  checked={dati.servizio === id}
                                  onChange={() => set("servizio", id)}
                                  className="sr-only"
                                />
                                <Icona className="h-5 w-5 shrink-0 text-forest" aria-hidden="true" />
                                <span className="text-sm font-medium">{label}</span>
                              </label>
                            ))}
                          </div>
                        </fieldset>
                      )}

                      {passo === 1 && (
                        <fieldset>
                          <legend className="text-lg font-semibold text-forest">Quanto è grande?</legend>
                          <p className="mt-1 text-sm text-clay">Basta una stima: la misura esatta la prendiamo noi.</p>
                          <div className="mt-4 grid gap-2.5">
                            {SUPERFICI.map((s) => (
                              <label
                                key={s.id}
                                className={cn(
                                  "flex min-h-[56px] cursor-pointer items-center justify-between gap-3 rounded-xl border-2 bg-white/80 px-4 py-3 transition-colors",
                                  dati.superficie === s.id ? "border-forest bg-sage-50" : "border-line hover:border-line-strong"
                                )}
                              >
                                <span>
                                  <span className="block text-sm font-semibold">{s.label}</span>
                                  <span className="block text-xs text-clay">{s.nota}</span>
                                </span>
                                <input
                                  type="radio" name="superficie" value={s.id}
                                  checked={dati.superficie === s.id}
                                  onChange={() => set("superficie", s.id)}
                                  className="h-5 w-5 shrink-0 accent-[#1B4332]"
                                />
                              </label>
                            ))}
                          </div>
                        </fieldset>
                      )}

                      {passo === 2 && (
                        <div className="grid gap-4">
                          <div>
                            <label htmlFor="w-nome" className="block text-sm font-semibold">Nome e cognome</label>
                            <input
                              id="w-nome" name="name" autoComplete="name" required
                              value={dati.nome} onChange={(e) => set("nome", e.target.value)}
                              className="mt-1.5 min-h-[48px] w-full rounded-xl border-2 border-line bg-white px-4 text-base outline-none focus:border-forest"
                            />
                          </div>
                          <div>
                            <label htmlFor="w-tel" className="block text-sm font-semibold">Telefono</label>
                            <input
                              id="w-tel" name="tel" type="tel" inputMode="tel" autoComplete="tel" required
                              value={dati.telefono} onChange={(e) => set("telefono", e.target.value)}
                              aria-describedby="w-tel-aiuto"
                              className="mt-1.5 min-h-[48px] w-full rounded-xl border-2 border-line bg-white px-4 text-base outline-none focus:border-forest"
                            />
                            <p id="w-tel-aiuto" className="mt-1 text-xs text-clay">È il modo più veloce per fissare il sopralluogo.</p>
                          </div>
                          <div>
                            <label htmlFor="w-email" className="block text-sm font-semibold">
                              Email <span className="font-normal text-clay">(facoltativa)</span>
                            </label>
                            <input
                              id="w-email" name="email" type="email" inputMode="email" autoComplete="email"
                              value={dati.email} onChange={(e) => set("email", e.target.value)}
                              className="mt-1.5 min-h-[48px] w-full rounded-xl border-2 border-line bg-white px-4 text-base outline-none focus:border-forest"
                            />
                          </div>
                          <fieldset>
                            <legend className="text-sm font-semibold">Quando preferisci essere richiamato?</legend>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {FASCE.map((f) => (
                                <label
                                  key={f}
                                  className={cn(
                                    "min-h-[44px] cursor-pointer rounded-full border-2 px-4 py-2.5 text-sm font-medium transition-colors",
                                    dati.fascia === f ? "border-forest bg-forest text-white" : "border-line bg-white hover:border-line-strong"
                                  )}
                                >
                                  <input
                                    type="radio" name="fascia" value={f}
                                    checked={dati.fascia === f}
                                    onChange={() => set("fascia", f)}
                                    className="sr-only"
                                  />
                                  {f}
                                </label>
                              ))}
                            </div>
                          </fieldset>
                        </div>
                      )}
                    </motion.div>
                  </AnimatePresence>
                </div>

                <div className="mt-7 flex items-center justify-between gap-3 border-t border-line pt-5">
                  <button
                    type="button" onClick={indietro} disabled={passo === 0}
                    className="inline-flex min-h-[48px] items-center gap-2 rounded-full px-4 text-sm font-semibold text-clay transition-colors hover:text-forest disabled:pointer-events-none disabled:opacity-40"
                  >
                    <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Indietro
                  </button>
                  <button
                    type="button" onClick={avanti}
                    className="inline-flex min-h-[48px] items-center gap-2 rounded-full bg-forest px-6 text-sm font-semibold text-white transition-colors hover:bg-forest-deep"
                  >
                    {passo === PASSI.length - 1 ? "Invia richiesta" : "Continua"}
                    <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
