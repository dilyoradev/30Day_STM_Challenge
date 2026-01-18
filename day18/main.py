from __future__ import annotations

import datetime as dt
from pathlib import Path

def prompt(msg: str, default: str | None = None) -> str:
    if default:
        raw = input(f"{msg} [{default}]: ").strip()
        return raw if raw else default
    return input(f"{msg}: ").strip()

def prompt_multiline(title: str) -> list[str]:
    print(f"\n{title}（複数行OK。空行で終了）")
    lines: list[str] = []
    while True:
        line = input("> ").rstrip()
        if line == "":
            break
        lines.append(line)
    return lines

def parse_time(s: str) -> dt.time:
    # Accept "9:00" or "09:00"
    try:
        h, m = s.split(":")
        return dt.time(hour=int(h), minute=int(m))
    except Exception:
        raise ValueError("Time must be HH:MM (e.g., 09:00).")

def minutes_between(start: dt.time, end: dt.time) -> int:
    today = dt.date.today()
    a = dt.datetime.combine(today, start)
    b = dt.datetime.combine(today, end)
    # If end is past midnight (rare), handle by adding a day
    if b < a:
        b += dt.timedelta(days=1)
    return int((b - a).total_seconds() // 60)

def fmt_hm(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if m else f"{h}h"

def bulletize(lines: list[str]) -> str:
    if not lines:
        return "- （なし）"
    return "\n".join(f"- {x}" for x in lines)

def build_report_jp(date_str: str, work_summary: str, did: list[str], learned: list[str], next_: list[str], blocked: list[str]) -> str:
    return f"""お疲れ様です！本日の日報です！

## 📅 日付
- {date_str}

## ⏱ 本日の稼働時間
- {work_summary}

## ✅ やったこと
{bulletize(did)}

## 🧠 学び
{bulletize(learned)}

## 🔜 次にやること
{bulletize(next_)}

## 🧩 困っていたこと
{bulletize(blocked)}
"""

def build_report_en(date_str: str, work_summary: str, did: list[str], learned: list[str], next_: list[str], blocked: list[str]) -> str:
    return f"""Daily Update

## Date
- {date_str}

## Work Hours
- {work_summary}

## Done
{bulletize(did)}

## Learnings
{bulletize(learned)}

## Next
{bulletize(next_)}

## Blockers
{bulletize(blocked)}
"""

def main() -> None:
    now = dt.datetime.now()
    date_str = prompt("日付", default=now.strftime("%Y-%m-%d"))

    # Work time
    start_s = prompt("開始時刻 (HH:MM)", default="09:00")
    end_s = prompt("終了時刻 (HH:MM)", default="18:00")
    break_min_s = prompt("休憩 (分)", default="60")

    try:
        start_t = parse_time(start_s)
        end_t = parse_time(end_s)
        break_min = int(break_min_s)
        total = minutes_between(start_t, end_t) - break_min
        if total < 0:
            total = 0
    except Exception as e:
        print(f"\n時刻の入力が不正です: {e}")
        print("稼働時間の計算はスキップします。")
        work_summary = f"{start_s} - {end_s} (break {break_min_s}m)"
    else:
        work_summary = f"{start_s} - {end_s}（休憩 {break_min}分）= 実働 {fmt_hm(total)}"

    # Content
    did = prompt_multiline("やったこと")
    learned = prompt_multiline("学び")
    next_ = prompt_multiline("次にやること")
    blocked = prompt_multiline("困っていたこと")

    lang = prompt("出力言語 (jp/en/both)", default="jp").lower().strip()
    jp = build_report_jp(date_str, work_summary, did, learned, next_, blocked)
    en = build_report_en(date_str, work_summary, did, learned, next_, blocked)

    if lang == "en":
        output = en
        suffix = "en"
    elif lang == "both":
        output = jp + "\n---\n\n" + en
        suffix = "both"
    else:
        output = jp
        suffix = "jp"

    # Save
    out_dir = Path.cwd() / "wol_logs"
    out_dir.mkdir(exist_ok=True)
    filename = f"wol_{date_str}_{now.strftime('%H%M%S')}_{suffix}.md"
    path = out_dir / filename
    path.write_text(output, encoding="utf-8")

    print("\n" + "=" * 60)
    print(output)
    print("=" * 60)
    print(f"\n✅ Saved: {path}")

if __name__ == "__main__":
    main()
