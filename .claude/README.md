# .claude — skills e MCP di progetto

## Skills: ui-ux-pro-max (plugin installato manualmente)

`/plugin marketplace add` non è disponibile in questo ambiente, quindi il plugin
`ui-ux-pro-max@ui-ux-pro-max-skill` è stato installato copiando le sue skill
in `.claude/skills/` (skill di progetto, caricate automaticamente).

Origine: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill — v2.13.0, MIT.
Manifest del plugin conservato in `.claude-plugin/plugin.json`.

Skill disponibili: `banner-design`, `brand`, `design`, `design-system`,
`slides`, `ui-styling`, `ui-ux-pro-max`.

Esempio d'uso:

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "beauty spa wellness" \
  --design-system -p "Serenity Spa"
```

Aggiornare il plugin = ricopiare `.claude/skills/` dal repo upstream.

## MCP: 21st.dev

`.mcp.json` registra il server HTTP `21st`. La chiave API NON è nel repo:
va esposta come variabile d'ambiente prima di avviare Claude Code.

```bash
export TWENTYFIRST_API_KEY="21st_sk_..."
```

In alternativa, registrazione solo locale (scritta in `~/.claude.json`, mai committata):

```bash
claude mcp add --transport http 21st https://21st.dev/api/mcp \
  --header "x-api-key: $TWENTYFIRST_API_KEY"
```
