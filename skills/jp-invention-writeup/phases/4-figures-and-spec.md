# Phase 4: 図面PPTX と 技術説明書DOCX

事務所に提出するメイン資料を作る。図面PPTXと、図面ごとの詳細説明＋請求項を含むWordファイル。

## 入力
- `~/patent/<案件名>/work/idea-expanded.md`
- `~/patent/<案件名>/output/請求項.txt`（Phase 3完了済み）

## 禁止事項

**Phase 4 の図面と技術説明書では AI画像生成（banana等）を使わない。** 理由：
- 参照符号（10, 11, 100, …）が再生成のたびに変わって明細書本文と整合しなくなる
- テキストが画像化されるため、事務所側で文言修正不可
- JPO提出図面はベクター線画ベースが基本で、ラスタAI画像は推奨されない

Phase 4 の図面は **JSON仕様 → build_figure_html.py → Puppeteer → build_figure_pptx.py** のHTMLレンダルートで作る。
表紙や概念図など「テキスト整合性が不要な絵」は Phase 2 で生成済みのものを必要に応じて流用してよい（その場合も技術説明書本文には埋め込まない）。

## 出力
- `~/patent/<案件名>/output/図面.pptx`
- `~/patent/<案件名>/output/技術説明書.docx`

## 手順

### 1. 図面リストを設計

まず **何枚の図を作るか** を決める。サンプル明細書（30枚）の構成を参考に、典型的な内訳は：

| # | 図種別 | 用途 |
|---|---|---|
| 図1 | システム全体構成図 | 主要構成要素（端末、サーバ、DB）とその関係 |
| 図2 | 処理部の内訳 | サーバの内部モジュール構成 |
| 図3 | ハードウェア構成 | CPU・メモリ・通信IFなどのHW構成 |
| 図4 | データ構造（ER図） | 主要データのエンティティ関連 |
| 図5〜 | データの例 | 各テーブル/構造体の具体的内容 |
| 図N | 処理フローチャート | 主要処理の流れ |
| 図N+1 | 画面例 | UIの実施例 |
| 最終図 | 全体方法のフローチャート | 全体の方法発明としての流れ |

中規模発明なら **10〜15枚**、大規模なら **20〜30枚** が目安。

図面リストは markdown 表で `work/figure-list.md` に整理：

```markdown
| 図番 | タイトル | 種別 | 主要構成要素 |
|---|---|---|---|
| 図1 | 〇〇システムの構成例 | 構成図 | 端末(1), サーバ(100), 外部DB(2) |
| 図2 | 〇〇サーバの処理部 | ブロック図 | 処理部(110), モジュールA(111), モジュールB(112) |
| ... |
```

### 2. ユーザー確認（図面リスト）

図面リストをユーザーに見せ、過不足・順序を確定する。**ここで確定させると後戻りが少ない。**

### 3. 各図面のJSON仕様を作る

確定したリストに沿って、各図ごとに `work/figure-specs/figure-N.json` を作る。
仕様の書式は `templates/figure-spec.example.json` に従う。

最小例：
```json
{
  "figure_number": 1,
  "title": "本実施形態に係る〇〇システムの構成例",
  "components": [
    {"id": "client", "label": "参加者端末", "ref": "1", "pos": [1, 2], "size": [2, 1]},
    {"id": "server", "label": "〇〇サーバ", "ref": "100", "pos": [4, 2], "size": [3, 1.5]},
    {"id": "db", "label": "施設内DB", "ref": "2", "pos": [4, 4], "size": [3, 1]}
  ],
  "arrows": [
    {"from": "client", "to": "server", "direction": "right"},
    {"from": "server", "to": "db", "direction": "down"}
  ]
}
```

- `ref` は参照符号。`references/figure-conventions.md` のルール（10, 20, 30… 主要要素／その下位を11,12…）に従う
- `pos` `size` は **インチ単位**、左上原点（pptxスライドサイズ 13.333 x 7.5 inch / 16:9）
- フローチャート専用の `"figure_type": "flowchart"` モードを使う場合は steps/branches を記述（テンプレ参照）

### 4. 図面PPTX生成

**画面例（UIモック）図面：`html_file` モード**

請求項対象がアプリ画面の場合、自動生成の block_diagram では不十分。カスタム HTMLでUIモックを書く：

```json
// figure-NN.json
{
  "figure_number": 11,
  "title": "差分提示画面の例を示す図",
  "figure_type": "html_file",
  "html_path": "../figure-html-custom/figure-11.html"
}
```

カスタムHTMLは `work/figure-html-custom/figure-NN.html` に保存（保護領域）。
詳細は `references/figure-conventions.md` の「画面例（UIモック）図面の作り方」参照。

**実施例HTML（Phase 2）を図面に流用するワークフロー（推奨）**

Phase 2 で発明説明資料の実施例スライド用に作った `work/figure-html-custom/exhibit-*.html`（カラー高品質UIモック）を、図面でもそのまま、または簡易化して再利用するのが効率的かつ整合性が高い。

1. **複製**: `cp work/figure-html-custom/exhibit-N-xxx.html work/figure-html-custom/figure-M.html`
2. **特許図面化の簡易化**を適用（最小限）:
   - **モノクロ寄り**: 背景色・主色は薄いグレー〜白に。アクセント色は黒〜濃グレーへ置換（特許庁提出時はモノクロ化されるため、最初から線画寄りで作っておくと事務所側の手戻りが減る）
   - **影・透過・装飾を削減**: `box-shadow` `backdrop-filter` 等は削除。罫線（`border: 1.5px solid #000` 等）で構造を表現
   - **画面フレーム枠を追加**: `.screen { border: 2.5px solid #000; }` で外周を明確化
   - **参照符号を `.ref` クラスで配置**: 主要要素ごとに `G1` `G2` …（または `H1`…）を画面要素の左外側 `-34px` に配置
   - **吹き出し・要素ハイライトは外す**: 装飾的説明は明細書本文に書く
3. **figure-spec.json を作成**: `figure_type: "html_file"` で上記HTMLを参照
4. **明細書本文との整合**: 参照符号のラベルを `work/figure-descriptions.md` の `【符号の説明】` セクションと一致させる

これによりPhase 2 と Phase 4 でUIの構造（タブ名・パネル名・配置）が一貫し、進歩性主張で「実施例画面≒図面の画面例」と説明できる。

カラーで残したい場合（社内提出用）は簡易化せず exhibit HTML をそのまま `figure_type: "html_file"` で使ってもよいが、その場合は事務所側でモノクロ変換が入ることを想定する。

**推奨：HTML経由の高品質ルート（v2）**

JSON仕様 → SVG埋込HTML → Puppeteerで PNG → PPTXに1スライド1図でフル埋込：

```bash
# Step 1: JSON → HTML（block_diagram は inch座標を自動スケール、flowchart は box幅・高さを動的調整）
python3 ${SKILL_DIR}/scripts/build_figure_html.py \
  --specs ~/patent/<案件名>/work/figure-specs/ \
  --out-dir ~/patent/<案件名>/work/figure-html/

# Step 2: HTML → PNG（Puppeteer）— for ループで全14図を一気にレンダ
for n in $(seq -w 1 14); do
  node ${SKILL_DIR}/render-tools/render_html.js \
    ~/patent/<案件名>/work/figure-html/figure-${n}.html \
    ~/patent/<案件名>/work/figures-rendered/figure-${n}.png
done

# Step 3: PPTX組立（フル画像埋込モード）
python3 ${SKILL_DIR}/scripts/build_figure_pptx.py \
  --specs ~/patent/<案件名>/work/figure-specs/ \
  --rendered-dir ~/patent/<案件名>/work/figures-rendered/ \
  --output ~/patent/<案件名>/output/図面.pptx
```

このルートの利点：
- 図番ヘッダ・キャプション・参照符号がCSS制御で揃う
- 表・フローチャート・ブロック図のレイアウト品質が大幅向上
- 各図のソース（HTML）は work/figure-html/ に残るので後から微調整可能

**従来：python-pptx ネイティブ描画ルート**

`--rendered-dir` を省略すると、build_figure_pptx.py が直接python-pptxで shapes を描画する従来モードになる。デザイン品質は低めだがpptxシェイプとして編集可能。

### 5. 図面ごとの説明文を書く

各図について `work/figure-descriptions.md` に **説明段落** を書く。`references/jpo-style.md` の文体に揃える。組織内サンプルがあれば `【発明を実施するための形態】` 配下の段落をリファレンスにする：

```markdown
## 図1の説明

【００１１】
図１に示すように、本実施形態に係る〇〇システムは、参加者端末１、〇〇サーバ１００、施設内DB２を備える。参加者端末１は、〇〇を入力するための端末である。〇〇サーバ１００は、〜
```

- 段落番号 `【００XX】` は通し番号（全体で連番）
- 参照符号は **本文中で全角数字** で振る（例：「サーバ１００」）。ファイル内では半角でもよいが、最終的に全角に変換する
- 1図につき1〜3段落が目安

### 6. 符号の説明セクション

`work/figure-descriptions.md` の末尾に `【符号の説明】` を作る：

```markdown
## 符号の説明

【００XX】
　１　参加者端末
　２　施設内DB
１００　〇〇サーバ
```

### 7. 技術説明書DOCX生成

```bash
python3 ${SKILL_DIR}/scripts/build_spec_docx.py \
  --idea ~/patent/<案件名>/work/idea-expanded.md \
  --claims ~/patent/<案件名>/output/請求項.txt \
  --figure-list ~/patent/<案件名>/work/figure-list.md \
  --figure-descriptions ~/patent/<案件名>/work/figure-descriptions.md \
  --output ~/patent/<案件名>/output/技術説明書.docx
```

このスクリプトは以下のセクションを順に組み立てる：

1. 【発明の名称】
2. 【技術分野】
3. 【背景技術】
4. 【発明が解決しようとする課題】
5. 【課題を解決するための手段】
6. 【発明の効果】
7. 【図面の簡単な説明】（figure-list から自動生成）
8. 【発明を実施するための形態】（figure-descriptions から）
9. 【符号の説明】
10. 【特許請求の範囲】（請求項.txt から流し込み）

### 8. 最終確認

ユーザーに以下を確認：
- 図面の番号と順序、参照符号の一貫性
- 説明文の用語が請求項と整合しているか
- 抜けセクションがないか

**.pptx と .docx は人間が PowerPoint / Word で最終調整する前提。** スクリプトはあくまで土台。

## 重要な実装ポイント

### フォント設定（latin / ea / cs を必ず全設定）

python-pptx / python-docx の `run.font.name = ...` は **latin typeface のみ** 設定する。
日本語（East Asian）文字はテーマ既定フォントへフォールバックするため、PowerPoint上で
「フォント名は Yu Gothic UI と表示されるが、実描画は別フォント」というズレが起きる。

- pptx: `scripts/pptx_helpers.py` の `set_run_font_full(run, font_name)` を使う
- docx: `scripts/build_spec_docx.py` 内の `set_run_font_full(run, font_name)` を使う

両者とも内部で `<w:rFonts ascii="..." eastAsia="..." hAnsi="..." cs="..."/>` または
`<a:latin>` `<a:ea>` `<a:cs>` 全てを設定する。

### 技術説明書のmarkdown処理

`build_spec_docx.py` v2 は `idea-expanded.md` を読む際に：
- `**bold**` `__bold__` → bold run
- `*italic*` → italic run（任意）
- `` `code` `` → 等幅 run
- `- xxx` `* xxx` → 行頭「・ 」付き段落
- `1. xxx` → 行頭「1. 」付き段落
- `## heading` → スキップ（章立ては明示的にコード側で生成）

これにより markdown 記法が docx に残らない。
