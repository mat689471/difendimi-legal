import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import { azienda } from "@/lib/content";
import "./globals.css";

/* next/font ospita i font in locale: niente richiesta a Google al caricamento
   e nessuno spostamento del testo quando arrivano (display: swap). */
const sans = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});
const display = Playfair_Display({
  subsets: ["latin"],
  display: "swap",
  weight: ["500", "600", "700"],
  variable: "--font-display",
});

export const metadata: Metadata = {
  title: `${azienda.nome} — ${azienda.claim} a Massa, Carrara e Versilia`,
  description:
    "Progettazione e manutenzione giardini tra Massa, Carrara e la Versilia: prato a rotoli, potature, impianti di irrigazione, pulizia terreni. Sopralluogo gratuito.",
  openGraph: {
    title: `${azienda.nome} — ${azienda.payoff}`,
    description: "Giardinaggio e cura del verde tra mare e Apuane. Sopralluogo gratuito.",
    locale: "it_IT",
    type: "website",
  },
};

export const viewport = { themeColor: "#1B4332" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it" className={`${sans.variable} ${display.variable}`}>
      <body>
        <a
          href="#contenuto"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-forest focus:px-4 focus:py-3 focus:text-white"
        >
          Vai al contenuto
        </a>
        {children}
      </body>
    </html>
  );
}
