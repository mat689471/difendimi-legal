"""Adattatore MetaTrader 5 (Fusion Market) — DISATTIVO per default.

Implementa l'interfaccia Broker parlando col terminale MetaTrader 5. NON e'
utilizzabile finche' non lo colleghi consapevolmente, perche':

  * richiede il pacchetto `MetaTrader5` (pip install MetaTrader5), che gira
    solo su Windows col terminale MT5 installato e in esecuzione;
  * richiede le credenziali di un conto — usa PRIMA un conto DEMO di Fusion
    Market, mai il conto reale finche' non ti fidi della strategia;
  * il modulo si rifiuta di operare in 'live' se non hai messo allow_live=true
    nella config (vedi risk.py).

Qui non ci sono chiavi né connessioni automatiche: sei tu a fornirle.
"""

from __future__ import annotations

from .broker import Broker, Order, Position


class MetaTrader5Broker(Broker):
    def __init__(self, login: int, password: str, server: str, *, live: bool = False):
        self.login = login
        self.server = server
        self._live = live
        self._mt5 = self._connect(password)

    def _connect(self, password: str):
        try:
            import MetaTrader5 as mt5  # type: ignore
        except ImportError as exc:  # pragma: no cover - dipende dall'ambiente
            raise RuntimeError(
                "Pacchetto MetaTrader5 non installato. Su Windows: pip install MetaTrader5, "
                "col terminale MT5 aperto. Per ora usa PaperBroker (modalita' paper)."
            ) from exc
        if not self._live and "demo" not in self.server.lower():
            raise RuntimeError(
                f"Server '{self.server}' non sembra un conto demo. Per sicurezza collego "
                "solo conti demo salvo attivazione live esplicita."
            )
        if not mt5.initialize(login=self.login, password=password, server=self.server):
            raise RuntimeError(f"initialize MT5 fallito: {mt5.last_error()}")
        return mt5

    # I metodi sotto sono lasciati come punti di aggancio: vanno completati
    # quando colleghi davvero MT5, mappando Order/Position sulle chiamate mt5.
    def open(self, order: Order) -> Position:  # pragma: no cover
        raise NotImplementedError(
            "Aggancio MT5 non implementato: mappa qui order_send() su una Position. "
            "Fallo solo dopo aver validato la strategia in paper/demo."
        )

    def close(self, position_id: int, price: float | None = None) -> float:  # pragma: no cover
        raise NotImplementedError("Aggancio MT5 non implementato: mappa qui la chiusura posizione.")

    def positions(self) -> list[Position]:  # pragma: no cover
        raise NotImplementedError("Aggancio MT5 non implementato: mappa qui positions_get().")

    def equity(self) -> float:  # pragma: no cover
        return float(self._mt5.account_info().equity)
