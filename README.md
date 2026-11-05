# claude-usage

Mod do [Herdr](https://herdr.dev) que mostra, numa barra acima da barra de status, o uso dos limites do Claude Code:

- **5h**: medidor de 0 a 100% da sessao atual (quanto ainda resta). Sem aviso.
- **hoje**: o limite semanal dividido em 7 dias (100/7 = 14,28% por dia). Aviso se o uso do dia passa disso.
- **semana**: o dia *n* libera *n* x 14,28% acumulado. Aviso se o uso acumulado passa do liberado.

Os dias contam a partir do reset semanal (`resets_at - 7d`), nao do calendario. Quando uma barra passa do limite ela fica vermelha, o painel mostra `AVISO: dia e/ou semana` e o Herdr dispara uma notificacao (uma vez por dia e tipo).

## Como funciona

1. O Claude Code roda `statusline.py` como `statusLine`. Ele le `rate_limits` (planos Pro/Max), calcula dia e semana, imprime a barra de status do Claude e grava `~/.claude/token-monitor/state.json`.
2. O mod (`main.js`) le esse arquivo a cada 5 segundos e desenha o painel.

Os dados so atualizam enquanto uma sessao do Claude Code esta ativa.

## Instalacao

1. Copie esta pasta para `~/.config/herdr-app/mods/claude-usage/`.
2. Em `~/.claude/settings.json`:
   ```json
   "statusLine": {
     "type": "command",
     "command": "python3 ~/.config/herdr-app/mods/claude-usage/statusline.py"
   }
   ```
   (use o caminho absoluto se o seu Claude Code nao expandir `~`)
3. O Herdr nao encaixa o mod sozinho nos layouts que ele distribui. Clone o layout e acrescente o bloco acima da barra de status:
   ```sh
   herdr-app do layout.clone '{"name":"main","as":"main-claude"}'
   ```
   e em `layouts/main-claude.json`, antes do bloco `status`, inclua:
   ```json
   { "id": "claude-usage", "type": "block", "size": { "px": 26 }, "content": { "mod": "claude-usage" } }
   ```
4. `herdr-app check ~/.config/herdr-app/mods/claude-usage` e `herdr-app do layout.switch '{"name":"main-claude"}'`.

A notificacao usa o comando `herdr` no PATH do processo do Claude.
