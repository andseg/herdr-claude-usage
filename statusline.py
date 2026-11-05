#!/usr/bin/env python3
"""Statusline do Claude Code: monitora os limites de 5h, do dia e da semana (7d).

- 5h: medidor simples de 0 a 100% da sessao atual (mostra quanto ainda resta). Sem aviso.
- Dia: o limite semanal dividido em 7 dias de 100/7 (14,28%). Aviso se o uso do dia passa disso.
- Semana: dia n libera n * 14,28% acumulado. Aviso se o uso acumulado passa do liberado.
Os dias contam a partir do reset semanal (resets_at - 7d), nao do relogio.
Notificacao do Herdr uma vez por dia e tipo. Estado em ~/.claude/token-monitor/state.json
(lido pelo mod claude-usage do Herdr).
"""
import json, os, subprocess, sys, time

DIR = os.path.expanduser("~/.claude/token-monitor")
STATE = os.path.join(DIR, "state.json")
DAY = 100.0 / 7
RED, YEL, GRN, DIM, RST = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"
LABEL = {"day": "dia", "week": "semana"}


def read_window(rl, key):
    w = rl.get(key)
    if not isinstance(w, dict) or w.get("used_percentage") is None or not w.get("resets_at"):
        return None
    try:
        return float(w["used_percentage"]), int(w["resets_at"])
    except (TypeError, ValueError):
        return None


try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
rl = data.get("rate_limits") if isinstance(data, dict) else None
rl = rl if isinstance(rl, dict) else {}
now = time.time()

wk = read_window(rl, "seven_day")
if not wk:
    print(f"{DIM}limite semanal indisponivel{RST}")
    sys.exit(0)
used, resets = wk
k = max(0, min(6, int((now - (resets - 7 * 86400)) // 86400)))  # indice do dia (0..6)
fv = read_window(rl, "five_hour")

try:
    st = json.load(open(STATE))
    if not isinstance(st, dict):
        st = {}
except Exception:
    st = {}
# estado de outra semana, antigo ou quebrado: repoe so o que faltar
if st.get("week_resets") != resets:
    st = {"week_resets": resets}
alerted = st.get("alerted") if isinstance(st.get("alerted"), dict) else {}
baselines = st.get("baselines") if isinstance(st.get("baselines"), dict) else {}
last = st.get("last_used") if isinstance(st.get("last_used"), (int, float)) else (0.0 if k == 0 else used)

# baseline do dia = ultimo uso visto antes de o dia comecar
base = baselines.setdefault(str(k), last)
day_used = max(0.0, used - base)
allowed_week = (k + 1) * DAY
day = {"used": day_used, "allowed": DAY, "warn": day_used > DAY, "index": k + 1}
week = {"used": used, "allowed": allowed_week, "warn": used > allowed_week, "index": k + 1}

alerts, new = [], []
for name, w in (("day", day), ("week", week)):
    if w["warn"]:
        alerts.append(name)
        key = f"{name}:{resets}:{k}"
        if not alerted.get(key):
            alerted[key] = True
            new.append(name)
if new:
    parts = [f"{LABEL[n]} {(day if n == 'day' else week)['used']:.0f}% de "
             f"{(day if n == 'day' else week)['allowed']:.1f}%" for n in alerts]
    try:
        subprocess.Popen(
            ["herdr", "notification", "show",
             f"Claude: limite excedido ({' e '.join(LABEL[n] for n in new)})",
             "--body", f"Dia {k+1}/7: " + " | ".join(parts),
             "--position", "top-right", "--sound", "request"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True)
    except Exception:
        pass

r = lambda v: round(v, 2)
state = {
    "week_resets": resets, "alerted": alerted, "baselines": baselines,
    "last_used": used, "updated": int(now),
    "five": None if not fv else {"resets_at": fv[1], "used": r(fv[0]), "allowed": 100.0, "warn": False},
    "day": {"resets_at": resets, **{a: (r(b) if isinstance(b, float) else b) for a, b in day.items()}},
    "week": {"resets_at": resets, **{a: (r(b) if isinstance(b, float) else b) for a, b in week.items()}},
}
state["week"]["slices"] = state["day"]["slices"] = 7
try:
    os.makedirs(DIR, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE)
except Exception:
    pass

c = lambda warn: RED if warn else GRN
out = ""
if fv:
    out += f"5h {GRN}{fv[0]:.0f}%{RST}/100% | "
out += (f"D{k+1}/7 | hoje {c(day['warn'])}{day_used:.0f}%{RST}/{DAY:.1f}% | "
        f"semana {c(week['warn'])}{used:.0f}%{RST}/{allowed_week:.1f}%")
if alerts:
    out += f" {YEL}AVISO: {' e '.join(LABEL[n] for n in alerts)}{RST}"
print(out)
