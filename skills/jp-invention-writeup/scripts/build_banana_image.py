#!/usr/bin/env python3
"""Banana (Gemini Nano Banana) 経由でテキストなしのブランクレイアウトPNGを生成。

このスクリプトは Phase 2 の発明説明資料PPTX用ヒーロー画像や概念図の
**第1段階**（テキストなしレイアウト生成）を担う。
第2段階の日本語ラベル合成は compose_jp_labels.py に分離している。

理由: Gemini の日本語フォントレンダリングが不安定で、長い和文ラベルは
頻繁に文字化けする。テキストを最初から含めず、後段で PIL + Yu Gothic /
Noto Sans JP で確実に合成する二段階方式を強制する。

入力 JSON 仕様 (templates/banana-spec.example.json 参照):
{
  "prompt": "...英文プロンプト。テキストなしを明示すること...",
  "aspect_ratio": "16:9",
  "resolution": "2K",
  "model": "gemini-3.1-flash-image-preview"
}

Usage:
    python3 build_banana_image.py \\
        --spec ~/patent/<案件名>/work/banana-specs/overview.json \\
        --output ~/patent/<案件名>/work/banana-blank/overview.png
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

try:
    import urllib.request
except ImportError:
    print("urllib required", file=sys.stderr)
    sys.exit(1)


API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def get_api_key() -> str:
    for env in ("GOOGLE_AI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        v = os.environ.get(env)
        if v:
            return v
    raise SystemExit(
        "API key not found. Set GEMINI_API_KEY or GOOGLE_AI_API_KEY environment variable."
    )


def reinforce_no_text(prompt: str) -> str:
    """Geminiへ「テキストを描画するな」を強く伝える尾札を付与する。

    呼び出し側のプロンプトが既にこの指示を含んでいても二重に書いて損はしない。
    日本語ラベル合成を後段で行うため、画像内には1文字も描かれてほしくない。
    """
    suffix = (
        "\n\nIMPORTANT CONSTRAINT: NEVER render any text, letters, words, "
        "alphabets, kanji, kana, digits, captions, labels, or typographic "
        "glyphs anywhere in this image. Leave every text area as a solid "
        "darker-teal #0E6F69 rectangle — these blank zones will have Japanese "
        "text composited on top in a post-processing step. This is critical: "
        "any text inside the image will be discarded."
    )
    if "NEVER render any text" in prompt:
        return prompt
    return prompt + suffix


def generate(spec: dict, output_path: Path, api_key: str) -> dict:
    prompt = reinforce_no_text(spec["prompt"])
    model = spec.get("model", "gemini-3.1-flash-image-preview")
    aspect = spec.get("aspect_ratio", "16:9")
    resolution = spec.get("resolution", "2K")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect,
                "imageSize": resolution,
            },
        },
    }

    url = f"{API_BASE}/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}")

    data = json.loads(body)
    candidates = data.get("candidates") or []
    for cand in candidates:
        for part in cand.get("content", {}).get("parts", []) or []:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(base64.b64decode(inline["data"]))
                return {
                    "path": str(output_path),
                    "model": model,
                    "aspect_ratio": aspect,
                    "resolution": resolution,
                }
    raise SystemExit(f"No image returned. Response: {json.dumps(data)[:500]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True, help="JSON spec file")
    ap.add_argument("--output", required=True, help="Output PNG path")
    args = ap.parse_args()

    spec_path = Path(args.spec).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if "prompt" not in spec:
        raise SystemExit("spec must include 'prompt'")

    api_key = get_api_key()
    result = generate(spec, out_path, api_key)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
