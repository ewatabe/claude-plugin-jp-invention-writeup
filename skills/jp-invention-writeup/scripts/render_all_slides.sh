#!/bin/bash
# 役員説明レベルのリッチスライド HTML を Chrome ヘッドレスで 1920x1080 PNG に
# 並列レンダリングするヘルパ。
#
# 使い方:
#   bash render_all_slides.sh <html-slides-dir> <figures-rendered-dir>
#
# 例:
#   bash ${SKILL_DIR}/scripts/render_all_slides.sh \
#       ~/patent/<案件名>/work/html-slides/ \
#       ~/patent/<案件名>/work/figures-rendered/
#
# 必須: google-chrome（または google-chrome-stable）
# 並列度: -P 4（4 プロセス並列）

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <html-slides-dir> <figures-rendered-dir>" >&2
  exit 1
fi

HTML_DIR="$(realpath "$1")"
OUT_DIR="$(realpath "$2")"

mkdir -p "$OUT_DIR"

if ! command -v google-chrome >/dev/null 2>&1 && ! command -v google-chrome-stable >/dev/null 2>&1; then
  echo "ERROR: google-chrome not found in PATH" >&2
  echo "       インストールしてから再実行してください (apt install google-chrome-stable 等)" >&2
  exit 2
fi

CHROME=$(command -v google-chrome 2>/dev/null || command -v google-chrome-stable)

echo "▸ HTML dir : $HTML_DIR"
echo "▸ OUT dir  : $OUT_DIR"
echo "▸ Chrome   : $CHROME"

# 既に PNG がある HTML はスキップ
for f in "$HTML_DIR"/*.html; do
  base=$(basename "$f" .html)
  if [ ! -f "$OUT_DIR/${base}.png" ]; then
    echo "$base"
  fi
done | xargs -I{} -P 4 bash -c '
  f="{}";
  '"$CHROME"' --headless --no-sandbox --hide-scrollbars \
    --window-size=1920,1080 --disable-gpu --virtual-time-budget=8000 \
    --screenshot="'"$OUT_DIR"'/${f}.png" \
    "file://'"$HTML_DIR"'/${f}.html" \
    > /dev/null 2>&1 && echo "OK: ${f}"
'

echo
echo "▸ rendered $(ls "$OUT_DIR"/*.png 2>/dev/null | wc -l) PNG files"
