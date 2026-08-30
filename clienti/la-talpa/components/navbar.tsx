"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Menu, X, MapPin, Phone } from "lucide-react";
import { azienda } from "@/lib/content";
import { cn } from "@/lib/utils";

const voci = [
  { href: "#servizi", label: "Servizi" },
  { href: "#lavori", label: "Lavori" },
  { href: "#recensioni", label: "Recensioni" },
  { href: "#preventivo", label: "Preventivo" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [attiva, setAttiva] = useState<string>("");
  const [apertoMobile, setApertoMobile] = useState(false);
  const ridotto = useReducedMotion();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  /* L'indicatore segue la sezione visibile. IntersectionObserver invece di
     calcoli su scroll: nessuna lettura di layout a ogni frame. */
  useEffect(() => {
    const sezioni = voci
      .map((v) => document.querySelector(v.href))
      .filter((el): el is Element => Boolean(el));
    if (!sezioni.length) return;

    const obs = new IntersectionObserver(
      (entries) => {
        const visibile = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visibile) setAttiva(`#${visibile.target.id}`);
      },
      { rootMargin: "-45% 0px -45% 0px", threshold: [0, 0.25, 0.5, 1] }
    );
    sezioni.forEach((s) => obs.observe(s));
    return () => obs.disconnect();
  }, []);

  // Con il menu aperto la pagina sotto non deve scorrere.
  useEffect(() => {
    document.body.style.overflow = apertoMobile ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [apertoMobile]);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-[background-color,box-shadow,backdrop-filter] duration-300",
        scrolled ? "bg-white/75 backdrop-blur-xl shadow-soft" : "bg-transparent"
      )}
    >
      <nav className="wrap flex h-[72px] items-center justify-between gap-4" aria-label="Principale">
        <a href="#contenuto" className="flex shrink-0 items-baseline gap-2">
          <span className="font-display text-2xl font-bold tracking-tight text-forest">
            La Talpa
          </span>
          <span className="hidden text-[11px] uppercase tracking-[0.16em] text-clay sm:inline">
            Verde
          </span>
        </a>

        <ul className="hidden items-center gap-1 md:flex">
          {voci.map((v) => {
            const isAttiva = attiva === v.href;
            return (
              <li key={v.href} className="relative">
                <a
                  href={v.href}
                  aria-current={isAttiva ? "true" : undefined}
                  className={cn(
                    "relative block rounded-full px-4 py-2 text-sm font-medium transition-colors",
                    isAttiva ? "text-forest" : "text-clay hover:text-forest"
                  )}
                >
                  {v.label}
                  {isAttiva && (
                    <motion.span
                      layoutId="nav-attiva"
                      className="absolute inset-0 -z-10 rounded-full bg-sage-100"
                      transition={ridotto ? { duration: 0 } : { type: "spring", stiffness: 380, damping: 32 }}
                    />
                  )}
                </a>
              </li>
            );
          })}
        </ul>

        <div className="flex items-center gap-2">
          <span className="hidden items-center gap-1.5 rounded-full border border-sage-300 bg-sage-50 px-3 py-1.5 text-xs font-medium text-forest lg:inline-flex">
            <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
            Disponibile a {azienda.zona.split(" · ")[0]} e Versilia
          </span>

          <a
            href="#preventivo"
            className="hidden min-h-[44px] items-center rounded-full bg-forest px-5 text-sm font-semibold text-white transition-colors hover:bg-forest-deep sm:inline-flex"
          >
            Preventivo immediato
          </a>

          <a
            href={`tel:${azienda.telefono.replace(/\s/g, "")}`}
            aria-label={`Chiama ${azienda.nome}`}
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-line text-forest sm:hidden"
          >
            <Phone className="h-5 w-5" aria-hidden="true" />
          </a>

          <button
            type="button"
            onClick={() => setApertoMobile((v) => !v)}
            aria-expanded={apertoMobile}
            aria-controls="menu-mobile"
            aria-label={apertoMobile ? "Chiudi il menu" : "Apri il menu"}
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-line text-forest md:hidden"
          >
            {apertoMobile ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
          </button>
        </div>
      </nav>

      {apertoMobile && (
        <div id="menu-mobile" className="border-t border-line bg-white/95 backdrop-blur-xl md:hidden">
          <ul className="wrap flex flex-col py-2">
            {voci.map((v) => (
              <li key={v.href}>
                <a
                  href={v.href}
                  onClick={() => setApertoMobile(false)}
                  className="block min-h-[52px] border-b border-line/70 py-3.5 text-base font-medium text-ink last:border-0"
                >
                  {v.label}
                </a>
              </li>
            ))}
            <li className="py-3">
              <a
                href="#preventivo"
                onClick={() => setApertoMobile(false)}
                className="flex min-h-[52px] items-center justify-center rounded-full bg-forest px-5 font-semibold text-white"
              >
                Preventivo immediato
              </a>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
}
