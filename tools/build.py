#!/usr/bin/env python3
"""work.json から、このサイトのHTMLをすべて生成します。

使い方（リポジトリのルートで）:
    python3 tools/build.py

生成されるもの:
    index.html（作品トップ）、episodeN.html（各話）、volumeN.html（単行本）、404.html

編集してよいのは work.json、css/、js/ です。生成されたHTMLは直接編集しないでください。

話・巻を追加するとき:
  1. 画像を置く
       images/episodes/episode02-001.webp, episode02-002.webp …（話2桁-ページ3桁）
       images/thumbs/episode02.webp
       images/volumes/volume02-cover.webp（巻を追加するとき）
  2. work.json の "episodes" / "volumes" に追記する
  3. python3 tools/build.py
ページ数は画像の枚数から自動で数えます。
"""
import glob, hashlib, html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
e = html.escape

data = json.load(open("work.json", encoding="utf-8"))
site, work = data["site"], data["work"]
episodes, volumes, related = data["episodes"], data.get("volumes", []), data.get("related", [])
site_link = data.get("site_link")
BASE = site["url"].rstrip("/") + "/"
TITLE = work["title"]
# タイトルが長いときの改行位置（work.json の work.title_break に「前|後」と書く）。なければそのまま。
TITLE_HTML = "<br>".join(e(x) for x in work["title_break"].split("|")) if work.get("title_break") else e(TITLE)
# ヒーローの小見出し（work.json の work.kicker。なければ表示しない）とキャッチコピー（work.catch_copy）
KICKER = work.get("kicker", "")
KICKER_HTML = f'<div class="jp-kicker">{e(KICKER)}</div>' if KICKER else ""
CATCH_HTML = f'<p class="jp-catch">{e(work["catch_copy"])}</p>' if work.get("catch_copy") else ""


def ver(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()[:8]


def img(base):
    """拡張子なしのパスから、実在する画像（webp優先）のパスを返す"""
    for ext in ("webp", "jpg", "png"):
        if os.path.exists(f"{base}.{ext}"):
            return f"{base}.{ext}"
    sys.exit(f"エラー: 画像が見つかりません: {base}.webp（または .jpg）")


def count_pages(no):
    for ext in ("webp", "jpg"):
        n = len(glob.glob(f"images/episodes/episode{no:02d}-*.{ext}"))
        if n:
            return n
    sys.exit(f"エラー: images/episodes/episode{no:02d}-001.webp などがありません")


def count_protected(no):
    n = len(glob.glob(f"protected/episode{no:02d}-*.akg"))
    if not n:
        sys.exit(f"エラー: protected/episode{no:02d}-001.akg などがありません（tools/encrypt_episode.py で作ります）")
    return n


for ep in episodes:
    ep["pages"] = count_protected(ep["no"]) if ep.get("protected") else count_pages(ep["no"])
ep_by_no = {ep["no"]: ep for ep in episodes}
vol_of_ep = {}
for v in volumes:
    for n in v["episodes"]:
        vol_of_ep[n] = v

V_CSS = ver("css/style.css")
V_VIEWER = ver("js/viewer.js")
V_TOP = ver("js/top.js")
V_PROT = ver("js/protected-reader.js") if os.path.exists("js/protected-reader.js") else ""
V_LISTEN = ver("js/listen.js") if os.path.exists("js/listen.js") else ""


def head(title, desc, url, typ, prefix="", theme=False):
    og = f'''<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{typ}">
<meta property="og:site_name" content="{e(site["name"])}">
<meta property="og:locale" content="ja_JP">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}images/ogp/default.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(TITLE)}">
<meta name="twitter:card" content="summary_large_image">'''
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{'<meta name="theme-color" content="#111111">' if theme else ''}
<title>{e(title)}</title>
{og}
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}css/style.css?v={V_CSS}"></head>
'''


def date_html(ep):
    """話の公開日（work.json の episodes[].date に "2026-11-21" の形で書く）。なければ表示しない。"""
    d = ep.get("date")
    if not d:
        return ""
    y, m, dd = (int(x) for x in d.split("-"))
    return f'<div class="episode-date" data-date="{d}">{y}年{m}月{dd}日</div>'

def characters_html():
    """登場人物（work.json の characters）。なければ何も出さない。"""
    chars = data.get("characters") or []
    if not chars:
        return ""
    cards = []
    for c in chars:
        role = f'<span class="char-role">{e(c["role"])}</span>' if c.get("role") else ""
        reading = f'<span class="char-reading">{e(c["reading"])}</span>' if c.get("reading") else ""
        note = f'<p class="char-note">{e(c["note"])}</p>' if c.get("note") else ""
        links = "".join(
            f'<a class="char-cameo" href="{e(x["url"])}" target="_blank" rel="noopener">'
            + (f'<img src="{img("images/related/" + x["icon"])}" alt="">' if x.get("icon") else "")
            + f'<span>{e(x["title"])}</span><i aria-hidden="true">›</i></a>'
            for x in c.get("cameo", []))
        cameo = f'<span class="char-cameo-head">ほかの作品でも会える</span>{links}' if links else ""
        cards.append(
            f'<li class="char-card{" is-main" if c.get("main") else ""}">'
            f'<img src="{img("images/characters/" + c["image"])}" alt="{e(c["name"])}" loading="lazy">'
            f'{role}<strong class="char-name">{e(c["name"])}</strong>{reading}'
            f'<p class="char-desc">{e(c["desc"])}</p>{note}<div class="char-cameos">{cameo}</div></li>')
    return f'<div class="info-section char-section"><h2>登場人物</h2><ul class="char-list">{"".join(cards)}</ul></div>'

def vol_cover(v):
    return img(f"images/volumes/volume{v['no']:02d}-cover")


def index_page():
    first, last = episodes[0], episodes[-1]
    hero_vol = volumes[0] if volumes else None
    hero_img = (f'<img src="{vol_cover(hero_vol)}" alt="{e(TITLE)} 第{hero_vol["no"]}巻表紙">' if hero_vol else "")
    rows = "".join(
        f'<a class="episode-row" href="episode{ep["no"]}.html" data-ep="{ep["no"]}">'
        f'<img class="episode-thumb" src="{img(f"images/thumbs/episode{ep["no"]:02d}")}" alt="第{ep["no"]}話 {e(ep["title"])}">'
        f'<div class="episode-meta"><div class="episode-title">第{ep["no"]}話 <span>{e(ep["title"])}</span></div>{date_html(ep)}{('<span class="protected-badge">🔒 パスワード</span>' if ep.get("protected") else "")}</div>'
        f'<div class="episode-read">読む</div></a>' for ep in episodes)
    tiles = "".join(
        f'<a class="volume-tile" href="volume{v["no"]}.html"><img src="{vol_cover(v)}" alt="{e(TITLE)} 第{v["no"]}巻表紙">'
        f'<div><strong>第{v["no"]}巻</strong><span>{e(v["summary"])}</span></div></a>'
        for v in sorted(volumes, key=lambda v: -v["no"]))
    tab = ' target="_blank" rel="noopener"'
    def rail_card(r):
        badge = f'<span class="rail-badge">{e(r["badge"])}</span>' if r.get("badge") else ""
        tags = "".join(f"<span>{e(t)}</span>" for t in r.get("tags", []))
        year = f'<span class="rail-year">{e(r["year"])}</span>' if r.get("year") else ""
        author = f'<span class="rail-author">作者：{e(r["author"])}</span>' if r.get("author") and r["author"] != work["author"] else ""
        inner = (f'<span class="rail-cover"><img loading="lazy" src="{img("images/related/" + r["cover"])}" alt="{e(r["cover_alt"])}">{badge}</span>'
                 f'<strong class="rail-title">{e(r["title"])}</strong>{year}{author}<span class="rail-tags">{tags}</span>')
        if r.get("url"):
            return f'<a class="rail-card" href="{e(r["url"])}"{tab if r.get("new_tab") else ""}>{inner}</a>'
        return f'<div class="rail-card is-static">{inner}</div>'
    cards = '<div class="work-rail">' + "".join(rail_card(r) for r in related) + "</div>"
    # 話数の範囲ボタン：50話以下では不要。51話を超えるときは ringo-chan の仕組み（PER_RANGE）に置き換える
    RANGE_BAR = ""
    related_html = f'<div class="info-section"><h2>同じ作者の作品</h2>{cards}</div>' if related else ""
    footer_link = f' ｜ <a href="{e(site_link["url"])}" target="_blank" rel="noopener" style="text-decoration:underline">{e(site_link["title"])}</a>' if site_link else ""
    return head(TITLE, site["description"], BASE, "website") + f'''<body class="top-page"><div class="jp-shell">
<section class="jp-hero">{hero_img}<div class="jp-hero-right"><div class="jp-hero-text">{KICKER_HTML}<div class="jp-logo">{TITLE_HTML}</div>{CATCH_HTML}</div></div></section>
<section class="jp-info"><h1 class="jp-title">{TITLE_HTML}</h1><div class="jp-author">{e(work["author"])}</div><div class="jp-tags"><span>オリジナル漫画</span><span>全{len(episodes)}話公開中</span></div><div class="jp-actions"><a class="jp-btn primary" href="episode{first["no"]}.html">第{first["no"]}話から読む</a><a class="jp-btn" href="episode{last["no"]}.html">最新話から読む</a></div></section>
<nav class="jp-tabs" aria-label="作品メニュー"><button class="jp-tab active" data-tab="episodes">話</button><button class="jp-tab" data-tab="comics">コミックス</button><button class="jp-tab" data-tab="info">作品情報</button></nav>
<section id="episodes" class="jp-panel active"><div class="episode-sort-header"><span>全{len(episodes)}話</span><div class="sort-switch episode-sort"><button type="button" class="sort-btn active" data-order="asc">1話から</button><span>|</span><button type="button" class="sort-btn" data-order="desc">最新話から</button></div></div>{RANGE_BAR}<div class="episode-list">{rows}</div></section>
<section id="comics" class="jp-panel"><div class="comics-header"><strong>コミックス</strong><div class="comics-sort"><span class="active">新しい順</span></div></div><div class="volume-list">{tiles}</div></section>
<section id="info" class="jp-panel info-panel"><div class="work-intro"><div class="work-catch">{e(TITLE)}</div>{summary_block()}<div class="author-profile"><img src="{img("images/work/author-portrait")}" alt="{e(work["author_portrait_alt"])}"><div><span>作者</span><strong>{e(work["author"])}</strong></div></div></div>{characters_html()}{related_html}</section>
</div><footer>{e(site["copyright"])}{footer_link}</footer>
<script src="js/top.js?v={V_TOP}"></script></body></html>
'''


def summary_block():
    ja = f'<p class="work-summary" lang="ja">{e(work["summary"])}</p>'
    if not work.get("summary_en") and not work.get("summary_audio"):
        return ja
    tools = '<div class="sum-tools">'
    if work.get("summary_audio"):
        tools += (f'<button type="button" class="sum-listen" data-audio="{e(work["summary_audio"])}">'
                  '<span class="sum-ic">▶</span><span class="sum-lb" data-ja="あらすじを聞く" data-en="Listen">あらすじを聞く</span></button>')
    if work.get("summary_en"):
        tools += '<span class="sum-lang"><button type="button" data-l="ja" aria-pressed="true">日本語</button><button type="button" data-l="en" aria-pressed="false">English</button></span>'
    tools += "</div>"
    en = ""
    if work.get("summary_en"):
        en = (f'<div class="sum-en" lang="en" hidden><p class="sum-title">{e(work.get("title_en", ""))}</p>'
              f'<p class="sum-catch">{e(work.get("catch_copy_en", ""))}</p><p class="work-summary">{e(work["summary_en"])}</p></div>')
    credit = f'<p class="sum-credit">音声：{e(work["voice_credit"])}</p>' if work.get("voice_credit") else ""
    return f'<div class="sum-box">{tools}<div class="sum-ja">{ja}</div>{en}{credit}</div>'




def pages_html(items, eager):
    out = []
    for i, (src, alt, attr) in enumerate(items):
        lazy = "" if i < eager else ' loading="lazy"'
        out.append(f'    <div class="manga-page"{attr}><img{lazy} src="{src}" alt="{e(alt)}"></div>')
    return "\n".join(out)


def reader_tail(total, footer_links):
    return (f'<div class="page-nav"><button id="prev" type="button">← 次のページ</button>'
            f'<button id="next" type="button">前のページ →</button></div>'
            f'<div class="counter" id="counter">1 / {total}</div>'
            f'<div class="reader-footer">{footer_links}</div>'
            f'<script src="js/viewer.js?v={V_VIEWER}"></script></body></html>\n')


def reader_top(back_href, back_text, extra=""):
    return (f'<body class="reader-page"><header class="reader-bar"><div class="reader-bar-inner">'
            f'<div class="reader-title"><a id="context-back" href="{back_href}">{back_text}</a></div>'
            f'<div class="reader-controls">{extra}<button class="small-btn" id="top" type="button">先頭へ</button></div></div><div class="progress" aria-hidden="true"><div id="progress-fill"></div></div></header>\n')


def transcript_of(no):
    """transcripts/episodeNN.json があれば読み込む（文字起こし・音声）"""
    path = f"transcripts/episode{no:02d}.json"
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


LOCK = ('<section class="protected-lock" id="protected-lock" aria-labelledby="protected-lock-title"><div class="protected-lock-card">'
        '<div class="protected-lock-mark" aria-hidden="true">🔒</div><h1 id="protected-lock-title">この話はパスワードが必要です</h1>'
        '<p>この話は限定公開です。<br>パスワードを入力すると漫画を読めます。</p>'
        '<form class="protected-lock-form" id="protected-lock-form"><label class="sr-only" for="protected-password">パスワード</label>'
        '<input id="protected-password" name="password" type="password" autocomplete="current-password" placeholder="パスワード" required>'
        '<button id="protected-submit" type="submit">読む</button><p class="protected-lock-error" id="protected-error" role="alert" aria-live="polite"></p></form></div></section>')


def episode_page(ep):
    no, v = ep["no"], vol_of_ep.get(ep["no"])
    tr = transcript_of(no)
    title = f'第{no}話「{ep["title"]}」 | {TITLE}'
    desc = f'オリジナル漫画『{TITLE}』第{no}話「{ep["title"]}」'
    prot = bool(ep.get("protected"))
    items = [(img(f"images/episodes/episode{no:02d}-{p:03d}"), f"第{no}話 ページ{p}", f' data-i="{p - 1}"')
             for p in range(1, ep["pages"] + 1)] if not prot else []
    vattr = f' data-volume-href="volume{v["no"]}.html" data-volume-label="第{v["no"]}巻"' if v else ""
    nav = f'<div class="episode-nav"><a class="small-btn" href="volume{v["no"]}.html">第{v["no"]}巻の目次</a></div>' if v else ""
    footer = '<a href="index.html">HOME</a>' + (f'　|　<a href="volume{v["no"]}.html">第{v["no"]}巻</a>' if v else "")
    extra = ('<button class="small-btn tr-btn" id="listen-toggle" type="button" aria-pressed="false">'
             '<span aria-hidden="true">🔊</span> 文字・音声</button>') if tr else ""
    trjs = ""
    if tr:
        blob = json.dumps(tr, ensure_ascii=False).replace("</", "<\\/")
        trjs = (f'<script type="application/json" id="transcript">{blob}</script>'
                f'<script src="js/listen.js?v={V_LISTEN}" defer></script>')
    html = (head(title, desc, f"{BASE}episode{no}.html", "article", theme=True)
            + reader_top("index.html", "← 話一覧へ戻る", extra)
            + f'<main class="viewer" id="viewer"{vattr}>\n{pages_html(items, 2) if not prot else prot_pages(no, ep["pages"])}\n</main>\n{nav}'
            + reader_tail(ep["pages"], footer).replace("</body>", trjs + (f'<script src="js/protected-reader.js?v={V_PROT}"></script>' if prot else "") + "</body>"))
    if prot:
        html = html.replace('<body class="reader-page">', '<body class="reader-page protected-locked">' + LOCK, 1)
    return html


def prot_pages(no, n):
    return "\n".join(f'    <div class="manga-page" data-i="{p - 1}"><img data-protected-src="protected/episode{no:02d}-{p:03d}.akg" alt="第{no}話 ページ{p}"></div>'
                     for p in range(1, n + 1))


def volume_page(v):
    no = v["no"]
    title = f'第{no}巻 | {TITLE}'
    desc = f'オリジナル漫画『{TITLE}』第{no}巻'
    items = [(vol_cover(v), f"{TITLE} 第{no}巻 表紙", ' data-volume-cover="true"')]
    i = 0
    for n in v["episodes"]:
        ep = ep_by_no[n]
        for p in range(1, ep["pages"] + 1):
            items.append((img(f"images/episodes/episode{n:02d}-{p:03d}"), f"第{n}話 ページ{p}", f' data-i="{i}"'))
            i += 1
    footer = '<a href="index.html">HOME</a>　|　<a href="index.html#comics">コミックス一覧</a>'
    return (head(title, desc, f"{BASE}volume{no}.html", "article", theme=True)
            + reader_top("index.html#comics", "← コミックス一覧へ戻る")
            + f'<main class="viewer" id="viewer" data-volume-reader="true">\n{pages_html(items, 3)}\n</main>\n'
            + reader_tail(len(items), footer))


def not_found_page():
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>ページが見つかりません | {e(TITLE)}</title>
<link rel="icon" href="{BASE}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{BASE}css/style.css?v={V_CSS}"></head>
<body class="top-page"><div class="jp-shell"><div class="nf">
<p class="nf-code" aria-hidden="true">404</p>
<h1>ページが見つかりません</h1>
<p>URLがまちがっているか、ページが移動したのかもしれません。</p>
<div class="jp-actions" style="justify-content:center"><a class="jp-btn primary" href="{BASE}">{e(TITLE)}のトップへ</a></div>
</div></div><footer>{e(site["copyright"])}</footer></body></html>
'''


def write(path, text):
    open(path, "w", encoding="utf-8", newline="\n").write(text)
    print("生成:", path)


write("index.html", index_page())
for ep in episodes:
    write(f"episode{ep['no']}.html", episode_page(ep))
for v in volumes:
    write(f"volume{v['no']}.html", volume_page(v))
write("404.html", not_found_page())
print("完了")
