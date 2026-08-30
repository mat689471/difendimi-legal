import type { Config } from "tailwindcss";

/**
 * Token del brand La Talpa.
 * I rapporti di contrasto sono verificati su sfondo #F7F5F1:
 *   ink 14.9:1 · forest 10.2:1 · soil 12.7:1 · clay 6.0:1 · bronze 4.6:1
 * `gold` sta a 2.85:1 ed e' quindi SOLO decorativo: mai testo, mai bordo
 * che debba comunicare uno stato. Per il testo caldo si usa `clay`.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#F7F5F1",
        surface: "#FFFFFF",
        ink: "#16231C",
        forest: { DEFAULT: "#1B4332", deep: "#122E22", light: "#2D6A4F" },
        soil: "#3E2723",
        clay: "#6B5B4B",
        bronze: "#8A6A3F",
        gold: "#B08D4F",
        line: "#E3DED4",
        "line-strong": "#6F8570",
        sage: { 50: "#F1F4EF", 100: "#DDE5DA", 300: "#A9BCA6" },
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      borderRadius: { xl: "1rem", "2xl": "1.5rem", "3xl": "2rem" },
      boxShadow: {
        soft: "0 1px 2px rgba(22,35,28,.04), 0 12px 32px -16px rgba(22,35,28,.18)",
        lift: "0 2px 4px rgba(22,35,28,.05), 0 24px 48px -24px rgba(22,35,28,.28)",
      },
      keyframes: {
        marquee: { from: { transform: "translateX(0)" }, to: { transform: "translateX(-50%)" } },
        pulseRing: {
          "0%": { transform: "scale(1)", opacity: "0.55" },
          "70%": { transform: "scale(1.7)", opacity: "0" },
          "100%": { transform: "scale(1.7)", opacity: "0" },
        },
      },
      animation: {
        marquee: "marquee var(--marquee-duration,42s) linear infinite",
        "pulse-ring": "pulseRing 2.4s cubic-bezier(.22,.61,.36,1) infinite",
      },
    },
  },
  plugins: [],
};
export default config;
