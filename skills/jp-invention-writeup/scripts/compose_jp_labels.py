#!/usr/bin/env python3
"""ブランクレイアウト PNG に日本語ラベルを合成する。

Banana で生成した「暗いティール #0E6F69 の矩形がテキスト枠」になっている
レイアウト画像を入力に取り、JSON 仕様の labels を上から PIL で描画する。

枠の検出方針:
- ピクセル単位で #0E6F69 近傍色を mask
- 自前 flood-fill で連結成分の bounding box を抽出
- y0 → x0 の順でソート（上→下、左→右）
- role 別 (title / step / callout) にバケットを当てる

枠数とラベル数が合わない場合は、`overrides` で座標を JSON 直書きできる。

入力 JSON 仕様の labels 部分:
{
  "labels": {
    "title": {"text": "<案件名>ワークフロー"},
    "steps": [
      {"title": "<ステップ1名>", "desc": "<ステップ1の補足>"},
      ...
    ],
    "callouts": [
      {"title": "<コールアウト1>", "desc": "<コールアウト1の補足>"},
      ...
    ],
    "fonts": {
      "title_size": 96,
      "step_title_size": 40, "step_desc_size": 26,
      "callout_title_size": 44, "callout_desc_size": 28
    },
    "overrides": {
      "title_box": [x0, y0, x1, y1],
      "step_boxes": [[...], [...], ...],
      "callout_boxes": [[...], [...], ...]
    }
  }
}

Usage:
    python3 compose_jp_labels.py \\
        --image work/banana-blank/overview.png \\
        --spec work/banana-specs/overview.json \\
        --output work/figures-rendered/overview.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


# ---- フォント探索 ----
# Linux/WSL/Mac それぞれで通る候補を順に試す
FONT_CANDIDATES_REGULAR = [
    "/mnt/c/Windows/Fonts/NotoSansJP-VF.ttf",
    "/mnt/c/Windows/Fonts/YuGothR.ttc",
    "/mnt/c/Windows/Fonts/meiryo.ttc",
    "/mnt/c/Windows/Fonts/msgothic.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
]
FONT_CANDIDATES_BOLD = [
    "/mnt/c/Windows/Fonts/YuGothB.ttc",
    "/mnt/c/Windows/Fonts/meiryob.ttc",
    "/mnt/c/Windows/Fonts/NotoSansJP-VF.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/Library/Fonts/Hiragino Sans GB.ttc",
]


def _find_font(candidates) -> str:
    for p in candidates:
        if Path(p).exists():
            return p
    raise SystemExit(
        "Japanese font not found. Install Noto Sans CJK "
        "(`apt install fonts-noto-cjk`) or run on WSL where Yu Gothic / Meiryo are available."
    )


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = _find_font(FONT_CANDIDATES_BOLD if bold else FONT_CANDIDATES_REGULAR)
    try:
        return ImageFont.truetype(path, size, index=0)
    except Exception:
        return ImageFont.truetype(_find_font(FONT_CANDIDATES_REGULAR), size)


# ---- テキスト枠（ダーク・ティール領域）の検出 ----
def detect_text_boxes(
    image: Image.Image,
    color_target=(14, 111, 105),
    tol=40,
    min_area=20000,
    min_aspect=1.5,
) -> list[tuple[int, int, int, int]]:
    """ダーク・ティール矩形領域の bounding box リストを返す。

    min_area と min_aspect で小さな影やアイコン内部の暗領域を除外する
    (テキスト枠は基本的に「広く・横長」)。

    Returns:
        [(x0, y0, x1, y1), ...]  サイズ降順
    """
    px = image.convert("RGB").load()
    W, H = image.size
    tr, tg, tb = color_target

    # mask: 各ピクセルがターゲット色の近傍か
    mask = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            if (
                abs(r - tr) <= tol
                and abs(g - tg) <= tol
                and abs(b - tb) <= tol
                # かつ teal 系（青緑優位、赤は低い）
                and r < 60
                and g >= b - 20
                and g < 180
                and b < 180
            ):
                mask[y][x] = True

    visited = [[False] * W for _ in range(H)]
    boxes = []
    for sy in range(H):
        for sx in range(W):
            if not mask[sy][sx] or visited[sy][sx]:
                continue
            # iterative DFS
            stack = [(sy, sx)]
            visited[sy][sx] = True
            min_y, max_y, min_x, max_x = sy, sy, sx, sx
            size = 0
            while stack:
                y, x = stack.pop()
                size += 1
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny][nx] and not visited[ny][nx]:
                        visited[ny][nx] = True
                        stack.append((ny, nx))
            w = max_x - min_x + 1
            h = max_y - min_y + 1
            if size < min_area:
                continue
            if h == 0 or (w / h) < min_aspect:
                continue
            boxes.append((size, min_x, min_y, max_x, max_y))

    boxes.sort(reverse=True)
    return [(x0, y0, x1, y1) for _, x0, y0, x1, y1 in boxes]


def classify_boxes(
    boxes: list[tuple[int, int, int, int]],
    image_height: int,
) -> dict:
    """検出枠を縦位置で title / steps / callouts に分類する。

    ヒューリスティック:
    - 画像上から30% より上 → title 候補
    - それ以外で同じ y 帯にまとまるもの → steps（最も大きな帯）と callouts（次の帯）
    - 結果として steps と callouts はそれぞれ x 昇順で並べる
    """
    if not boxes:
        return {"title_box": None, "step_boxes": [], "callout_boxes": []}

    # y 中心でクラスタリング（簡易: y 範囲ごとに bucket）
    rows = []
    for box in boxes:
        x0, y0, x1, y1 = box
        cy = (y0 + y1) // 2
        placed = False
        for row in rows:
            row_cy = sum((b[1] + b[3]) // 2 for b in row) / len(row)
            if abs(cy - row_cy) < 80:  # 80px 以内なら同じ行
                row.append(box)
                placed = True
                break
        if not placed:
            rows.append([box])

    # y 昇順で行を並べ替え
    rows.sort(key=lambda r: sum((b[1] + b[3]) // 2 for b in r) / len(r))

    result = {"title_box": None, "step_boxes": [], "callout_boxes": []}

    # 一番上の行で、かつ y_center < 画像の20%以下なら title とみなす
    for row in rows:
        row.sort(key=lambda b: b[0])  # x 昇順
    if rows and len(rows[0]) == 1:
        x0, y0, x1, y1 = rows[0][0]
        if (y0 + y1) / 2 < image_height * 0.20:
            result["title_box"] = rows[0][0]
            rows = rows[1:]

    # 行数が一番多いものを steps、それ以外で次に多いものを callouts と推定
    rows_by_count = sorted(enumerate(rows), key=lambda t: -len(t[1]))
    if rows_by_count:
        step_idx, step_row = rows_by_count[0]
        result["step_boxes"] = step_row
        for idx, row in enumerate(rows):
            if idx != step_idx and len(row) >= 1:
                result["callout_boxes"].extend(row)
        # callout は y, x 順でソート
        # 同じ行帯（y_center が 80px 以内）は同一バケット扱いにしてから x 昇順
        result["callout_boxes"].sort(key=lambda b: (((b[1] + b[3]) // 2) // 80, b[0]))
    return result


# ---- 描画ヘルパー ----
WHITE = (255, 255, 255, 255)
SOFT_WHITE = (220, 240, 240, 255)


def draw_centered(draw: ImageDraw.ImageDraw, text: str, cx: int, cy: int, fnt, fill=WHITE):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((cx - w // 2 - bbox[0], cy - h // 2 - bbox[1]), text, font=fnt, fill=fill)


def draw_card_text(
    draw: ImageDraw.ImageDraw,
    title: str,
    desc: Optional[str],
    box: tuple[int, int, int, int],
    title_size: int,
    desc_size: int,
):
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    f_t = load_font(title_size, bold=True)
    if desc:
        # title 上 / desc 下
        draw_centered(draw, title, cx, cy - (y1 - y0) // 6, f_t, fill=WHITE)
        f_d = load_font(desc_size, bold=False)
        draw_centered(draw, desc, cx, cy + (y1 - y0) // 5, f_d, fill=SOFT_WHITE)
    else:
        draw_centered(draw, title, cx, cy, f_t, fill=WHITE)


# ---- メイン処理 ----
def compose(spec_path: Path, image_path: Path, out_path: Path) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    labels = spec.get("labels") or {}
    fonts_cfg = labels.get("fonts") or {}
    title_size = fonts_cfg.get("title_size", 96)
    step_t_size = fonts_cfg.get("step_title_size", 40)
    step_d_size = fonts_cfg.get("step_desc_size", 26)
    cal_t_size = fonts_cfg.get("callout_title_size", 44)
    cal_d_size = fonts_cfg.get("callout_desc_size", 28)

    img = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    overrides = labels.get("overrides") or {}
    title_box = tuple(overrides["title_box"]) if overrides.get("title_box") else None
    step_boxes = [tuple(b) for b in overrides.get("step_boxes", [])]
    callout_boxes = [tuple(b) for b in overrides.get("callout_boxes", [])]

    # overrides が完全に揃っていない場合は自動検出で補完
    if not (title_box and step_boxes):
        detected = detect_text_boxes(img)
        classified = classify_boxes(detected, img.height)
        if not title_box:
            title_box = classified["title_box"]
        if not step_boxes:
            step_boxes = classified["step_boxes"]
        if not callout_boxes:
            callout_boxes = classified["callout_boxes"]

    # title 描画
    title = labels.get("title")
    if title:
        text = title["text"] if isinstance(title, dict) else str(title)
        size = (title.get("size") if isinstance(title, dict) else None) or title_size
        f = load_font(size, bold=True)
        if title_box:
            x0, y0, x1, y1 = title_box
            cx = (x0 + x1) // 2
            cy = (y0 + y1) // 2
            draw_centered(draw, text, cx, cy, f, fill=WHITE)
        else:
            # フォールバック: 画像上部中央
            bbox = draw.textbbox((0, 0), text, font=f)
            tw = bbox[2] - bbox[0]
            draw.text(((img.width - tw) // 2, 30), text, font=f, fill=WHITE)

    # step 描画
    steps = labels.get("steps") or []
    n = min(len(steps), len(step_boxes))
    for i in range(n):
        s = steps[i]
        draw_card_text(
            draw,
            s.get("title", ""),
            s.get("desc"),
            step_boxes[i],
            title_size=s.get("title_size", step_t_size),
            desc_size=s.get("desc_size", step_d_size),
        )

    # callout 描画
    callouts = labels.get("callouts") or []
    n = min(len(callouts), len(callout_boxes))
    for i in range(n):
        c = callouts[i]
        draw_card_text(
            draw,
            c.get("title", ""),
            c.get("desc"),
            callout_boxes[i],
            title_size=c.get("title_size", cal_t_size),
            desc_size=c.get("desc_size", cal_d_size),
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, optimize=True)

    return {
        "output": str(out_path),
        "title_box": list(title_box) if title_box else None,
        "step_boxes": [list(b) for b in step_boxes],
        "callout_boxes": [list(b) for b in callout_boxes],
        "steps_drawn": min(len(steps), len(step_boxes)),
        "callouts_drawn": min(len(callouts), len(callout_boxes)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", required=True, help="Blank layout PNG from build_banana_image.py")
    ap.add_argument("--spec", required=True, help="JSON spec with labels block")
    ap.add_argument("--output", required=True, help="Output composited PNG")
    args = ap.parse_args()

    result = compose(
        Path(args.spec).expanduser().resolve(),
        Path(args.image).expanduser().resolve(),
        Path(args.output).expanduser().resolve(),
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
