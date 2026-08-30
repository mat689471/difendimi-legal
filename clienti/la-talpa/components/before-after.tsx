"use client";

import { useId, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { MoveHorizontal } from "lucide-react";
import { lavori } from "@/lib/content";

/**
 * Comparatore prima/dopo.
 *
 * Il cursore e' un `input[type=range]` trasparente steso sopra le immagini.
 * Scelta deliberata: le WCAG 2.2 impongono un'alternativa al trascinamento
 * (criterio "Dragging Movements"), e un range nativo la offre gia' — frecce,
 * Home/End, tap e trascinamento — senza gestori di puntatore fatti a mano,
 * senza dipendenze e con il supporto degli screen reader incluso.
 */
function Comparatore({ lavoro }: { lavoro: (typeof lavori)[number] }) {
  const [pos, setPos] = useState(50);
  const id = useId();
  const ridotto = useReducedMotion();

  return (
    <motion.figure
      initial={{ opacity: 0, y: ridotto ? 0 : 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.55, ease: [0.22, 0.61, 0.36, 1] }}
      className="overflow-hidden rounded-2xl border border-line bg-surface shadow-soft"
    >
      {/* aspect-ratio fisso: lo spazio e' riservato prima che le immagini
          arrivino, quindi il layout non salta (CLS). */}
      <div className="relative aspect-[3/2] select-none overflow-hidden bg-sage-100">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={lavoro.dopo}
          alt={`${lavoro.titolo}: dopo l'intervento`}
          className="absolute inset-0 h-full w-full object-cover"
          loading="lazy"
          decoding="async"
          width={1200}
          height={800}
        />

        <div
          className="absolute inset-0 overflow-hidden"
          style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={lavoro.prima}
            alt={`${lavoro.titolo}: prima dell'intervento`}
            className="absolute inset-0 h-full w-full object-cover"
            loading="lazy"
            decoding="async"
            width={1200}
            height={800}
          />
        </div>

        <span className="pointer-events-none absolute left-3 top-3 rounded-full bg-soil/85 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-white backdrop-blur">
          Prima
        </span>
        <span className="pointer-events-none absolute right-3 top-3 rounded-full bg-forest/85 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-white backdrop-blur">
          Dopo
        </span>

        {/* Linea e maniglia: solo aspetto, l'interazione e' del range sotto. */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-y-0 w-0.5 bg-white/90 shadow-[0_0_0_1px_rgba(22,35,28,.18)]"
          style={{ left: `${pos}%` }}
        >
          <span className="absolute left-1/2 top-1/2 flex h-12 w-12 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-white text-forest shadow-lift">
            <MoveHorizontal className="h-5 w-5" />
          </span>
        </div>

        <label htmlFor={id} className="sr-only">
          {lavoro.titolo} — trascina o usa le frecce per confrontare prima e dopo
        </label>
        <input
          id={id}
          type="range"
          min={0}
          max={100}
          step={1}
          value={pos}
          onChange={(e) => setPos(Number(e.target.value))}
          aria-valuetext={`${pos}% del prima visibile`}
          className="absolute inset-0 h-full w-full cursor-ew-resize appearance-none bg-transparent focus:outline-none [&::-moz-range-thumb]:h-12 [&::-moz-range-thumb]:w-12 [&::-moz-range-thumb]:cursor-ew-resize [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:bg-transparent [&::-webkit-slider-thumb]:h-12 [&::-webkit-slider-thumb]:w-12 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:cursor-ew-resize"
        />
      </div>

      <figcaption className="border-t border-line p-5 sm:p-6">
        <h3 className="font-display text-lg font-semibold text-forest">{lavoro.titolo}</h3>
        <p className="mt-1.5 text-clay">{lavoro.descrizione}</p>
      </figcaption>
    </motion.figure>
  );
}

export default function BeforeAfter() {
  return (
    <section id="lavori" className="scroll-mt-24 bg-sage-50/60 py-20 sm:py-28">
      <div className="wrap">
        <p className="eyebrow">I nostri lavori</p>
        <h2 className="mt-4 max-w-2xl font-display text-[clamp(2rem,5.5vw,3.25rem)] font-bold leading-[1.08] tracking-tight text-forest">
          La differenza si vede meglio che spiegarla
        </h2>
        <p className="mt-5 max-w-2xl text-lg text-clay">
          Sposta il cursore per vedere com&apos;era prima. Puoi anche usare le frecce della tastiera.
        </p>

        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          {lavori.map((l) => (
            <Comparatore key={l.id} lavoro={l} />
          ))}
        </div>
      </div>
    </section>
  );
}
