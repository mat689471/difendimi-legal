"""Il Guardiano — la skill che Jarvis dedica al TUO benessere.

Tutto il resto di Jarvis serve a fare cose. Questa skill serve a proteggere la
persona che gliele chiede. Non blocca nulla — tu comandi sempre — ma alza la
voce della prudenza nei momenti giusti:

  * quando stai per compiere qualcosa di irreversibile a notte fonda;
  * quando stai per muovere denaro reale;
  * quando vai troppo veloce, a raffica (segno di stanchezza o impulsivita');
  * quando sei al lavoro da troppo tempo senza una pausa.

E' pensata per parlare poco e bene: ogni avviso ha un tempo di riposo, cosi'
Jarvis non diventa mai assillante. Un guardiano discreto, non un controllore.

Perche' questa e non un'altra: perche' un assistente davvero fidato ti guarda
le spalle anche da te stesso. Questo e' il senso vero di "non ti tradisco".
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Advisory:
    level: str      # "info" | "suggerimento" | "attenzione"
    key: str        # identificativo (per audit e per il tempo di riposo)
    message: str    # in italiano, in carattere


@dataclass
class GuardianConfig:
    appellativo: str = "signore"
    quiet_start: int = 23           # inizio ore "notturne" (prudenza alzata)
    quiet_end: int = 6              # fine ore notturne
    session_break_minutes: int = 120  # dopo quanto suggerire una pausa
    rapid_window_sec: int = 60      # finestra per contare le azioni a raffica
    rapid_count: int = 8            # quante azioni in quella finestra fanno scattare l'avviso
    cooldown_minutes: int = 30      # riposo minimo tra due avvisi uguali


class Guardian:
    def __init__(self, config: GuardianConfig | None = None):
        self.config = config or GuardianConfig()
        self._session_start: datetime | None = None
        self._recent: deque[datetime] = deque()
        self._last_emitted: dict[str, datetime] = {}
        self._break_suggested = False

    # --- helper temporali ------------------------------------------------
    def _is_quiet(self, hour: int) -> bool:
        s, e = self.config.quiet_start, self.config.quiet_end
        return hour >= s or hour < e if s > e else s <= hour < e

    def _on_cooldown(self, key: str, now: datetime) -> bool:
        last = self._last_emitted.get(key)
        if last is None:
            return False
        return (now - last).total_seconds() < self.config.cooldown_minutes * 60

    def _emit(self, advisories: list[Advisory], adv: Advisory, now: datetime) -> None:
        if not self._on_cooldown(adv.key, now):
            self._last_emitted[adv.key] = now
            advisories.append(adv)

    # --- API principale --------------------------------------------------
    def observe(self, *, risk: str = "SAFE", real_money: bool = False,
                now: datetime | None = None) -> list[Advisory]:
        """Valuta il momento e ritorna gli avvisi (spesso nessuno).

        `risk` usa gli stessi livelli del resto di Jarvis (SAFE/ELEVATED/
        CATASTROPHIC); `real_money` segnala un'operazione con soldi veri.
        """
        now = now or datetime.now()
        sig = self.config.appellativo
        advisories: list[Advisory] = []

        if self._session_start is None:
            self._session_start = now
        self._recent.append(now)
        while self._recent and (now - self._recent[0]).total_seconds() > self.config.rapid_window_sec:
            self._recent.popleft()

        irreversible = risk == "CATASTROPHIC"
        night = self._is_quiet(now.hour)

        # 1. irreversibile + notte fonda: la combinazione piu' pericolosa
        if irreversible and night:
            self._emit(advisories, Advisory(
                "attenzione", "notte_irreversibile",
                f"{sig.capitalize()}, è notte fonda e sta per compiere un'azione "
                f"senza ritorno. Le suggerisco di dormirci su: domani deciderà con "
                f"la mente lucida. Io sarò qui."), now)

        # 2. denaro reale: mai in automatico, sempre con un respiro
        if real_money:
            extra = " Per giunta a quest'ora." if night else ""
            self._emit(advisories, Advisory(
                "attenzione", "denaro_reale",
                f"Un attimo, {sig}. Stiamo per muovere denaro reale.{extra} Nessuna "
                f"operazione vale la sua serenità: è davvero sicuro?"), now)

        # 3. azioni a raffica: stanchezza o impulsivita'
        if len(self._recent) >= self.config.rapid_count:
            self._emit(advisories, Advisory(
                "suggerimento", "a_raffica",
                f"{sig.capitalize()}, stiamo andando molto veloci. Un respiro non "
                f"guasta: preferisce che rallenti?"), now)

        # 4. sessione lunga: una pausa (una volta sola)
        elapsed_min = (now - self._session_start).total_seconds() / 60
        if not self._break_suggested and elapsed_min >= self.config.session_break_minutes:
            self._break_suggested = True
            self._emit(advisories, Advisory(
                "suggerimento", "pausa",
                f"{sig.capitalize()}, siamo al lavoro da un po'. Una pausa la "
                f"aiuterebbe più di quanto pensi — il lavoro resta, lei viene prima."), now)

        return advisories

    def reset_session(self) -> None:
        """Da chiamare dopo una pausa reale: azzera i contatori di sessione."""
        self._session_start = None
        self._break_suggested = False
        self._recent.clear()
