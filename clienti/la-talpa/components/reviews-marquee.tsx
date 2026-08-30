"use client";

import { useState } from "react";
import { Star, Pause, Play, Quote } from "lucide-react";
import { recensioni } from "@/lib/content";
import { cn } from "@/lib/utils";

/**
 * La spaziatura sta nel margine destro della scheda, non in un `gap` del
 * contenitore. Con il gap le due metà del nastro non misurerebbero lo stesso,
 * la traslazione del 50% non coinciderebbe con un ciclo esatto e a ogni giro
 * si vedrebbe uno scatto. Col margine ogni metà vale 5 × (larghezza + 20px)
 * e il ciclo chiude perfetto.
 */
function Scheda({ r }: { r: (typeof recensioni)[number] }) {
  return (
    <figure className="mr-5 flex w-[19rem] shrink-0 flex-col rounded-2xl border border-line bg-surface p-6 shadow-soft sm:w-[22rem]">
      <Quote className="h-6 w-6 text-sage-300" aria-hidden="true" />
      <blockquote className="mt-3 flex-1 leading-relaxed text-ink">{r.testo}</blockquote>
      <figcaption className="mt-5 flex items-center justify-between border-t border-line pt-4">
        <span className="text-sm font-semibold text-forest">
          {r.autore} · <span className="font-normal text-clay">{r.luogo}</span>
        </span>
        <span className="flex" role="img" aria-label="5 stelle su 5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star key={i} className="h-3.5 w-3.5 fill-bronze text-bronze" aria-hidden="true" />
          ))}
        </span>
      </figcaption>
    </figure>
  );
}

function Gruppo({ nascosto = false }: { nascosto?: boolean }) {
  return (
    <div className="flex shrink-0" aria-hidden={nascosto || undefined}>
      {recensioni.map((r, i) => (
        <Scheda key={i} r={r} />
      ))}
    </div>
  );
}

export default function ReviewsMarquee() {
  const [inPausa, setInPausa] = useState(false);

  return (
    <section id="recensioni" className="scroll-mt-24 overflow-hidden py-20 sm:py-28">
      <div className="wrap">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Dicono di noi</p>
            <h2 className="mt-4 max-w-xl font-display text-[clamp(2rem,5.5vw,3.25rem)] font-bold leading-[1.08] tracking-tight text-forest">
              Clienti tra Massa, Carrara e la Versilia
            </h2>
          </div>

          {/* Un contenuto che scorre da solo deve poter essere fermato:
              requisito WAI per il movimento automatico. */}
          <button
            type="button"
            onClick={() => setInPausa((v) => !v)}
            aria-pressed={inPausa}
            className="inline-flex min-h-[44px] items-center gap-2 rounded-full border border-line-strong px-4 text-sm font-semibold text-forest transition-colors hover:bg-sage-50"
          >
            {inPausa ? <Play className="h-4 w-4" aria-hidden="true" /> : <Pause className="h-4 w-4" aria-hidden="true" />}
            {inPausa ? "Riprendi" : "Metti in pausa"}
          </button>
        </div>
      </div>

      {/* Si ferma anche al passaggio del mouse e quando il fuoco da tastiera
          entra nel nastro: altrimenti non si riuscirebbe a leggerlo. */}
      <div className="group/marquee relative mt-12 flex overflow-hidden [mask-image:linear-gradient(90deg,transparent,#000_6%,#000_94%,transparent)]">
        <div
          className={cn(
            "flex motion-safe:animate-marquee",
            "group-hover/marquee:[animation-play-state:paused] group-focus-within/marquee:[animation-play-state:paused]",
            inPausa && "[animation-play-state:paused]"
          )}
        >
          <Gruppo />
          {/* Copia solo per la continuità visiva: nascosta agli screen reader,
              che leggerebbero altrimenti due volte le stesse recensioni. */}
          <Gruppo nascosto />
        </div>
      </div>
    </section>
  );
}
