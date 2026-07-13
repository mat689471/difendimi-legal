# difendimi-legal

Contiene anche **Jarvis**, un assistente AI modulare (in italiano) con
sicurezza al centro: audit log, kill switch, autenticazione a proprietario
unico. Moduli: automazione di sistema, interfaccia + voce, pipeline contenuti,
trading (demo-first).

➡️ Documentazione e istruzioni: [`jarvis/README.md`](jarvis/README.md)

```bash
pip install -r jarvis/requirements.txt
python jarvis/server.py          # avvia l'interfaccia (apri l'URL col token)
python -m jarvis.trading         # demo trading (paper, 0 euro reali)
python -m pytest jarvis/tests/   # 25 test
```
