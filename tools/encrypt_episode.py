#!/usr/bin/env python3
"""パスワード付きの話の画像（.akg）を作ります。

使い方（リポジトリのルートで）:
    python3 tools/encrypt_episode.py 2 原稿.pdf
    python3 tools/encrypt_episode.py 2 画像1.jpg 画像2.jpg …

  - PDF（1ページ＝1枚のスキャン）か画像を渡します。幅1105pxのWebPにしてから暗号化します。
  - 画像は渡した順に protected/episode02-001.akg, 002.akg … になります（前の分は消して作り直します）。
  - パスワードは実行中に聞かれます。環境変数 AKG_PASSWORD に入れておくこともできます。
  - そのあと work.json の話に "protected": true を付けて python3 tools/build.py を実行します。

必要なもの: pip install cryptography pillow pymupdf
※ .akg は「ファイルの場所と名前」も鍵の一部です。名前を変えると読めなくなります。
形式: 'AKG1' + IV(12バイト) + AES-GCM暗号文。鍵は PBKDF2-SHA256（15万回）。js/protected-reader.js と対です。
"""
import getpass, glob, io, os, sys
from PIL import Image
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALT, ITERATIONS, WIDTH = b"ApexKingness2026", 150000, 1105

if len(sys.argv) < 3 or not sys.argv[1].isdigit():
    sys.exit(__doc__)
no, files = int(sys.argv[1]), [os.path.abspath(f) for f in sys.argv[2:]]
os.chdir(ROOT)
password = os.environ.get("AKG_PASSWORD") or getpass.getpass("パスワード: ")
if not os.environ.get("AKG_PASSWORD") and getpass.getpass("もう一度: ") != password:
    sys.exit("パスワードが一致しません。")


def images():
    for f in files:
        if f.lower().endswith(".pdf"):
            import pymupdf
            d = pymupdf.open(f)
            for page in d:
                x = page.get_images()[0][0]
                yield Image.open(io.BytesIO(d.extract_image(x)["image"]))
        else:
            yield Image.open(f)


key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=ITERATIONS).derive(password.encode("utf-8"))
os.makedirs("protected", exist_ok=True)
for old in glob.glob(f"protected/episode{no:02d}-*.akg"):
    os.remove(old)
n = 0
for n, im in enumerate(images(), 1):
    im = im.convert("RGB")
    im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=82, method=6)
    path = f"protected/episode{no:02d}-{n:03d}.akg"
    iv = os.urandom(12)
    open(path, "wb").write(b"AKG1" + iv + AESGCM(key).encrypt(iv, buf.getvalue(), path.encode("utf-8")))
    print("作成:", path)
print(f"\n{n}枚を暗号化しました。work.json の第{no}話に \"protected\": true を付けて、python3 tools/build.py を実行してください。")
