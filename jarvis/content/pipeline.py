"""Pipeline contenuti: da un 'brief' a un video + pacchetto social.

Un brief descrive il contenuto in modo semplice. La pipeline:
  1. lo converte nei props del video Remotion (data-driven: vedi
     remotion/src/ViralVideo.tsx);
  2. costruisce il comando di render Remotion e lo esegue TRAMITE Jarvis,
     quindi con audit log e kill switch — niente gira fuori dal tuo controllo;
  3. genera il pacchetto social (descrizione + hashtag) pronto per la
     pubblicazione.

ONESTA' sulla pubblicazione: la pubblicazione su YouTube/social NON e'
automatica. Richiede le TUE credenziali e la TUA approvazione, e
l'automazione del posting viola le condizioni d'uso di molte piattaforme
(rischio sospensione dell'account). Qui prepariamo tutto; l'ultimo clic e' tuo.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REMOTION = REPO / "remotion"
COMPOSITION_ID = "DifendimiViral"

# Rispecchia defaultViralProps in remotion/src/ViralVideo.tsx.
# Se cambi i default là, aggiornali qui (o viceversa).
DEFAULTS = {
    "brand": "⚖️ DIFENDIMI",
    "tagline": "L'App che rende giustizia accessibile",
    "urgencyBar": "⚠️ CONOSCI I TUOI DIRITTI ⚠️",
    "captions": [
        "Sei stato fermato dalla polizia?",
        "Non sai cosa puoi e NON puoi fare? 🚫",
        "DIFENDIMI ti guida 24/7 con intelligenza artificiale 🤖",
        "",
        '"Finalmente posso difendermi da solo" 💬',
        "30 giorni GRATIS 🎁 Nessuna carta richiesta",
        "Scarica ora. La legge è dalla tua parte. ⚖️",
    ],
    "features": [
        "✅ Diritti in tempo reale",
        "✅ Documenti legali gratis",
        "✅ Database leggi italiane",
    ],
    "ctaBadge": "📲 Scarica DIFENDIMI",
    "stores": "App Store  •  Google Play",
    "hashtags": "#difendimi #diritti #italia #legge #giustizia",
}


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "video"


def build_props(brief: dict) -> dict:
    """Converte un brief 'umano' nei props del video, riempiendo i buchi
    con i default. Le didascalie centrali seguono lo schema narrativo
    hook -> agita -> soluzione -> (features) -> testimonianza -> offerta -> CTA.
    """
    captions = list(DEFAULTS["captions"])
    mapping = {0: "hook", 1: "agitate", 2: "solution", 4: "testimonial", 5: "offer", 6: "cta"}
    for idx, key in mapping.items():
        if brief.get(key):
            captions[idx] = brief[key]

    return {
        "brand": brief.get("brand", DEFAULTS["brand"]),
        "tagline": brief.get("tagline", DEFAULTS["tagline"]),
        "urgencyBar": brief.get("urgency", DEFAULTS["urgencyBar"]),
        "captions": captions,
        "features": brief.get("features", DEFAULTS["features"]),
        "ctaBadge": brief.get("ctaBadge", DEFAULTS["ctaBadge"]),
        "stores": brief.get("stores", DEFAULTS["stores"]),
        "hashtags": brief.get("hashtags", DEFAULTS["hashtags"]),
    }


def social_package(brief: dict, props: dict) -> str:
    """Descrizione pronta per il post: titolo, corpo dai messaggi, hashtag."""
    title = brief.get("title") or props["captions"][0]
    body_lines = [c for i, c in enumerate(props["captions"]) if c and i != 3]
    body = "\n".join(f"• {line}" for line in body_lines)
    features = "\n".join(props["features"])
    return (
        f"{title}\n\n{body}\n\n{features}\n\n"
        f"{props['ctaBadge']}  —  {props['stores']}\n\n{props['hashtags']}\n"
    )


@dataclass
class BuildOutput:
    slug: str
    props_path: Path
    output_video: Path
    social_path: Path
    render_command: str
    files_written: list[Path] = field(default_factory=list)


def prepare(brief: dict) -> BuildOutput:
    """Prepara props, pacchetto social e comando di render. Non renderizza."""
    slug = slugify(brief.get("name") or brief.get("title") or "video")
    props = build_props(brief)

    props_dir = REMOTION / "props"
    out_dir = REMOTION / "out"
    props_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    props_path = props_dir / f"{slug}.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")

    social_path = out_dir / f"{slug}.social.txt"
    social_path.write_text(social_package(brief, props), encoding="utf-8")

    output_video = out_dir / f"{slug}.mp4"
    from .render import render_command as _render_command  # lazy: evita import circolare
    render_command = _render_command(props_path, output_video)
    return BuildOutput(slug, props_path, output_video, social_path, render_command,
                       [props_path, social_path])


def run(brief: dict, jarvis=None, execute: bool = True) -> BuildOutput:
    """Prepara e (se execute) renderizza davvero il video in .mp4, sotto kill
    switch e audit di Jarvis."""
    from .render import render as _render
    out = prepare(brief)
    print(f"[pipeline] props   -> {out.props_path}")
    print(f"[pipeline] social  -> {out.social_path}")
    if not execute:
        print(f"[pipeline] render  -> {out.render_command}")
        return out
    if jarvis is None:
        from jarvis.agent import Jarvis
        jarvis = Jarvis.from_config(str(REPO / "jarvis" / "config.yaml"))
    print(f"[pipeline] rendering -> {out.output_video} …")
    ok = _render(out.props_path, out.output_video,
                 killswitch=jarvis.killswitch, audit=jarvis.audit)
    print(f"[pipeline] render {'OK' if ok else 'FALLITO'}: {out.output_video}")
    return out


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("uso: python -m jarvis.content <brief.json> [--no-render]")
        return 1
    brief = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    execute = "--no-render" not in argv
    run(brief, execute=execute)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
