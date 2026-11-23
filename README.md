# アペックスキングネス

SAKU制作のオリジナル漫画『アペックスキングネス』の公開サイトです（GitHub Pages）。
公開URL: https://saku3298.github.io/apex-kingness/

画面はジャンププラス風です。縦向きは1ページ表示、横向きは右から左の2ページ見開きで読めます。

## フォルダ構成

| 場所 | 役割 |
|---|---|
| `work.json` | 作品情報・話数・巻・関連作品のデータ（**ここを編集します**） |
| `tools/build.py` | `work.json` から全HTMLを生成します |
| `tools/optimize_images.py` | 画像をWebPに変換して軽くします |
| `tools/make_ogp.py` | SNS共有用の画像を `images/ogp/default.jpg` に生成します |
| `css/style.css` | 画面のデザイン（トップ・ビューア・404） |
| `js/viewer.js` | ビューア（スワイプ・見開き・続きから読む） |
| `js/top.js` | トップページ（タブ切り替え・話数の並べ替え） |
| `images/episodes/` | 各話のページ画像 `episode01-001.webp` …（話2桁-ページ3桁） |
| `images/volumes/` | 単行本の表紙 `volume01-cover.webp` |
| `images/thumbs/` | 話一覧のサムネイル `episode01.webp` |
| `images/related/` | 「同じ作者の作品」の表紙 |
| `images/work/` | トップのヒーロー画像・作者画像 |
| `images/ogp/` | SNS共有用の画像（JPG） |
| `assets/favicon.svg` | タブのアイコン |
| `index.html`, `episodeN.html`, `volumeN.html`, `404.html` | **自動生成されるので直接編集しません** |

## 第2話を追加する手順

1. 画像を置く
   - 本文: `images/episodes/episode02-001.jpg`, `episode02-002.jpg` …（JPG／PNGのままで構いません）
   - サムネイル: `images/thumbs/episode02.jpg`（横長 568×216 程度）
2. `work.json` の `episodes` に追記する
   ```json
   { "no": 2, "title": "第2話のタイトル", "date": "2026-12-05" }
   ```
   `date` は公開日です（話一覧に「2026年12月5日」と出ます。公開から30日以内は「新着」も付きます）。
   単行本にも入れる場合は、`volumes` の該当巻の `episodes` に `2` を足します（新しい巻は `images/volumes/volume02-cover.jpg` を置いて、`volumes` に追加）。
3. 変換と生成を実行する
   ```
   python3 tools/optimize_images.py --delete-originals   # WebPに変換（元のJPG/PNGは消えます）
   python3 tools/make_ogp.py                             # 共有用画像（話数の表示が変わります）
   python3 tools/build.py                                # HTML生成
   ```
   （`optimize_images.py` と `make_ogp.py` は Pillow が必要です: `pip install pillow`）
4. 変更したファイルをGitHubにアップロードする

ページ数は画像の枚数から自動で数えます。

## 操作方法

- PC: 画面の左右ボタン、← → キー、マウスホイールでページ移動
- スマートフォン縦向き: 1ページ表示・横スワイプ
- スマートフォン横向き: 右に若いページを置く2ページ見開き
- 途中で閉じても、次に開いたときに「続きから読む」を選べます（読んだ位置は読者の端末にだけ保存されます）

## GitHub Pages の公開設定

1. GitHubで `apex-kingness` というPublicリポジトリを作る
2. このフォルダの**中身**をリポジトリ直下にアップロードする（フォルダごと入れない）
3. 「Settings」→「Pages」→ Source を「Deploy from a branch」、Branch を「main」、フォルダを「/ (root)」にして「Save」

## 注意

- 元の高解像度データ（PDFなど）は、GitHubとは別の場所にも保管してください。
- `index.html` などの生成物を直接編集すると、次の生成で上書きされます。

## 登場人物を追加・変更する

作品情報タブの「登場人物」は、`work.json` の `characters` から作られます。

```json
{ "name": "名前", "reading": "よみ", "image": "ファイル名（拡張子なし）", "desc": "ひとこと説明",
  "main": true, "role": "主人公", "note": "補足（小さく表示）",
  "cameo": [ { "label": "他作品にも登場", "url": "https://…" } ] }
```

顔の画像は正方形で `images/characters/` に置きます（400×400程度）。`main` は主人公だけに付けます。

## タイトル・キャッチコピーのフォントについて

トップのタイトルとキャッチコピーには、次の2つのフォントを使っています（どちらもSIL Open Font License）。

- タイトル: Dela Gothic One → `assets/fonts/title.woff2`
- キャッチコピー: Shippori Mincho B1（ExtraBold）→ `assets/fonts/catch.woff2`

通信量を減らすため、**今使っている文字だけ**を切り出した軽量版です。
`work.json` の `title` や `catch_copy` を変えて、文字が新しくなったときは、フォントの作り直しが必要です
（作り直さないと、新しい文字だけ標準のフォントで表示されます）。Claudeに「フォントを作り直して」と頼めば対応できます。

ヒーローの小見出し（赤い線の横の一言）は、今は出していません。出したいときは `work.json` の `work.kicker` に書きます。

## 文字起こし・音声（読み上げ）

- 各話の文字起こしは `transcripts/episodeNN.json` に書きます。ファイルがある話だけ、読書画面に「🔊 文字・音声」ボタンが出ます。
- `pages` の中に、ページ番号ごとに行を並べます。`kind` は `title`（題）・`narr`（語り）・`say`（セリフ）。
  - `ja`：日本語、`en`：英語、`audio`：日本語の音声ファイル（`audio/episodeNN/p001-01.mp3` など）
  - `noread: true`：画面に出すが読み上げない（作品タイトルなど）
  - `en_say`：英語の読み上げだけ別の言い方にしたいとき
- 日本語の音声は VOICEVOX（冥鳴ひまり）で作ります。クレジット「VOICEVOX:冥鳴ひまり」を必ず表示します（読書画面と作品情報に自動で出ます）。
- 英語は、見る人の端末の声（女性）で読み上げます。
- あらすじの英語・音声は `work.json` の `summary_en`・`catch_copy_en`・`title_en`・`summary_audio`・`voice_credit` です。
- 読み方を直したいとき（アクセントなど）は、音声ファイルを作り直します。画面の文字は `ja` のままで変わりません。
