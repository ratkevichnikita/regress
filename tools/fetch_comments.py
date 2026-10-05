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

P = None  # активный профиль
YT = "/opt/homebrew/bin/yt-dlp"


# --- общее для всех профилей -------------------------------------------------
NOISE = ["подпис", "канал", "спасибо за видео", "благодарю", "http", "₽", "руб",
         "скидк", "промокод", "вебинар"]
ADVICE = ["вам надо", "вам нужно", "попробуйте", "советую", "рекомендую",
          "почитайте", "в помощь", "вам поможет", "просто начните"]

# --- профили -----------------------------------------------------------------
PROFILES = {
"telo": dict(
  min_len=60, age=(28,47), drop_male=True,
  unresolved=["не могу","не получается","не знаю","до сих пор","как убрать","что делать",
              "не понимаю как","никак не","не выходит","не справляюсь","устала","задолбал",
              "замкнутый круг","выхода нет","непонятно","не понятно","как избавиться",
              "как справиться","как перестать","не помогает","глубинная работа","не отпускает"],
  core=["сон","сплю","уснуть","засыпа","бессонниц","просыпа","тревог","паник","напряжен","зажим",
        "расслаб","сердц","дыш","воздух","ком в горле","плеч","челюст","живот","болит","боли",
        "давлен","психосоматик","дрожь","спин","выгоран","сил нет","усталость","мышц","тело","температур"],
  life=["муж","дет","сын","доч","работ","мам","начальник","семь","лет мне","мне 3","мне 4",
        "декрет","отпуск","больничн"],
  resolved=["сейчас всё хорошо","сейчас все хорошо","помог психолог","избавилась","освободилась",
            "мне помогла","мне помогло","я поменялась","теперь я","я справилась","прошла терапию",
            "стало намного легче"],
),
"otn": dict(
  min_len=80, age=(24,50), drop_male=False,
  unresolved=["не могу отпустить","не могу забыть","не получается","не знаю как","не знаю что",
              "до сих пор","снова","опять","одно и то же","одни и те же","не понимаю почему",
              "как перестать","что делать","не отпускает","никак не","третий раз","каждый раз",
              "почему я","почему мне","не выходит","не складывается","замкнутый круг","по кругу"],
  core=["отношен","бывш","расстал","расстава","партн","любл","влюб","отпустить","забыть","развод",
        "брак","муж","жена","парень","девушк","свидан","одинок","близост","ревн","привязан",
        "выбира","притяг","бросил","ушёл","ушел","ушла","изменил","токсичн","созависим","разрыв"],
  life=["лет","замуж","дети","ребен","работ","мам","отец","семь","живём","живем"],
  resolved=["я отпустила","я отпустил","сейчас всё хорошо","сейчас все хорошо","встретила",
            "вышла замуж","женился","мне помогло","мне помогла","я справилась","я справился",
            "теперь я счастл","прошла терапию","всё наладилось"],
),
}

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
    if len(t) < P["min_len"]:
        return 0, [], f"короткий ({len(t)} зн.)"
    short_but_sharp = len(t) < 150 and hits(t, P["unresolved"]) and hits(t, P["core"])
    if hits(t, NOISE):
        return 0, [], "реклама или благодарность"
    if P["drop_male"] and (MASC.search(low) or hits(t, MASC_WORDS)) and not FEM.search(low):
        return 0, [], "вероятно мужской род"
    if m := re.search(r"мне\s+(\d{2})", low):
        age = int(m.group(1))
        lo, hi = P["age"]
        if not lo <= age <= hi:
            return 0, [], f"возраст вне сегмента ({age})"

    pts, why = 0, []
    if u := hits(t, P["unresolved"]):
        pts += 3 * min(len(u), 3); why.append("незакрытость: " + ", ".join(u[:3]))
    if b := hits(t, P["core"]):
        pts += 2 * min(len(b), 4); why.append("тема: " + ", ".join(b[:4]))
    if l := hits(t, P["life"]):
        pts += 1 * min(len(l), 3); why.append("маркеры жизни: " + ", ".join(l[:3]))
    if FEM.search(low):
        pts += 2; why.append("женский род")
    if len(t) > 400:
        pts += 2; why.append("развёрнутый")
    if short_but_sharp:
        pts += 4; why.append("короткая и точная")
    if r := hits(t, P["resolved"]):
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
        elif argv[i] == "--profile":
            globals()["P"] = PROFILES[argv[i + 1]]; i += 2
        elif argv[i].startswith("--"):
            i += 1
        else:
            args.append(argv[i]); i += 1
    if not args:
        print(__doc__); sys.exit(1)

    if P is None: globals()["P"] = PROFILES["telo"]
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
