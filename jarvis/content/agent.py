"""L'Agente Contenuti — il cuore automatizzato di ContentFlow.

Dato il brand di un cliente e un numero N, genera N contenuti pronti:
per ognuno inventa un'angolazione, ne ricava un brief, e lo passa alla pipeline
(props Remotion + pacchetto social). E' cio' che un cliente pagherebbe: mette
il brand una volta, riceve contenuti in serie.

Due cervelli per le idee:
  * IdeaGenerator (offline): ruota tra angolazioni e argomenti del brand con
    template. Deterministico, funziona sempre, zero costi.
  * LlmIdeaGenerator (opzionale): con Claude inventa idee davvero originali.
    Si attiva con ANTHROPIC_API_KEY + `pip install anthropic`.

Ogni pezzo generato finisce in un manifest e nell'audit log.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .pipeline import REMOTION, prepare, slugify


@dataclass
class Brand:
    """La configurazione che il cliente inserisce una volta sola."""
    name: str                       # nome interno/slug
    display: str                    # come appare nel video (es. "⚖️ DIFENDIMI")
    tagline: str = ""               # sottotitolo sotto il nome
    urgency: str = ""               # barra in alto (es. "⚖️ CONSULENZA GRATUITA ⚖️")
    audience: str = "i tuoi clienti"
    topics: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    offer: str = ""
    cta: str = ""
    cta_badge: str = ""
    hashtags_base: str = ""
    stores: str = ""        # riga contatto sotto il video (es. "Studio Rossi • Milano")
    testimonial: str = ""   # testimonianza (se vuota, ne generiamo una neutra)

    @classmethod
    def from_dict(cls, d: dict) -> "Brand":
        return cls(
            name=d["name"], display=d.get("display", d["name"]),
            tagline=d.get("tagline", ""), urgency=d.get("urgency", ""),
            audience=d.get("audience", "i tuoi clienti"),
            topics=d.get("topics", []), features=d.get("features", []),
            offer=d.get("offer", ""), cta=d.get("cta", ""),
            cta_badge=d.get("cta_badge", ""), hashtags_base=d.get("hashtags_base", ""),
            stores=d.get("stores", ""), testimonial=d.get("testimonial", ""),
        )


# Angolazioni: il "trucco" per generare tanti contenuti diversi dallo stesso
# brand. Ognuna e' un modo di raccontare un argomento.
_ANGLES = [
    ("errore",
     "L'errore più comune con {topic}",
     "E può costarti caro. 😰",
     "{display} ti mostra come evitarlo 🤖"),
    ("diritto",
     "{topic}: sai davvero cosa ti spetta?",
     "La maggior parte delle persone no. 🚫",
     "{display} te lo spiega in un minuto ⚖️"),
    ("scadenza",
     "{topic}: attenzione ai tempi ⏳",
     "Aspettare può farti perdere il diritto.",
     "{display} ti avvisa e ti guida 🤖"),
    ("domanda",
     "«{topic}?» — la domanda che ci fanno tutti",
     "E quasi nessuno sa la risposta giusta.",
     "{display} risponde, subito e gratis 💬"),
    ("caso",
     "Storia vera: {topic}",
     "È finita meglio di quanto pensi.",
     "Con {display} puoi farcela anche tu ✅"),
]


class IdeaGenerator:
    """Genera brief ruotando angolazioni e argomenti. Offline, deterministico."""

    def briefs(self, brand: Brand, count: int) -> list[dict]:
        topics = brand.topics or [brand.display]
        out: list[dict] = []
        for i in range(count):
            angle_key, hook_t, agitate_t, solution_t = _ANGLES[i % len(_ANGLES)]
            topic = topics[i % len(topics)]
            ctx = {"topic": topic, "display": brand.display, "audience": brand.audience}
            tag = slugify(topic)
            out.append({
                "name": f"{brand.name}-{i+1:02d}-{tag}",
                "title": hook_t.format(**ctx),
                "brand": brand.display,
                "tagline": brand.tagline,
                "urgency": brand.urgency,
                "hook": hook_t.format(**ctx),
                "agitate": agitate_t.format(**ctx),
                "solution": solution_t.format(**ctx),
                "features": brand.features,
                "testimonial": brand.testimonial or f'"Consiglio {brand.display}!" 💬',
                "offer": brand.offer,
                "cta": brand.cta,
                "ctaBadge": brand.cta_badge,
                "stores": brand.stores or brand.display,
                "hashtags": (brand.hashtags_base + " #" + tag).strip(),
                "_angle": angle_key,
                "_topic": topic,
            })
        return out


class LlmIdeaGenerator:
    """Idee originali con Claude. Attivo solo con SDK + API key."""

    def __init__(self, model: str = "claude-sonnet-5", api_key: str | None = None):
        self.model = model
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def briefs(self, brand: Brand, count: int) -> list[dict]:
        if not self.available():
            raise RuntimeError(
                "Generatore LLM inattivo: servono ANTHROPIC_API_KEY e `pip install anthropic`."
            )
        import anthropic
        client = anthropic.Anthropic(api_key=self._api_key)
        system = (
            "Sei un copywriter per contenuti social brevi. Ricevi un brand e "
            "restituisci SOLO un array JSON di oggetti, uno per video, con i "
            "campi: name, title, hook, agitate, solution, offer, cta. Testi in "
            "italiano, concisi, adatti a un reel verticale."
        )
        user = (
            f"Brand: {brand.display}. Pubblico: {brand.audience}. "
            f"Argomenti: {', '.join(brand.topics)}. Genera {count} idee diverse."
        )
        msg = client.messages.create(model=self.model, max_tokens=2048,
                                     system=system, messages=[{"role": "user", "content": user}])
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        ideas = json.loads(text)
        for i, idea in enumerate(ideas):
            idea.setdefault("name", f"{brand.name}-{i+1:02d}")
            idea["brand"] = brand.display
            idea["features"] = brand.features
            idea["ctaBadge"] = brand.cta_badge
            idea.setdefault("hashtags", brand.hashtags_base)
        return ideas[:count]


@dataclass
class Piece:
    slug: str
    angle: str
    topic: str
    props: str
    social: str
    video: str | None = None


class ContentAgent:
    """Orchestratore: brand -> idee -> pipeline -> contenuti + manifest."""

    def __init__(self, generator=None, audit=None, killswitch=None):
        self.generator = generator or IdeaGenerator()
        self.audit = audit
        self.killswitch = killswitch

    def produce(self, brand: Brand, count: int = 5, render: bool = False) -> list[Piece]:
        pieces: list[Piece] = []
        for brief in self.generator.briefs(brand, count):
            angle = brief.pop("_angle", "n/d")
            topic = brief.pop("_topic", "")
            out = prepare(brief)
            video = None
            if render:
                from .render import render as _render
                ok = _render(out.props_path, out.output_video,
                             killswitch=self.killswitch, audit=self.audit)
                video = str(out.output_video) if ok else None
            pieces.append(Piece(out.slug, angle, topic, str(out.props_path),
                                str(out.social_path), video))
            if self.audit:
                self.audit.record("content_generated", brand=brand.name, slug=out.slug,
                                  angle=angle, rendered=bool(video))

        manifest_dir = REMOTION / "out" / slugify(brand.name)
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest = manifest_dir / "manifest.json"
        manifest.write_text(json.dumps(
            [p.__dict__ for p in pieces], ensure_ascii=False, indent=2), encoding="utf-8")
        return pieces


def main(argv: list[str] | None = None) -> int:
    import sys
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("uso: python -m jarvis.content.agent <brand.json> [--count N]")
        return 1
    from ..env import load_env
    load_env()  # carica jarvis/.env (ANTHROPIC_API_KEY per le idee LLM)
    brand = Brand.from_dict(json.loads(Path(argv[0]).read_text(encoding="utf-8")))
    count = 5
    if "--count" in argv:
        count = int(argv[argv.index("--count") + 1])
    do_render = "--render" in argv

    gen = LlmIdeaGenerator()
    # collega audit + kill switch, così i render sono tracciati e fermabili
    from ..agent import load_config
    from ..core import AuditLog, KillSwitch
    cfg = load_config()
    audit = AuditLog(cfg["audit_path"])
    killswitch = KillSwitch(cfg["stop_sentinel"])
    agent = ContentAgent(generator=gen if gen.available() else IdeaGenerator(),
                         audit=audit, killswitch=killswitch)
    print(f"[agente] genero {count} contenuti per «{brand.display}» "
          f"({'LLM' if isinstance(agent.generator, LlmIdeaGenerator) else 'offline'})"
          f"{' + render .mp4' if do_render else ''}")
    for p in agent.produce(brand, count, render=do_render):
        print(f"  ✓ [{p.angle:8}] {p.slug}")
        print(f"     social: {p.social}")
        if p.video:
            print(f"     video:  {p.video}")
        elif do_render:
            print(f"     video:  ⚠️ render non riuscito")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
