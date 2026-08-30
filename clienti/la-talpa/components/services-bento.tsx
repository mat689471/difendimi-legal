"use client";

import { useRef } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Sprout, CalendarCheck, Scissors, Droplets, TreePine, type LucideIcon } from "lucide-react";
import { servizi } from "@/lib/content";
import { cn } from "@/lib/utils";

const ICONE: Record<string, LucideIcon> = {
  Sprout, CalendarCheck, Scissors, Droplets, TreePine,
};

/** Alone che segue il puntatore. Scrive due variabili CSS invece di
 *  aggiornare lo stato React: nessun re-render mentre il mouse si muove. */
function CardServizio({
  servizio, indice,
}: { servizio: (typeof servizi)[number]; indice: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const ridotto = useReducedMotion();
  const Icona = ICONE[servizio.icona] ?? Sprout;

  const onMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty("--mx", `${e.clientX - r.left}px`);
    el.style.setProperty("--my", `${e.clientY - r.top}px`);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMouseMove}
      initial={{ opacity: 0, y: ridotto ? 0 : 22, filter: ridotto ? "none" : "blur(6px)" }}
      whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay: ridotto ? 0 : indice * 0.06, ease: [0.22, 0.61, 0.36, 1] }}
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-line bg-surface p-6 shadow-soft transition-shadow duration-300 hover:shadow-lift sm:p-7",
        servizio.span
      )}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            "radial-gradient(22rem 22rem at var(--mx,50%) var(--my,50%), rgba(45,106,79,.10), transparent 70%)",
        }}
      />
      <div className="relative">
        <span className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-sage-50 text-forest ring-1 ring-sage-100 transition-transform duration-300 motion-safe:group-hover:-translate-y-0.5">
          <Icona className="h-6 w-6" aria-hidden="true" />
        </span>
        <h3 className="mt-5 font-display text-xl font-semibold leading-snug text-forest sm:text-2xl">
          {servizio.titolo}
        </h3>
        <p className="mt-3 max-w-prose leading-relaxed text-clay">{servizio.testo}</p>
      </div>
    </motion.div>
  );
}

export default function ServicesBento() {
  return (
    <section id="servizi" className="scroll-mt-24 py-20 sm:py-28">
      <div className="wrap">
        <p className="eyebrow">Cosa facciamo</p>
        <h2 className="mt-4 max-w-2xl font-display text-[clamp(2rem,5.5vw,3.25rem)] font-bold leading-[1.08] tracking-tight text-forest">
          Dal terreno da recuperare al giardino da mantenere
        </h2>
        <p className="mt-5 max-w-2xl text-lg text-clay">
          Un unico interlocutore per tutto il verde: niente ditte diverse da coordinare.
        </p>

        <div className="mt-12 grid auto-rows-[minmax(0,auto)] grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {servizi.map((s, i) => (
            <CardServizio key={s.id} servizio={s} indice={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
