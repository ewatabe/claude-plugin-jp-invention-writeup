#!/usr/bin/env python3
"""図面 JSON仕様 → HTMLファイル変換。

`work/figure-specs/figure-*.json` を読み、figure_type ごとに HTML テンプレを
適用してきれいな HTML を `work/figure-html/figure-*.html` に出力する。
後段で render_html.js (Puppeteer) で PNG 化し、build_figure_pptx.py で
.pptx に埋め込む。

対応モード:
- block_diagram : 構成図／ブロック図／ER図 (SVGで要素＋矢印＋参照符号)
- flowchart     : 縦フロー（start/end/process/decision の形状区別、矢印に分岐ラベル）
- table         : 表形式（クリーンなテーブル）
- image         : 既存画像をそのまま埋込
- screen_mockup : UI画面モック（前面要素＋ヘッダ＋annotation）

Usage:
    python3 build_figure_html.py \\
        --specs ~/patent/<案件名>/work/figure-specs/ \\
        --out-dir ~/patent/<案件名>/work/figure-html/
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

# 図面スライドの 16:9 ピクセルサイズ（高解像度レンダ前提）
W = 1920
H = 1080


# ============================================================
# 共通スタイル
# ============================================================
COMMON_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Noto Sans JP', 'Yu Gothic UI', system-ui, sans-serif; }
.slide { width: %dpx; height: %dpx; background: #FFFFFF; position: relative; }

/* 図面ヘッダ（JPO実務準拠） */
.fig-header-doctype { position: absolute; left: 40px; top: 30px; font-size: 18pt; color: #000; }
.fig-header-figno   { position: absolute; left: 40px; top: 70px; font-size: 18pt; color: #000; }
.fig-header-figbig  { position: absolute; left: 50%%; top: 24px; transform: translateX(-50%%);
                      font-size: 28pt; font-weight: 700; color: #000; }
.fig-title-caption  { position: absolute; left: 50%%; top: 78px; transform: translateX(-50%%);
                      font-size: 14pt; color: #444; max-width: 80%%; text-align: center; white-space: nowrap; }

/* 図面本体エリア */
.fig-body { position: absolute; left: 60px; right: 60px; top: 130px; bottom: 60px; }

/* SVG 中の標準スタイル */
.comp-box   { fill: #FFFFFF; stroke: #1F1F1F; stroke-width: 2; }
.comp-box-rounded { fill: #FFFFFF; stroke: #1F1F1F; stroke-width: 2; rx: 8; ry: 8; }
.comp-cylinder-top { fill: #F8FAFC; stroke: #1F1F1F; stroke-width: 2; }
.comp-cylinder-body { fill: #FFFFFF; stroke: #1F1F1F; stroke-width: 2; }
.comp-diamond { fill: #FFFAEC; stroke: #1F1F1F; stroke-width: 2; }
.comp-label { font-family: 'Noto Sans JP'; font-size: 17pt; fill: #1F1F1F;
              text-anchor: middle; dominant-baseline: middle; }
.comp-sub   { font-family: 'Noto Sans JP'; font-size: 12pt; fill: #444;
              text-anchor: middle; }
.ref-num    { font-family: 'Noto Sans JP'; font-size: 14pt; font-weight: 700;
              fill: #1F4E79; }
.arrow      { fill: none; stroke: #1F1F1F; stroke-width: 2; }
.flow-label { font-family: 'Noto Sans JP'; font-size: 12pt; fill: #666; }
""" % (W, H)


def header_html(spec):
    """JPO実務に倣った図面ヘッダ HTML。"""
    n = spec.get("figure_number", "?")
    title = html.escape(spec.get("title", ""))
    return f"""
<div class="fig-header-doctype">【書類名】　図面</div>
<div class="fig-header-figno">【図{n}】</div>
<div class="fig-header-figbig">図 {n}</div>
<div class="fig-title-caption">{title}</div>
"""


# ============================================================
# block_diagram レンダリング
# ============================================================
SHAPE_KIND_TO_SVG = {
    "rectangle": "rect",
    "rounded_rectangle": "rect_rounded",
    "cylinder": "cylinder",
    "diamond": "diamond",
    "rhombus": "diamond",
}


def _svg_component(comp, scale_x, scale_y):
    """1コンポーネントを SVG として描画。
    pos/size は inch 単位（既存JSON互換）。SVG座標系に変換。
    """
    x, y = comp["pos"]
    w, h = comp["size"]
    label = comp.get("label", "")
    ref = comp.get("ref", "")
    shape = comp.get("shape", "rectangle")
    anchor = comp.get("ref_anchor", "top_left")

    sx = x * scale_x; sy = y * scale_y
    sw = w * scale_x; sh = h * scale_y

    out = []
    kind = SHAPE_KIND_TO_SVG.get(shape, "rect")
    if kind == "rect":
        out.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" class="comp-box"/>')
    elif kind == "rect_rounded":
        out.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" rx="10" ry="10" class="comp-box-rounded"/>')
    elif kind == "cylinder":
        ry = min(sh * 0.15, 20)
        # body
        out.append(
            f'<path d="M{sx:.1f},{sy+ry:.1f} '
            f'A{sw/2:.1f},{ry:.1f} 0 0 1 {sx+sw:.1f},{sy+ry:.1f} '
            f'L{sx+sw:.1f},{sy+sh-ry:.1f} '
            f'A{sw/2:.1f},{ry:.1f} 0 0 1 {sx:.1f},{sy+sh-ry:.1f} Z" '
            f'class="comp-cylinder-body"/>'
        )
        # top ellipse
        out.append(f'<ellipse cx="{sx+sw/2:.1f}" cy="{sy+ry:.1f}" rx="{sw/2:.1f}" ry="{ry:.1f}" class="comp-cylinder-top"/>')
    elif kind == "diamond":
        cx = sx + sw / 2; cy = sy + sh / 2
        pts = f"{cx:.1f},{sy:.1f} {sx+sw:.1f},{cy:.1f} {cx:.1f},{sy+sh:.1f} {sx:.1f},{cy:.1f}"
        out.append(f'<polygon points="{pts}" class="comp-diamond"/>')

    # ラベル（複数行対応）
    lines = label.split("\n")
    line_h = 22
    total_h = line_h * len(lines)
    start_y = sy + sh / 2 - total_h / 2 + line_h * 0.75
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{sx+sw/2:.1f}" y="{start_y + i * line_h:.1f}" class="comp-label">{html.escape(line)}</text>'
        )

    # 参照符号
    if ref:
        if anchor == "top_left":
            rx, ry = sx - 24, sy - 6
        elif anchor == "top_right":
            rx, ry = sx + sw + 6, sy - 6
        elif anchor == "bottom_left":
            rx, ry = sx - 24, sy + sh + 18
        elif anchor == "bottom_right":
            rx, ry = sx + sw + 6, sy + sh + 18
        else:
            rx, ry = sx - 24, sy - 6
        out.append(
            f'<text x="{rx:.1f}" y="{ry:.1f}" class="ref-num">{html.escape(ref)}</text>'
        )
    return "\n".join(out)


def _svg_arrow(frm, to, direction):
    """from→to の component を結ぶ矢印 (SVG path)。"""
    fx, fy = frm["pos"]; fw, fh = frm["size"]
    tx, ty = to["pos"]; tw, th = to["size"]
    fcx, fcy = fx + fw/2, fy + fh/2
    tcx, tcy = tx + tw/2, ty + th/2

    # 端点
    if abs(tcx - fcx) >= abs(tcy - fcy):
        if tcx > fcx:
            sx, sy = fx + fw, fcy
            ex, ey = tx, tcy
        else:
            sx, sy = fx, fcy
            ex, ey = tx + tw, tcy
    else:
        if tcy > fcy:
            sx, sy = fcx, fy + fh
            ex, ey = tcx, ty
        else:
            sx, sy = fcx, fy
            ex, ey = tcx, ty + th
    return sx, sy, ex, ey


ARROW_MARKER = """
<defs>
  <marker id="arrowhead" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
    <polygon points="0 0, 10 4, 0 8" fill="#1F1F1F"/>
  </marker>
</defs>
"""


def render_block_diagram(spec):
    body_w = W - 120
    body_h = H - 200
    components = spec.get("components", [])
    if not components:
        return ""

    # スペックは inch ベース（pptx slide 13.333 x 7.5 を想定したオリジナル設計）。
    # コンポーネントの実 x/y 範囲に合わせて HTML body 領域へフィット。
    pad = 0.15
    min_x = min(c["pos"][0] for c in components) - pad
    min_y = min(c["pos"][1] for c in components) - pad
    max_x = max(c["pos"][0] + c["size"][0] for c in components) + pad
    max_y = max(c["pos"][1] + c["size"][1] for c in components) + pad
    eff_w = max(max_x - min_x, 1)
    eff_h = max(max_y - min_y, 1)

    # アスペクト比を保ちつつ最大化
    scale = min(body_w / eff_w, body_h / eff_h)
    offset_x = (body_w - eff_w * scale) / 2
    offset_y = (body_h - eff_h * scale) / 2

    def tx(x): return offset_x + (x - min_x) * scale
    def ty(y): return offset_y + (y - min_y) * scale

    parts = [f'<svg viewBox="0 0 {body_w} {body_h}" width="{body_w}" height="{body_h}">', ARROW_MARKER]
    by_id = {}
    # 大きい順に先に描画（フレームが内側要素を覆ってしまうのを回避）
    for c in sorted(components, key=lambda c: -c["size"][0] * c["size"][1]):
        by_id[c["id"]] = c
        # スケール済み座標で _svg_component を呼ぶため、ローカル変換版を使う
        x0 = tx(c["pos"][0])
        y0 = ty(c["pos"][1])
        sw = c["size"][0] * scale
        sh = c["size"][1] * scale
        # 一時的に変換済み spec を渡す
        c_scaled = dict(c)
        c_scaled["pos"] = [x0 / scale + min_x, y0 / scale + min_y]
        c_scaled["size"] = c["size"]
        # _svg_component は scale_x/scale_y を使うので、シンプルに使い回す
        parts.append(_svg_component_at(c, x0, y0, sw, sh))
    for arr in spec.get("arrows", []):
        frm = by_id.get(arr["from"]); to = by_id.get(arr["to"])
        if not frm or not to:
            continue
        sx, sy, ex, ey = _svg_arrow(frm, to, arr.get("direction", "right"))
        parts.append(
            f'<line x1="{tx(sx):.1f}" y1="{ty(sy):.1f}" x2="{tx(ex):.1f}" y2="{ty(ey):.1f}" class="arrow" marker-end="url(#arrowhead)"/>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def _svg_component_at(comp, x, y, w, h):
    """既スケール済みの絶対座標 (x,y,w,h) で SVG component を描画。"""
    label = comp.get("label", "")
    ref = comp.get("ref", "")
    shape = comp.get("shape", "rectangle")
    anchor = comp.get("ref_anchor", "top_left")

    out = []
    kind = SHAPE_KIND_TO_SVG.get(shape, "rect")
    if kind == "rect":
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" class="comp-box"/>')
    elif kind == "rect_rounded":
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="10" ry="10" class="comp-box-rounded"/>')
    elif kind == "cylinder":
        ry = min(h * 0.15, 20)
        out.append(
            f'<path d="M{x:.1f},{y+ry:.1f} '
            f'A{w/2:.1f},{ry:.1f} 0 0 1 {x+w:.1f},{y+ry:.1f} '
            f'L{x+w:.1f},{y+h-ry:.1f} '
            f'A{w/2:.1f},{ry:.1f} 0 0 1 {x:.1f},{y+h-ry:.1f} Z" '
            f'class="comp-cylinder-body"/>'
        )
        out.append(f'<ellipse cx="{x+w/2:.1f}" cy="{y+ry:.1f}" rx="{w/2:.1f}" ry="{ry:.1f}" class="comp-cylinder-top"/>')
    elif kind == "diamond":
        cx = x + w / 2; cy = y + h / 2
        pts = f"{cx:.1f},{y:.1f} {x+w:.1f},{cy:.1f} {cx:.1f},{y+h:.1f} {x:.1f},{cy:.1f}"
        out.append(f'<polygon points="{pts}" class="comp-diamond"/>')

    # ラベル（複数行）
    lines = label.split("\n")
    line_h = 22
    total_h = line_h * len(lines)
    start_y = y + h / 2 - total_h / 2 + line_h * 0.75
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{x+w/2:.1f}" y="{start_y + i * line_h:.1f}" class="comp-label">{html.escape(line)}</text>'
        )

    # 参照符号
    if ref:
        if anchor == "top_left":
            rx, ry_ = x - 24, y - 6
        elif anchor == "top_right":
            rx, ry_ = x + w + 6, y - 6
        elif anchor == "bottom_left":
            rx, ry_ = x - 24, y + h + 18
        elif anchor == "bottom_right":
            rx, ry_ = x + w + 6, y + h + 18
        else:
            rx, ry_ = x - 24, y - 6
        out.append(
            f'<text x="{rx:.1f}" y="{ry_:.1f}" class="ref-num">{html.escape(ref)}</text>'
        )
    return "\n".join(out)


# ============================================================
# flowchart レンダリング
# ============================================================
def _estimate_label_width(label, font_pt=17):
    """日本語1文字 ≒ font_pt px、ASCII ≒ font_pt/2 px の粗推定。"""
    px = 0.0
    for line in label.split("\n"):
        w = 0.0
        for c in line:
            w += font_pt if ord(c) > 127 else font_pt * 0.55
        if w > px:
            px = w
    return px


def render_flowchart(spec):
    steps = spec.get("steps", [])
    transitions = spec.get("transitions", [])
    if not steps:
        return ""

    body_w = W - 120
    body_h = H - 200
    n = len(steps)

    # box幅：最長ラベルに合わせて決定（最大値で全box統一）
    max_label_px = max(_estimate_label_width(s.get("label", "")) for s in steps)
    box_w = min(max(int(max_label_px + 80), 380), body_w - 100)
    # ref numeral分の右余白を確保
    ref_pad = 80
    cx = body_w / 2 - ref_pad / 2  # 中央をref分だけ左に

    # box高さとgapを縦に収まるよう動的に
    max_lines = max(s.get("label", "").count("\n") + 1 for s in steps)
    box_h_base = 50 + max_lines * 22
    # 必要総高さ
    def total_h(bh, gap):
        return n * bh + (n - 1) * gap
    gap = 24
    box_h = box_h_base
    while total_h(box_h, gap) > body_h and box_h > 36:
        box_h -= 2
        if gap > 12:
            gap -= 1
    start_y = max(0, (body_h - total_h(box_h, gap)) / 2)

    parts = [f'<svg viewBox="0 0 {body_w} {body_h}" width="{body_w}" height="{body_h}">', ARROW_MARKER]
    positions = {}
    for i, step in enumerate(steps):
        y = start_y + i * (box_h + gap)
        sid = step["id"]
        positions[sid] = (cx - box_w/2, y, box_w, box_h)
        t = step.get("type", "process")
        label = step.get("label", "")
        ref = step.get("ref", "")
        if t == "start" or t == "end":
            parts.append(f'<rect x="{cx-box_w/2:.1f}" y="{y:.1f}" width="{box_w}" height="{box_h}" rx="{box_h/2:.0f}" ry="{box_h/2:.0f}" class="comp-box-rounded"/>')
        elif t == "decision":
            pts = f"{cx},{y:.1f} {cx+box_w/2:.1f},{y+box_h/2:.1f} {cx},{y+box_h:.1f} {cx-box_w/2:.1f},{y+box_h/2:.1f}"
            parts.append(f'<polygon points="{pts}" class="comp-diamond"/>')
        else:
            parts.append(f'<rect x="{cx-box_w/2:.1f}" y="{y:.1f}" width="{box_w}" height="{box_h}" class="comp-box"/>')
        # ラベル（複数行対応）
        lines = label.split("\n")
        line_h = 22
        total_label_h = line_h * len(lines)
        start_label_y = y + box_h / 2 - total_label_h / 2 + line_h * 0.75
        for j, line in enumerate(lines):
            parts.append(
                f'<text x="{cx}" y="{start_label_y + j * line_h:.1f}" class="comp-label">{html.escape(line)}</text>'
            )
        # 参照符号 (右側、box外)
        if ref:
            parts.append(f'<text x="{cx + box_w/2 + 14:.1f}" y="{y + box_h/2 + 6:.1f}" class="ref-num">{html.escape(ref)}</text>')

    # 矢印
    for tr in transitions:
        frm = positions.get(tr["from"]); to = positions.get(tr["to"])
        if not frm or not to:
            continue
        fx, fy, fw, fh = frm; tx, ty, tw, th = to
        sx_p = fx + fw/2; sy_p = fy + fh
        ex_p = tx + tw/2; ey_p = ty
        parts.append(
            f'<line x1="{sx_p:.1f}" y1="{sy_p:.1f}" x2="{ex_p:.1f}" y2="{ey_p:.1f}" class="arrow" marker-end="url(#arrowhead)"/>'
        )
        if tr.get("label"):
            mid_x = (sx_p + ex_p) / 2 + 14
            mid_y = (sy_p + ey_p) / 2 + 4
            parts.append(f'<text x="{mid_x:.1f}" y="{mid_y:.1f}" class="flow-label">{html.escape(tr["label"])}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


# ============================================================
# table レンダリング
# ============================================================
def render_table(spec):
    headers = spec.get("headers", [])
    rows = spec.get("rows", [])
    if not headers or not rows:
        return ""
    parts = ['<table class="data-table">']
    parts.append("<thead><tr>")
    for h in headers:
        parts.append(f"<th>{html.escape(str(h))}</th>")
    parts.append("</tr></thead>")
    parts.append("<tbody>")
    for row in rows:
        parts.append("<tr>")
        for v in row:
            parts.append(f"<td>{html.escape(str(v))}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


TABLE_CSS = """
.data-table { width: 100%; border-collapse: collapse; font-size: 14pt; }
.data-table thead { background: #F0F4F8; }
.data-table th { padding: 14px 12px; text-align: left; font-weight: 700; color: #1F1F1F;
                  border-bottom: 3px solid #1F4E79; }
.data-table td { padding: 12px; border-bottom: 1px solid #D1D9E0; color: #2C2C2C; vertical-align: top; }
.data-table tbody tr:nth-child(even) { background: #FAFBFC; }
"""


# ============================================================
# image レンダリング（外部画像をそのまま埋め込み）
# ============================================================
def render_image(spec):
    img = spec.get("image_path", "")
    if not img:
        return ""
    return f'<img src="file://{html.escape(img)}" style="max-width:100%;max-height:100%;object-fit:contain;"/>'


# ============================================================
# HTML 出力
# ============================================================
def render_figure_html(spec):
    ftype = spec.get("figure_type", "block_diagram")

    # html_file モード：spec の html_path が指す既存HTMLを使う（カスタム画面UIモック等）
    # 呼び出し側は render_figure_html ではなく main() で別経路扱いする
    if ftype == "html_file":
        return None  # main() で別処理

    if ftype == "block_diagram":
        body = render_block_diagram(spec)
        extra_css = ""
    elif ftype == "flowchart":
        body = render_flowchart(spec)
        extra_css = ""
    elif ftype == "table":
        body = render_table(spec)
        extra_css = TABLE_CSS
    elif ftype == "image":
        body = render_image(spec)
        extra_css = ".fig-body { display: flex; align-items: center; justify-content: center; }"
    else:
        body = f"<p>未対応 figure_type: {ftype}</p>"
        extra_css = ""

    title_caption = ""  # タイトルキャプションは header に含めるか body に含めるか

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>図 {spec.get('figure_number', '?')}: {html.escape(spec.get('title', ''))}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
{COMMON_CSS}
{extra_css}
</style>
</head>
<body>
<div class="slide">
  {header_html(spec)}
  <div class="fig-body">
    {body}
  </div>
</div>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--specs", required=True, help="figure-*.json のディレクトリ")
    ap.add_argument("--out-dir", required=True, help="HTML出力ディレクトリ")
    args = ap.parse_args()

    specs_dir = Path(args.specs).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(specs_dir.glob("figure-*.json"))
    if not json_files:
        print(f"ERROR: figure-*.json not found in {specs_dir}", file=sys.stderr)
        sys.exit(1)

    import shutil
    for jf in json_files:
        spec = json.loads(jf.read_text(encoding="utf-8"))
        n = spec.get("figure_number")
        out_html = out_dir / f"figure-{n:02d}.html"
        ftype = spec.get("figure_type", "block_diagram")

        if ftype == "html_file":
            # カスタムHTMLを丸ごとコピー
            src = Path(spec.get("html_path", "")).expanduser()
            if not src.is_absolute():
                src = jf.parent / src
            if not src.exists():
                print(f"  WARN: html_file not found: {src}")
                continue
            if src.resolve() != out_html.resolve():
                shutil.copyfile(src, out_html)
            print(f"  copied {out_html.name}: {spec.get('title', '')[:50]} (html_file)")
            continue

        html_text = render_figure_html(spec)
        if html_text is None:
            continue
        out_html.write_text(html_text, encoding="utf-8")
        print(f"  wrote {out_html.name}: {spec.get('title', '')[:50]}")


if __name__ == "__main__":
    main()
