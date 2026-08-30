"use client";

import { useEffect, useState } from "react";
import { Phone, MessageCircle, X, CalendarClock } from "lucide-react";
import { azienda } from "@/lib/content";
import { cn } from "@/lib/utils";

/**
 * Barra di contatto sempre raggiungibile.
 * Su mobile è una barra piena in fondo (il pollice arriva lì); da desktop
 * diventa un pulsante flottante che apre le stesse azioni.
 */
export default function FloatingContact() {
  const [aperto, setAperto] = useState(false);
  const [visibile, setVisibile] = useState(false);

  // Compare dopo il primo schermo: nell'hero i pulsanti ci sono già e
  // sovrapporlo subito coprirebbe contenuto senza aggiungere nulla.
  useEffect(() => {
    const onScroll = () => setVisibile(window.scrollY > 520);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const tel = `tel:${azienda.telefono.replace(/\s/g, "")}`;
  const wa = `https://wa.me/${azienda.whatsapp}?text=${encodeURIComponent(
    "Buongiorno, vorrei un sopralluogo per il mio giardino."
  )}`;

  return (
    <>
      {/* Mobile: barra fissa in basso */}
      <div className="fixed inset-x-0 bottom-0 z-40 flex gap-2.5 border-t border-line bg-white/92 px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 backdrop-blur-xl sm:hidden">
        <a
          href={tel}
          className="flex min-h-[52px] flex-1 items-center justify-center gap-2 rounded-full bg-forest text-sm font-semibold text-white"
        >
          <Phone className="h-[18px] w-[18px]" aria-hidden="true" /> Chiama
        </a>
        <a
          href={wa}
          target="_blank"
          rel="noopener noreferrer"
          className="flex min-h-[52px] flex-1 items-center justify-center gap-2 rounded-full border-2 border-forest text-sm font-semibold text-forest"
        >
          <MessageCircle className="h-[18px] w-[18px]" aria-hidden="true" /> WhatsApp
        </a>
      </div>

      {/* Desktop: pulsante flottante */}
      <div
        className={cn(
          "fixed bottom-7 right-7 z-40 hidden flex-col items-end gap-3 transition-all duration-300 sm:flex",
          visibile ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-4 opacity-0"
        )}
      >
        {aperto && (
          <div className="glass w-64 rounded-2xl p-3">
            <a href={tel} className="flex min-h-[52px] items-center gap-3 rounded-xl px-3 text-sm font-semibold text-forest hover:bg-sage-50">
              <Phone className="h-5 w-5" aria-hidden="true" />
              {azienda.telefonoLabel}
            </a>
            <a href={wa} target="_blank" rel="noopener noreferrer" className="flex min-h-[52px] items-center gap-3 rounded-xl px-3 text-sm font-semibold text-forest hover:bg-sage-50">
              <MessageCircle className="h-5 w-5" aria-hidden="true" />
              Scrivi su WhatsApp
            </a>
            <a href="#preventivo" onClick={() => setAperto(false)} className="flex min-h-[52px] items-center gap-3 rounded-xl px-3 text-sm font-semibold text-forest hover:bg-sage-50">
              <CalendarClock className="h-5 w-5" aria-hidden="true" />
              Richiedi sopralluogo
            </a>
          </div>
        )}

        <button
          type="button"
          onClick={() => setAperto((v) => !v)}
          aria-expanded={aperto}
          aria-label={aperto ? "Chiudi i contatti rapidi" : "Apri i contatti rapidi"}
          className="relative flex h-16 w-16 items-center justify-center rounded-full bg-forest text-white shadow-lift transition-transform hover:scale-105 active:scale-95"
        >
          {!aperto && (
            <span
              aria-hidden="true"
              className="absolute inset-0 rounded-full bg-forest motion-safe:animate-pulse-ring"
            />
          )}
          <span className="relative">
            {aperto ? <X className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
          </span>
        </button>
      </div>
    </>
  );
}
