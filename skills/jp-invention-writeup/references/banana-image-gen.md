# banana 画像生成オプション（Gemini Nano Banana）

Phase 2 の発明説明資料PPTX用「表紙ヒーロー画像」「概念図」「ワークフロー俯瞰図」を
AI画像生成で作るためのリファレンス。

このオプションは **ユーザーが明示的に依頼した場合のみ** 有効化する。
デフォルトは未使用。

## 設計思想：二段階方式（必須）

Gemini の画像生成（Nano Banana / Nano Banana 2）は **日本語フォントのレンダリングが不安定**。
長い和文ラベル・複雑なレイアウト・小さい文字では文字化けが頻発する。
特許文脈では文字化けは致命的（文言の正確さが要件）。

したがって、本スキルは **どんな場合も** 以下の二段階で生成する：

| ステップ | スクリプト | 役割 |
|---|---|---|
| Step A | `scripts/build_banana_image.py` | Gemini に **テキストなしの背景／フレームのみ** を描かせ、暗いティール `#0E6F69` の矩形をラベル枠として残す |
| Step B | `scripts/compose_jp_labels.py` | 枠を自動検出し、PIL + Yu Gothic / Noto Sans JP で日本語ラベルを上から合成 |

画像内に直接日本語を埋め込ませない。これは交渉の余地のない設計。

## クイックスタート

```bash
# 1. テンプレートを案件配下にコピー
mkdir -p ~/patent/<案件名>/work/banana-specs
cp ${SKILL_DIR}/templates/banana-spec.example.json \
   ~/patent/<案件名>/work/banana-specs/overview.json

# 2. overview.json を編集して prompt と labels を書く
#    (詳細は次節)

# 3. ブランクレイアウト生成
python3 ${SKILL_DIR}/scripts/build_banana_image.py \
  --spec ~/patent/<案件名>/work/banana-specs/overview.json \
  --output ~/patent/<案件名>/work/banana-blank/overview.png

# 4. 日本語ラベル合成
python3 ${SKILL_DIR}/scripts/compose_jp_labels.py \
  --image ~/patent/<案件名>/work/banana-blank/overview.png \
  --spec ~/patent/<案件名>/work/banana-specs/overview.json \
  --output ~/patent/<案件名>/work/figures-rendered/overview.png
```

## 環境前提

- `GEMINI_API_KEY` または `GOOGLE_AI_API_KEY` を環境変数に設定
- `Pillow` (pip install pillow)
- 日本語フォント（自動検出順）:
  1. WSL 経由: `/mnt/c/Windows/Fonts/NotoSansJP-VF.ttf`, `YuGothB.ttc`, `meiryo.ttc`, `msgothic.ttc`
  2. Linux: `/usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc`（`apt install fonts-noto-cjk`）
  3. macOS: `/Library/Fonts/Hiragino Sans GB.ttc`

## JSON 仕様の書き方

`templates/banana-spec.example.json` を雛形にする。
セクションは大きく **生成プロンプト** と **ラベル定義** の二段構え。

### 生成プロンプト側（Step A 用）

```json
{
  "prompt": "...英文プロンプト...",
  "aspect_ratio": "16:9",
  "resolution": "2K",
  "model": "gemini-3.1-flash-image-preview"
}
```

**プロンプト作成の原則:**

1. **必ず英文で書く。** Gemini は英文プロンプトのほうがレイアウト指示の解釈が安定する
2. **「テキストを描くな」を明示する。** スクリプト側で末尾に強い注意書きを自動付与するが、プロンプト本体にも書いておくと事故が減る:
   ```
   NEVER include any text, letters, words, numbers as labels,
   or typographic glyphs anywhere in the image
   ```
3. **ラベル枠は `#0E6F69` で塗る。** 自動検出が拾えるよう「a blank rectangle filled with slightly darker teal (#0E6F69)」と書く
4. **カードの色は `#14B8A6`、背景は `#0F172A`、アクセントは `#F97316`（コーラル）／ `#38BDF8`（シアン）を基調にする** と検出と統一感の両立がしやすい
5. **構図は明示的に。** 「6-step horizontal pipeline」「3 callout cards at the bottom」「title banner at top」のようにグリッドを言語化する
6. **アイコンは「small flat isometric icon」と書くと小さく抑えやすい** — 大きすぎるアイコンは枠検出と干渉する

**`aspect_ratio` の推奨:**
- 表紙・俯瞰図: `16:9`（プレゼン用標準）
- ヒーロー縦長: `4:5` または `3:4`
- バナー: `21:9`

**`resolution` の推奨:** `2K`（標準）。PPTX埋込なら 2K で十分。

### ラベル定義側（Step B 用）

```json
{
  "labels": {
    "title": {"text": "...", "size": 96},
    "steps": [
      {"title": "...", "desc": "..."},
      ...
    ],
    "callouts": [
      {"title": "...", "desc": "..."},
      ...
    ],
    "fonts": {
      "title_size": 96,
      "step_title_size": 40, "step_desc_size": 26,
      "callout_title_size": 44, "callout_desc_size": 28
    },
    "overrides": {}
  }
}
```

**書き方のコツ:**

| フィールド | 文字数の目安 | 役割 |
|---|---|---|
| `title.text` | 10〜20字 | 図全体のタイトル。画像上部の空きバナーに描画 |
| `steps[i].title` | 6〜10字 | ステップカードの主タイトル（太字） |
| `steps[i].desc` | 8〜15字 | ステップカードの説明（細字、1行） |
| `callouts[i].title` | 8〜14字 | コールアウトのキーワード（太字） |
| `callouts[i].desc` | 10〜16字 | コールアウトの補足（細字、1行） |

ラベル数と検出枠数が合わない場合は `overrides` で座標直書きできる：

```json
"overrides": {
  "title_box": [80, 30, 2670, 140],
  "step_boxes": [
    [161, 836, 457, 953],
    ...
  ],
  "callout_boxes": [
    [378, 1252, 834, 1400],
    ...
  ]
}
```

座標は `(x0, y0, x1, y1)` ピクセル単位。`overrides` が部分指定の場合、不足分は自動検出で補う。

## 枠の自動検出ロジック

`compose_jp_labels.py` の挙動:

1. 画像を RGB に展開
2. `#0E6F69 ± 40` の近傍色で mask 作成（ただし赤< 60 / 青緑優位）
3. 反復DFS で連結成分の bounding box を抽出
4. `min_area=20000` 以上 かつ `width/height >= 1.5` の枠だけ残す
5. y_center で行クラスタリング（80px 以内 → 同じ行）
6. 各行を x 昇順でソート
7. ロール割当:
   - 最上段に単独枠があり、画像高の20%以内に収まるなら **title_box**
   - 最も枠数が多い行を **step_boxes**
   - 残りの行を **callout_boxes**
8. ラベル配列の順序通りに描画

**自動検出が失敗するケース:**
- カードの背景色が `#14B8A6` でない（色が違うと mask が当たらない）
- 枠が小さすぎる（min_area で除外される）
- 枠が縦長（min_aspect で除外される）
- title バナーをティールで塗ってしまった（step扱いされる）

→ 上記のとき `overrides` で明示する。あるいは `prompt` を直して `#0E6F69` の塗りつぶしを徹底させる。

## 実例（同梱 example の出力イメージ）

`templates/banana-spec.example.json` は **医療情報処理系の案件を題材にした見本** として同梱されている。そのまま動作する：

- 6ステップ横並びパイプライン：データ収集 → 蓄積 → 知識ベース更新 → スコア算出 → 変化判定 → 担当者へ通知
- 3コールアウト：データ補正の要点／LLM要約コメント／関連メンバーへの波及
- タイトル：ワークフロー俯瞰図

新規案件で使うときは `template/banana-spec.example.json` を `~/patent/<案件名>/work/banana-specs/` 配下に複製し、`steps` / `callouts` / `title` を案件のドメイン語に書き換える。

検証コマンド：
```bash
python3 ${SKILL_DIR}/scripts/compose_jp_labels.py \
  --image <既に生成した blank PNG> \
  --spec ${SKILL_DIR}/templates/banana-spec.example.json \
  --output /tmp/test_compose.png
```

## トラブルシューティング

### Step A（Gemini生成）が失敗する

| 症状 | 原因 / 対処 |
|---|---|
| `HTTP 400: API key not valid` | `GEMINI_API_KEY` 未設定 or 期限切れ → https://aistudio.google.com/apikey で新しいキーを取得 |
| `HTTP 429 RESOURCE_EXHAUSTED` | レート制限。60秒待って再試行。無料枠は ~5〜15 RPM / ~20〜500 RPD |
| `IMAGE_SAFETY` finishReason | 安全フィルタ。プロンプトを抽象化／医療用語を弱める／"medical illustration" にトーンを変える |
| `Thinking level X is not supported` | `--thinking` を外す（gemini-3.1-flash-image-preview は thinking パラメタ非対応） |
| 画像内に英文テキストが描かれる | プロンプトの `NEVER include any text` を強める、または `imageConfig` を `responseModalities: ["IMAGE"]` のみに変更 |

### Step B（ラベル合成）が失敗する

| 症状 | 原因 / 対処 |
|---|---|
| `Japanese font not found` | `apt install fonts-noto-cjk`（Linux）、または WSL なら `/mnt/c/Windows/Fonts/` にアクセスできるか確認 |
| `steps_drawn` が 0 | ティール枠が検出されていない。`min_area` を下げる（CLI改修 or override 直書き） |
| ラベルが間違ったカードに描画される | 自動検出順がレイアウトと合っていない。`overrides.step_boxes` を明示 |
| 文字がはみ出す | ラベルを短くする、または `fonts.step_title_size` を小さくする |
| タイトルが画像外（上端） | ティールでタイトル枠が描かれていない → `overrides.title_box` を明示するか、プロンプトでタイトル枠を `#0E6F69` 塗りつぶしに |

### 検出枠の確認

`compose_jp_labels.py` の標準出力は JSON で検出座標を返す：

```json
{"output": "...", "title_box": null,
 "step_boxes": [[x0,y0,x1,y1], ...],
 "callout_boxes": [...],
 "steps_drawn": 6, "callouts_drawn": 3}
```

`step_boxes` の数 = ラベル数になっていれば正常。違っていれば `overrides` で修正。

## いつ banana を使わないか（再掲）

- **Phase 4 の図面.pptx** — 参照符号と編集性が必須
- **Phase 4 の技術説明書.docx** — テキスト主体、画像は figure-html ルート
- **Phase 2 の実施例UIモック** — `phases/2-invention-explainer-pptx.md` §4 の HTML/CSS 方式を維持
- **JPO提出用すべて** — 線画ベース原則

banana が活きるのは「発明説明用の俯瞰絵」「コンセプトイラスト」「表紙ヒーロー」など、
**文字の正確性より絵的訴求が効く局面** に限定する。

## コスト目安

| モデル | 解像度 | 単価 |
|---|---|---|
| gemini-3.1-flash-image-preview | 1K | ~$0.067 |
| gemini-3.1-flash-image-preview | 2K（推奨） | ~$0.134 |
| gemini-3.1-flash-image-preview | 4K | ~$0.268 |

1案件あたり試行錯誤含めても $1〜2 で収まる規模。Step B の PIL 合成は無料・即時。
