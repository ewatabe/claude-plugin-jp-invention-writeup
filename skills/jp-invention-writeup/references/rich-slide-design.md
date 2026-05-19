# リッチスライドデザイン — 発明説明資料の既定方式

Phase 2 の発明説明資料 PPTX は **常にこの方式で作る**。`HTML+CSS で個別スライドを記述 → Chrome ヘッドレスで 1920x1080 PNG レンダ → PPTX に 1 スライド 1 画像でフルブリード配置` という流れで、社内発明審議会・経営陣説明・特許事務所打合せのいずれにも耐えるビジュアル品質を最初から確保する。

テキスト修正は HTML を直接編集して該当スライドだけ再レンダする運用（最終節「スライド差し替えだけしたい」参照）。

## 例外：簡素モードへのフォールバック

ユーザーが明示的に「クイックモード」「簡素な markdown でよい」と指定した場合のみ、`scripts/build_explainer_pptx.py`（markdown ベース）を使うフォールバックを許容する。それ以外は本書のリッチスライド方式が既定。

出願書類の図面（参照符号付き、モノクロ）は Phase 4 の `build_figure_pptx.py` で別途作成する。本書のリッチスライド方式は **発明説明資料（社内・事務所打合せ用）のみ** に使う。

## 採用する技術スタック

| 工程 | ツール | 出力 |
|---|---|---|
| ① 個別スライド記述 | HTML + CSS（`templates/rich-slide.common.css` を継承） | `work/html-slides/NN-name.html` |
| ② 画像レンダ | Chrome ヘッドレス `--screenshot` 1920x1080 | `work/figures-rendered/NN-name.png` |
| ③ PPTX 組立 | `scripts/build_rich_pptx.py`（python-pptx） | `output/発明説明資料.pptx` |

依存:
- `google-chrome`（または `google-chrome-stable`）コマンド
- `python-pptx`（pip）
- 必要に応じて `Pillow` / `poppler-utils`（論文図切り抜きに使う場合）

## 基本構造（共通レイアウト）

各スライドは `1920x1080 px` で、以下の 4 領域に分かれる:

```
┌────────────────────────────────────────────┐
│ slide-header  ── 案件名 / セクション名      │ ヘッダ：上 24-48px
├────────────────────────────────────────────┤
│ slide-title    ── 44px 大タイトル           │
│ slide-subtitle ── 20px サブ                  │
├────────────────────────────────────────────┤
│ slide-main     ── メイン（自由レイアウト）   │ flex で残り全部
│                                              │
└────────────────────────────────────────────┤
│ slide-footer   ── 出典／注記 / ページ番号    │ フッタ：下 24-48px
└────────────────────────────────────────────┘
```

HTML の最低限の骨格は `templates/rich-slide.template.html`、表紙用は `templates/rich-slide.cover.html` を参照。

## デザインシステム（CSS 変数）

`templates/rich-slide.common.css` の `:root` に色・余白・タイポを集約。

| 用途 | 変数 | デフォルト |
|---|---|---|
| 主色（医療・信頼） | `--primary` | `#1E40AF` |
| 強調（成長・進化） | `--accent` | `#10B981` |
| 警告（課題・リスク） | `--warn` | `#EF4444` |
| 注意（保留・補足） | `--info` | `#F59E0B` |
| 背景 | `--bg` | `#F8FAFC` |
| 本文色 | `--text` | `#1E293B` |
| 余白色 | `--text-muted` | `#64748B` |

案件に応じて :root を差し替えると、案件カラーへ一括変更できる。

## 既製コンポーネント

`common.css` には以下のコンポーネントが用意されている:

- `.card` / `.card-title` / `.card-icon` — 標準カード
- `.badge-primary / -accent / -warn / -info / -gray` — ピル状バッジ
- `.stat .num` / `.stat .label` — KPI 風数値表示
- `.grid-2 / .grid-3 / .grid-4` — グリッドレイアウト
- `.flow / .flow-box / .flow-arrow` — フローチャート横並び
- `table.compare` — 比較テーブル（公知例差別化表）
- `.cover-slide` — 表紙用グラデーション背景
- `.paper-figframe / .paper-src` — 引用論文図のフレーム & 出典枠

スライド固有スタイルは HTML の `<style>` 内に書いて構わない（共通でないものまで CSS に入れると肥大化する）。

## 推奨スライド構成（中規模発明 18 枚案）

| # | テンプレ | 目的 |
|---|---|---|
| 01 | cover | 表紙：プロジェクト名・タイトル・サブ・メタ |
| 02 | agenda | アジェンダ 5 項目を視覚カードで |
| 03 | background | 業界状況：数値ファクト＋構造図 |
| 04 | problems | 現状の課題 6 件をカード化 |
| 04b | prior-art-figures | 公知例の論文図を引用（社内資料限定） |
| 05 | purpose | 本発明の目的（ヒーロー + 4 目的カード） |
| 06 | overview | 発明全体のアーキテクチャ図 |
| 07 | points-1 | 独立項 1 のポイント |
| 08 | points-2 | 独立項 2 のポイント（戦略学習等） |
| 09 | points-3 | 重要従属項のポイント |
| 10-14 | examples | 実施例 5 件（アプリ画面モック・転移概念図・合意判定・獲得サイクル・SV） |
| 15 | claims-summary | 独立請求項の階層図 |
| 16 | prior-art-table | 公知例差別化表（●◐×?） |
| 17 | benchmark | 実測ベンチマーク・コスト比較 |
| 18 | closing | 結論 + ネクストステップ |

## ワークフロー

```bash
# 1. 案件ディレクトリにスライド用ワーク領域を作る
WORK=~/patent/<案件名>/work
mkdir -p $WORK/html-slides $WORK/figures-rendered

# 2. 共通 CSS をコピー（テンプレを継承）
cp ${SKILL_DIR}/templates/rich-slide.common.css $WORK/html-slides/common.css

# 3. 各スライド HTML を作成
#    - 01-cover.html, 02-agenda.html, ..., 18-closing.html
#    - templates/rich-slide.template.html を起点に編集
#    - 表紙だけは templates/rich-slide.cover.html を使う

# 4. すべてのスライドを並列レンダ
bash ${SKILL_DIR}/scripts/render_all_slides.sh \
    $WORK/html-slides/ \
    $WORK/figures-rendered/

# 5. PPTX 組立
python3 ${SKILL_DIR}/scripts/build_rich_pptx.py \
    --rendered-dir $WORK/figures-rendered/ \
    --output ~/patent/<案件名>/output/発明説明資料.pptx
```

## 文字数・配置のチェックリスト

| 要素 | 上限の目安 |
|---|---|
| `slide-title` | 30 文字（折り返しなしで 1 行）／40 文字で 1 改行可 |
| `slide-subtitle` | 60 文字／1 行 |
| カード本文（`.card .desc`） | 80 文字／3 行以内 |
| バッジ | 12 文字以内 |
| 比較テーブル 1 セル | 30 文字以内 |
| フローチャート box | 16 文字以内 |

文字数を超えると 1920x1080 内に収まらず、PPTX 化後の見た目が乱れる。HTML レンダ後に PNG を目視確認すること（`Read` で開くか PowerPoint で開く）。

## アプリ画面モックの作り方

実施例で「ダッシュボード画面」「解析結果画面」等の UI モックを入れる場合、HTML+CSS で **タイトルバー → メニュータブ → サイドバー → メインパネル → フッタ** の Web アプリ構造を模写する。

参考例（`work/html-slides/10-example-braf.html` などで使ったパターン）:

```html
<div class="ex-app">
  <div class="ex-titlebar">
    <div class="dots"><div class="dot r"></div><div class="dot y"></div><div class="dot g"></div></div>
    <div class="url">https://shinka.local/runs/4128</div>
  </div>
  <div class="ex-header">…プロジェクトロゴ + 画面タイトル…</div>
  <div class="ex-tabs">…タブ…</div>
  <div class="ex-body">
    <div class="ex-side">…サイドバー…</div>
    <div class="ex-main">…メインパネル…</div>
    <div class="ex-right">…右ペイン…</div>
  </div>
  <div class="ex-foot">…フッタ…</div>
</div>
```

吹き出し（callout）で「請求項 N 対応」を明示すると、進歩性主張の根拠説明に直結する。

## トラブルシューティング

### 日本語が豆腐になる

Linux に Noto Sans CJK JP が入っているか確認:

```bash
fc-list :lang=ja | grep -iE "noto|yu" | head
```

未インストールなら:

```bash
sudo apt install fonts-noto-cjk fonts-noto-cjk-extra
```

CSS では Google Fonts CDN 経由で `Noto Sans JP` を読み込んでいるため、ネット接続があればフォールバック可能。

### Chrome レンダで画像が出ない

- `--virtual-time-budget=8000` を長めに（重い CSS の場合）
- `<img>` のパスは **HTML と同じディレクトリ** に置く（`file://` から相対パス）
- フォント CDN を読み込む間に時間がかかる場合がある

### PPTX のファイルサイズが大きい

- PNG 1 枚 ≒ 200-800 KB、18 枚で約 5-15 MB が目安
- 役員説明には許容範囲だが、メール添付では `pdftoppm` で JPG 化して圧縮するオプションもある

### スライド差し替えだけしたい

1 枚だけ修正した場合:

```bash
# 1. 該当 HTML を編集
vi $WORK/html-slides/04b-prior-art-figures.html

# 2. 1 枚だけレンダ
google-chrome --headless --no-sandbox --hide-scrollbars \
  --window-size=1920,1080 --disable-gpu --virtual-time-budget=8000 \
  --screenshot=$WORK/figures-rendered/04b-prior-art-figures.png \
  "file://$WORK/html-slides/04b-prior-art-figures.html"

# 3. PPTX 再生成
python3 ${SKILL_DIR}/scripts/build_rich_pptx.py \
    --rendered-dir $WORK/figures-rendered/ \
    --output ~/patent/<案件名>/output/発明説明資料.pptx
```

## 補助：markdown でドラフトを練る場合

リッチスライド方式が既定だが、本文の言い回しだけ先に発明者と詰めたい場合に限り、
`work/invention-explainer-draft.md`（markdown）に下書きを残してからリッチ化に進む運用も可能。
ただし最終出力は **常にリッチスライド方式** にする。
