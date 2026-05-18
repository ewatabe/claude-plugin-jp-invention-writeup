# jp-invention-writeup

日本特許の出願準備（発明者→特許事務所の引き渡し資料一式）を作成する Claude Code 用スキル。

発明者がアイデアを膨らませ、発明説明資料PPTX・請求項・図面PPTX・技術説明書DOCX を JPO 実務に沿った形式で揃えるところまでを4フェーズで支援する。

## できること

- **Phase 1**: ラフなアイデアを対話的に深掘り、公知例の初期スクリーニング、構造化メモ化
- **Phase 2**: 発明説明資料PPTX（5セクション構成）。実施例UIモックは HTML/CSS + Puppeteer で生成し、本物の画面に近い品質で証拠性・編集性を担保
- **Phase 3**: 独立項1個＋従属項複数を、サンプル準拠の (イ)(ロ)(ハ) ラベル構造で生成
- **Phase 4**: 図面PPTX（JSON仕様→HTML→PNG→pptx 埋込）と技術説明書DOCX（マークダウン除去・全 typeface 対応フォント統一済み）

## インストール

このスキルは Claude Code のスキルディレクトリに置く想定で設計されている。

```bash
# 1. スキルをクローン
git clone <REPO_URL> ${SKILL_DIR}

# 2. Python 依存
pip install -r ${SKILL_DIR}/requirements.txt

# 3. Node.js 依存（HTMLレンダ用 Puppeteer）
cd ${SKILL_DIR}/render-tools
npm install
```

### 必要環境

- Python 3.10+
- Node.js 18+（Puppeteer 24 系の要件）
- 日本語フォント:
  - **推奨**: `fonts-noto-cjk`（`sudo apt install fonts-noto-cjk`）
  - **WSL** なら `/mnt/c/Windows/Fonts/` 経由で Yu Gothic UI が使える
- （任意）`GEMINI_API_KEY` — banana 経由のオプション画像生成を使う場合のみ。https://aistudio.google.com/apikey で取得

## 使い方

Claude Code でこのスキルが認識されていれば、ユーザーが「特許のアイデアを膨らませたい」「発明説明資料の資料を作りたい」「請求項を書きたい」「図面と技術説明書を作りたい」のいずれかを依頼するとスキルが起動する。

案件ディレクトリは `~/patent/<案件名>/` に作る:

```
~/patent/<案件名>/
├── inputs/
│   ├── idea.md            # 発明者のラフなアイデア（必須）
│   ├── brainstorming.md   # 過去の壁打ち履歴（任意）
│   ├── prior-art.txt      # 特許事務所の公知例調査結果（任意）
│   └── references/        # その他参考資料
├── work/                  # フェーズ間の中間生成物
└── output/
    ├── 発明説明資料.pptx
    ├── 請求項.txt
    ├── 図面.pptx
    └── 技術説明書.docx
```

詳細なフェーズ別手順は `SKILL.md` と `phases/*.md` を参照。

## 過去サンプルの扱い（任意）

`~/patent/sample/` 配下に組織内の過去出願サンプル（明細書.docx・図面.pptx・請求項.txt・発明説明資料.pptx）を置いておくと、文体・粒度の見本として参照される。配置されていなくてもスキル本体は動作するが、組織固有のスタイル（言い回し・章順）に寄せたい場合は配置を推奨。

## オプション: banana 画像生成

Phase 2 の表紙ヒーロー画像／概念図を Gemini Nano Banana で生成するオプション。詳細は `references/banana-image-gen.md` 参照。

- 既定では使わない（ユーザーが明示的に依頼した場合のみ起動）
- Phase 4 の図面・技術説明書には使わない
- 必ず二段階方式：ブランクレイアウト生成 → PIL で日本語ラベル合成（Geminiの日本語描画崩れ回避）

## ライセンス

MIT License — 詳細は `LICENSE` 参照。

## 注意

- 本スキルは発明者向けの作業支援であり、**特許事務所による正式な公知例調査・明細書作成の代替ではない**。
- 生成された資料は必ず人間が PowerPoint / Word で最終調整してから事務所に渡すこと。
- 公知例調査は Phase 1 で Web/論文検索による初期スクリーニングを行うが、最終判断は事務所に委ねる。
