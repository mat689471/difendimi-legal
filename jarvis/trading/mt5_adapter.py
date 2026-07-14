"""Adattatore MetaTrader 5 (Fusion Market).

Implementa l'interfaccia Broker parlando col terminale MetaTrader 5. E'
funzionale, ma per usarlo servono cose che TU devi fornire consapevolmente:

  * il pacchetto `MetaTrader5` (pip install MetaTrader5), che gira solo su
    Windows col terminale MT5 installato e in esecuzione;
  * le credenziali di un conto — usa PRIMA un conto DEMO di Fusion Market;
  * per operare su un server non-demo devi passare live=True esplicitamente,
    e comunque il RiskManager richiede mode=live + allow_live + conferma.

Non ci sono chiavi né connessioni automatiche nel codice: le porti tu.
Nota: qui non c'e' il MetaTrader5, quindi questo modulo non e' coperto dai
test automatici — va provato sul tuo conto demo.
"""

from __future__ import annotations

from .broker import Broker, Order, Position


class MetaTrader5Broker(Broker):
    def __init__(self, login: int, password: str, server: str, *,
                 live: bool = False, magic: int = 990099, deviation: int = 20):
        self.login = login
        self.server = server
        self._live = live
        self.magic = magic
        self.deviation = deviation
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
                "solo conti demo salvo attivazione live esplicita (live=True)."
            )
        if not mt5.initialize(login=self.login, password=password, server=self.server):
            raise RuntimeError(f"initialize MT5 fallito: {mt5.last_error()}")
        return mt5

    # --- utility interne ------------------------------------------------
    def _tick(self, symbol: str):
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"nessun tick per {symbol}: simbolo assente o non selezionato")
        return tick

    def _point_value(self, symbol: str) -> float:
        info = self._mt5.symbol_info(symbol)
        if info is None or not info.trade_tick_size:
            return 1.0
        # valore di 1 unita' di prezzo per 1 lotto ≈ tick_value / tick_size
        return float(info.trade_tick_value) / float(info.trade_tick_size)

    def _to_position(self, p) -> Position:
        side = "buy" if p.type == self._mt5.POSITION_TYPE_BUY else "sell"
        return Position(
            id=int(p.ticket), symbol=p.symbol, side=side, volume=float(p.volume),
            entry_price=float(p.price_open), current_price=float(p.price_current),
            point_value=self._point_value(p.symbol),
            sl=float(p.sl) or None, tp=float(p.tp) or None,
        )

    # --- interfaccia Broker --------------------------------------------
    def open(self, order: Order) -> Position:
        mt5 = self._mt5
        tick = self._tick(order.symbol)
        if order.side == "buy":
            order_type, price = mt5.ORDER_TYPE_BUY, tick.ask
        else:
            order_type, price = mt5.ORDER_TYPE_SELL, tick.bid
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order.symbol,
            "volume": float(order.volume),
            "type": order_type,
            "price": price,
            "deviation": self.deviation,
            "magic": self.magic,
            "comment": "jarvis",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        if order.sl is not None:
            request["sl"] = float(order.sl)
        if order.tp is not None:
            request["tp"] = float(order.tp)

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"order_send fallito: {getattr(result, 'comment', mt5.last_error())}")

        # recupera la posizione appena aperta (per ticket dell'ordine/deal)
        for p in mt5.positions_get(symbol=order.symbol) or []:
            if int(p.ticket) == int(result.order) or int(getattr(p, "identifier", 0)) == int(result.order):
                return self._to_position(p)
        # fallback: costruisci dalla risposta
        return Position(
            id=int(result.order), symbol=order.symbol, side=order.side,
            volume=float(order.volume), entry_price=float(result.price),
            current_price=float(result.price), point_value=self._point_value(order.symbol),
            sl=order.sl, tp=order.tp,
        )

    def close(self, position_id: int, price: float | None = None) -> float:
        mt5 = self._mt5
        target = next((p for p in mt5.positions_get() or [] if int(p.ticket) == int(position_id)), None)
        if target is None:
            raise RuntimeError(f"posizione {position_id} non trovata")
        tick = self._tick(target.symbol)
        if target.type == mt5.POSITION_TYPE_BUY:
            close_type, close_price = mt5.ORDER_TYPE_SELL, tick.bid
        else:
            close_type, close_price = mt5.ORDER_TYPE_BUY, tick.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": target.symbol,
            "volume": float(target.volume),
            "type": close_type,
            "position": int(position_id),
            "price": close_price,
            "deviation": self.deviation,
            "magic": self.magic,
            "comment": "jarvis-close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        profit = float(target.profit)
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"chiusura fallita: {getattr(result, 'comment', mt5.last_error())}")
        return profit

    def positions(self) -> list[Position]:
        return [self._to_position(p) for p in self._mt5.positions_get() or []]

    def equity(self) -> float:
        info = self._mt5.account_info()
        if info is None:
            raise RuntimeError("account_info non disponibile")
        return float(info.equity)

    def shutdown(self) -> None:
        try:
            self._mt5.shutdown()
        except Exception:  # pragma: no cover
            pass
