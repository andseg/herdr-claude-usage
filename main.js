import { View, div } from "gpui-kit";
import { h_flex } from "gpui-base";
import { theme, home, readTextFile } from "herdr";

// Limite semanal do Claude dividido em 7 dias (100/7 = 14,28% por dia).
// Le ~/.claude/token-monitor/state.json, escrito por statusline.py (nesta pasta),
// que o Claude Code roda como statusLine (ver ~/.claude/settings.json).
const BAR = 90;

export default class ClaudeUsage extends View {
  init(_props, cx) {
    this.s = null;
    this.load(cx);
    cx.timer.every(5000, cx => this.load(cx));
  }

  load(cx) {
    cx.spawn(async cx => {
      let next = null;
      try {
        const txt = await readTextFile(`${home()}/.claude/token-monitor/state.json`);
        if (txt) next = JSON.parse(txt);
      } catch { next = null; }
      this.s = next;
      cx.notify();
    });
  }

  bar(t, label, used, allowed, warn, text) {
    const pct = Math.max(0, Math.min(100, used));
    const fill = warn ? t.blocked : t.working;
    return h_flex().gap(6).items_center()
      .child(div().text_color(t.muted).child(label))
      .child(div().w(BAR).h(6).rounded(3).bg(t.border).overflow_hidden()
        .child(div().w(Math.round(BAR * pct / 100)).h(6).bg(fill)))
      .child(div().text_color(warn ? t.blocked : t.muted)
        .child(text ?? `${Math.round(used)}% / ${allowed.toFixed(1)}%`));
  }

  render() {
    const t = theme();
    const s = this.s;
    const frame = () => h_flex().size_full().px(14).gap(16).items_center().bg(t.chrome)
      .border_t(1).border_color(t.border).text_size(11.8).text_color(t.muted);
    // Janela vencida nao vale: espera a statusline atualizar.
    const live = w => w && w.resets_at && w.resets_at * 1000 > Date.now() ? w : null;
    const five = live(s?.five), week = live(s?.week);
    if (!week) {
      return frame().child("Claude").child(div().text_color(t.dim).child("sem dados (abre uma sessao do Claude)"));
    }
    const day = live(s?.day);
    const names = [day?.warn && "dia", week.warn && "semana"].filter(Boolean).join(" e ");
    return frame()
      .child(div().text_color(t.foreground).child("Claude"))
      // 5h: medidor de 0 a 100% da sessao atual, sem aviso; mostra o que ainda resta.
      .when(Boolean(five), el => el.child(this.bar(t, "5h", five.used, 100, false,
        `${Math.round(five.used)}% / 100% · resta ${Math.max(0, Math.round(100 - five.used))}%`)))
      .when(Boolean(day), el => el.child(this.bar(t, "hoje", day.used, day.allowed, day.warn)))
      .child(this.bar(t, `semana ${week.index}/${week.slices}`, week.used, week.allowed, week.warn))
      .when(Boolean(names), el => el.child(div().text_color(t.blocked).child(`AVISO: ${names}`)));
  }
}
