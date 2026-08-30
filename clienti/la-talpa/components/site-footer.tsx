import { MapPin, Phone, Mail, Clock, Leaf } from "lucide-react";
import { azienda, comuni } from "@/lib/content";

export default function SiteFooter() {
  return (
    <footer className="border-t border-line bg-forest-deep pb-28 pt-16 text-sage-100 sm:pb-16">
      <div className="wrap">
        <div className="grid gap-12 lg:grid-cols-[1.2fr_1fr_1fr]">
          <div>
            <p className="font-display text-3xl font-bold text-white">La Talpa</p>
            <p className="mt-1 text-sm uppercase tracking-[0.16em] text-sage-300">{azienda.claim}</p>
            <p className="mt-5 max-w-sm leading-relaxed text-sage-100/80">{azienda.payoff}</p>

            <div className="mt-7">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-sage-300">
                Dove interveniamo
              </p>
              {/* Mappa stilizzata: elenco dei comuni serviti. Un'immagine di
                  mappa qui non aggiungerebbe informazione e peserebbe di più. */}
              <ul className="mt-3 flex flex-wrap gap-2">
                {comuni.map((c) => (
                  <li
                    key={c}
                    className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-sm text-sage-100"
                  >
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div>
            <h2 className="text-xs font-semibold uppercase tracking-[0.16em] text-sage-300">Contatti</h2>
            <ul className="mt-4 space-y-3.5">
              <li className="flex items-start gap-3">
                <Phone className="mt-0.5 h-[18px] w-[18px] shrink-0 text-sage-300" aria-hidden="true" />
                <a
                  href={`tel:${azienda.telefono.replace(/\s/g, "")}`}
                  className="font-semibold text-white underline-offset-4 hover:underline"
                >
                  {azienda.telefonoLabel}
                </a>
              </li>
              <li className="flex items-start gap-3">
                <Mail className="mt-0.5 h-[18px] w-[18px] shrink-0 text-sage-300" aria-hidden="true" />
                <a href={`mailto:${azienda.email}`} className="underline-offset-4 hover:underline">
                  {azienda.email}
                </a>
              </li>
              <li className="flex items-start gap-3">
                <MapPin className="mt-0.5 h-[18px] w-[18px] shrink-0 text-sage-300" aria-hidden="true" />
                <span>{azienda.zona}</span>
              </li>
            </ul>
          </div>

          <div>
            <h2 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-sage-300">
              <Clock className="h-4 w-4" aria-hidden="true" /> Orari
            </h2>
            <ul className="mt-4 space-y-2.5">
              {azienda.orari.map((o) => (
                <li key={o.giorno} className="flex justify-between gap-4 border-b border-white/10 pb-2 text-sm last:border-0">
                  <span className="text-sage-100/80">{o.giorno}</span>
                  <span className="font-semibold text-white">{o.ore}</span>
                </li>
              ))}
            </ul>

            <p className="mt-7 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3.5 py-2 text-xs text-sage-100">
              <Leaf className="h-4 w-4 text-sage-300" aria-hidden="true" />
              Smaltimento verde a norma
            </p>
          </div>
        </div>

        <div className="mt-14 border-t border-white/10 pt-6 text-sm text-sage-100/65">
          {/* DA COMPLETARE prima della pubblicazione: ragione sociale esatta,
              P.IVA, indirizzo della sede e link a privacy policy e cookie
              policy (obbligatori quando il modulo raccoglie dati personali). */}
          <p>© {new Date().getFullYear()} La Talpa — P.IVA [DA INSERIRE]</p>
          <p className="mt-1">Sito realizzato da [NOME DA DECIDERE]</p>
        </div>
      </div>
    </footer>
  );
}
