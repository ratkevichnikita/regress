#!/usr/bin/env python3
"""
Выгрузка и фильтрация комментариев YouTube под сегмент
«женщины 33-45 с синдромом отличницы, у которых напряжение вышло в тело».

  python3 fetch_comments.py "ССЫЛКА" [ещё ссылки...] [--limit 300]

Кладёт сырой JSON в tools/data/, отчёт — в tools/out/<id>.md
"""
import json, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
DATA, OUT = ROOT / "data", ROOT / "out"

MIN_LEN = 60           # короче — обычно «спасибо, это про меня»
YT = "/opt/homebrew/bin/yt-dlp"

# --- словари ---------------------------------------------------------------
UNRESOLVED = ["не могу", "не получается", "не знаю", "до сих пор", "как убрать",
              "что делать", "не понимаю как", "никак не", "не выходит",
              "не справляюсь", "устала", "задолбал", "замкнутый круг", "выхода нет",
              "непонятно", "не понятно", "как избавиться", "как справиться",
              "как перестать", "не помогает", "глубинная работа", "не отпускает"]

BODY = ["сон", "сплю", "уснуть", "засыпа", "бессонниц", "просыпа", "тревог", "паник",
        "напряжен", "зажим", "расслаб", "сердц", "дыш", "воздух", "ком в горле",
        "плеч", "челюст", "живот", "болит", "боли", "давлен", "психосоматик", "дрожь", "спин",
        "выгоран", "сил нет", "усталость", "мышц", "тело", "температур"]

LIFE = ["муж", "дет", "сын", "доч", "работ", "мам", "начальник", "семь",
        "лет мне", "мне 3", "мне 4", "декрет", "отпуск", "больничн"]

# уже вышли — в таблицу не идут, годятся только как «Стало»
RESOLVED = ["сейчас всё хорошо", "сейчас все хорошо", "помог психолог", "избавилась",
            "освободилась", "мне помогла", "мне помогло", "я поменялась",
            "теперь я", "я справилась", "прошла терапию", "стало намного легче"]

NOISE = ["подпис", "канал", "спасибо за видео", "благодарю", "http", "@", "₽", "руб",
         "скидк", "промокод", "курс ", "вебинар"]

ADVICE = ["вам надо", "вам нужно", "попробуйте", "советую", "рекомендую",
          "почитайте", "в помощь", "вам поможет", "просто начните"]

MASC = re.compile(r"\bя\s+(?:[а-яё]+\s+){0,2}[а-яё]{2,}(?<!ла)(?<!ло)л\b", re.I)
FEM  = re.compile(r"\bя\s+(?:[а-яё]+\s+){0,2}[а-яё]{2,}ла\b", re.I)
MASC_WORDS = ["жена", "женитьб", "супруга", "буду честен", "я сам ", "я должен",
              "я уверен", "я рад ", "я был ", "мужик", "как мужчина", "я женат"]


def hits(text, words):
    t = text.lower()
    return [w for w in words if w in t]


def score(c):
    """Возвращает (балл, причины, стоп-причина или None)."""
    t = c["text"].strip()
    low = t.lower()

    if c.get("author_is_uploader"):
        return 0, [], "автор канала"
    if len(t) < MIN_LEN:
        return 0, [], f"короткий ({len(t)} зн.)"
    short_but_sharp = len(t) < 120 and hits(t, UNRESOLVED) and hits(t, BODY)
    if hits(t, NOISE):
        return 0, [], "реклама или благодарность"
    if (MASC.search(low) or hits(t, MASC_WORDS)) and not FEM.search(low):
        return 0, [], "вероятно мужской род"
    if m := re.search(r"мне\s+(\d{2})", low):
        age = int(m.group(1))
        if not 28 <= age <= 47:
            return 0, [], f"возраст вне сегмента ({age})"

    pts, why = 0, []
    if u := hits(t, UNRESOLVED):
        pts += 3 * min(len(u), 3); why.append("незакрытость: " + ", ".join(u[:3]))
    if b := hits(t, BODY):
        pts += 2 * min(len(b), 4); why.append("тело: " + ", ".join(b[:4]))
    if l := hits(t, LIFE):
        pts += 1 * min(len(l), 3); why.append("маркеры жизни: " + ", ".join(l[:3]))
    if FEM.search(low):
        pts += 2; why.append("женский род")
    if len(t) > 400:
        pts += 2; why.append("развёрнутый")
    if short_but_sharp:
        pts += 4; why.append("короткая и точная")
    if r := hits(t, RESOLVED):
        pts -= 6; why.append("⚠ уже вышла: " + r[0])
    if hits(t, ADVICE):
        pts -= 6; why.append("⚠ советует другим")
    return pts, why, None


def fetch(url, limit):
    DATA.mkdir(parents=True, exist_ok=True)
    subprocess.run([YT, "--write-comments", "--skip-download", "--no-warnings", "-q",
                    "--extractor-args", f"youtube:max_comments={limit},all,{limit},20",
                    "-o", "%(id)s", url], cwd=DATA, check=True)
    vid = re.search(r"(?:v=|be/|shorts/)([\w-]{11})", url).group(1)
    return json.loads((DATA / f"{vid}.info.json").read_text(encoding="utf-8"))


def report(info, url):
    rows = []
    for c in info.get("comments", []):
        pts, why, stop = score(c)
        rows.append((pts, why, stop, c))
    rows.sort(key=lambda r: -r[0])

    take = [r for r in rows if r[2] is None and r[0] >= 6]
    maybe = [r for r in rows if r[2] is None and 2 <= r[0] < 6]
    drop = [r for r in rows if r[2] is not None or r[0] < 2]

    L = [f"# {info.get('title','')}", "",
         f"Ссылка: {url}",
         f"Комментариев выгружено: {len(rows)} · берём {len(take)} · "
         f"под вопросом {len(maybe)} · отсев {len(drop)}", ""]

    def block(title, items, show_why=True):
        L.append(f"## {title}\n")
        if not items:
            L.append("_пусто_\n"); return
        for i, (pts, why, stop, c) in enumerate(items, 1):
            txt = re.sub(r"\s+", " ", c["text"]).strip()
            L.append(f"**{i}.** {txt}")
            tail = f"`{pts}` " + (" · ".join(why) if show_why else stop or "")
            L.append(f"<sub>{tail} · ♥{c.get('like_count') or 0}</sub>\n")

    block("Берём", take)
    block("Под вопросом", maybe)
    L.append("## Отсев\n")
    for pts, why, stop, c in drop[:60]:
        txt = re.sub(r"\s+", " ", c["text"]).strip()[:110]
        L.append(f"- ~~{txt}~~ <sub>{stop or f'мало баллов ({pts})'}</sub>")
    return "\n".join(L)


def main():
    argv, args, limit = sys.argv[1:], [], 300
    i = 0
    while i < len(argv):
        if argv[i] == "--limit":
            limit = int(argv[i + 1]); i += 2
        elif argv[i].startswith("--"):
            i += 1
        else:
            args.append(argv[i]); i += 1
    if not args:
        print(__doc__); sys.exit(1)

    OUT.mkdir(parents=True, exist_ok=True)
    for url in args:
        info = fetch(url, limit)
        md = report(info, url)
        f = OUT / f"{info['id']}.md"
        f.write_text(md, encoding="utf-8")
        head = md.splitlines()[3]
        print(f"✓ {info.get('title','')[:55]}\n  {head}\n  → {f}")


if __name__ == "__main__":
    main()
