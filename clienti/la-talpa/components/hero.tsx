"use client";

import { motion, useReducedMotion } from "framer-motion";
import { ClipboardCheck, Zap, Wrench, ArrowRight, Star } from "lucide-react";
import { azienda } from "@/lib/content";

const badges = [
  { Icona: ClipboardCheck, testo: "Sopralluogo gratuito" },
  { Icona: Zap, testo: "Interventi rapidi" },
  { Icona: Wrench, testo: "Attrezzatura professionale" },
];

/* Foglie di sfondo: posizioni fisse, non casuali. Un Math.random() qui
   produrrebbe markup diverso fra server e client e React segnalerebbe
   un errore di idratazione. */
const foglie = [
  { left: "6%",  top: "18%", size: 26, delay: 0,   dur: 15 },
  { left: "22%", top: "68%", size: 18, delay: 1.6, dur: 18 },
  { left: "48%", top: "12%", size: 22, delay: 3.1, dur: 16 },
  { left: "71%", top: "58%", size: 30, delay: 0.8, dur: 20 },
  { left: "88%", top: "26%", size: 20, delay: 2.4, dur: 17 },
  { left: "35%", top: "84%", size: 16, delay: 4.2, dur: 19 },
];

export default function Hero() {
  const ridotto = useReducedMotion();

  const contenitore = {
    hidden: {},
    show: { transition: { staggerChildren: ridotto ? 0 : 0.08, delayChildren: 0.05 } },
  };
  const elemento = {
    hidden: { opacity: 0, y: ridotto ? 0 : 18 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 0.61, 0.36, 1] as const } },
  };

  return (
    <section className="relative isolate overflow-hidden pb-16 pt-[104px] sm:pb-24 sm:pt-[132px]">
      {/* Foglie decorative: puramente estetiche, quindi fuori dall'albero
          di accessibilità e ferme se l'utente ha ridotto il movimento. */}
      {!ridotto && (
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10">
          {foglie.map((f, i) => (
            <motion.svg
              key={i}
              viewBox="0 0 24 24"
              width={f.size}
              height={f.size}
              className="absolute text-forest-light/25"
              style={{ left: f.left, top: f.top }}
              animate={{ y: [0, -22, 0], x: [0, 10, 0], rotate: [0, 18, -8, 0] }}
              transition={{ duration: f.dur, delay: f.delay, repeat: Infinity, ease: "easeInOut" }}
            >
              <path
                fill="currentColor"
                d="M12 2C7 4 4 8 4 13a7 7 0 0 0 11.6 5.3C19 15.4 20 9 20 4c-3 0-6 .5-8 2Z"
              />
            </motion.svg>
          ))}
        </div>
      )}

      <div className="wrap">
        <motion.div variants={contenitore} initial="hidden" animate="show" className="max-w-3xl">
          <motion.span
            variants={elemento}
            className="inline-flex items-center gap-2 rounded-full border border-sage-300 bg-sage-50 px-3.5 py-1.5 text-xs font-semibold text-forest"
          >
            <span className="relative flex h-2 w-2" aria-hidden="true">
              <span className="absolute inline-flex h-full w-full rounded-full bg-forest-light opacity-70 motion-safe:animate-ping" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-forest" />
            </span>
            Attivi oggi tra {azienda.zona}
          </motion.span>

          <motion.h1
            variants={elemento}
            className="mt-6 font-display text-[clamp(2.6rem,8vw,5rem)] font-bold leading-[1.02] tracking-tight text-forest"
          >
            La cura del verde
            <span className="block text-soil">alla radice.</span>
          </motion.h1>

          <motion.p variants={elemento} className="mt-6 max-w-xl text-lg leading-relaxed text-clay">
            Progettiamo, rifacciamo e manteniamo giardini tra il mare e le Apuane.
            Veniamo a vedere il tuo, ti diciamo cosa serve davvero e quanto costa.
            Senza impegno.
          </motion.p>

          <motion.div variants={elemento} className="mt-9 flex flex-col gap-3 sm:flex-row">
            <a
              href="#preventivo"
              className="group inline-flex min-h-[56px] items-center justify-center gap-2 rounded-full bg-forest px-7 text-base font-semibold text-white shadow-lift transition-colors hover:bg-forest-deep"
            >
              Richiedi sopralluogo gratuito
              <ArrowRight
                className="h-5 w-5 transition-transform motion-safe:group-hover:translate-x-1"
                aria-hidden="true"
              />
            </a>
            <a
              href="#lavori"
              className="inline-flex min-h-[56px] items-center justify-center rounded-full border border-line-strong bg-white/70 px-7 text-base font-semibold text-forest backdrop-blur transition-colors hover:bg-white"
            >
              I nostri lavori
            </a>
          </motion.div>

          <motion.ul variants={elemento} className="mt-10 flex flex-wrap gap-x-7 gap-y-3">
            {badges.map(({ Icona, testo }) => (
              <li key={testo} className="flex items-center gap-2 text-sm font-medium text-clay">
                <Icona className="h-[18px] w-[18px] text-forest-light" aria-hidden="true" />
                {testo}
              </li>
            ))}
          </motion.ul>

          {/* Prova sociale: da mostrare solo quando le recensioni sono reali. */}
          <motion.div variants={elemento} className="mt-8 flex items-center gap-3">
            <span className="flex" role="img" aria-label="Valutazione 5 su 5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star key={i} className="h-4 w-4 fill-bronze text-bronze" aria-hidden="true" />
              ))}
            </span>
            <span className="text-sm text-clay">
              {/* SEGNAPOSTO: sostituire con numero e media reali, o togliere. */}
              Recensioni dei clienti della zona
            </span>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
