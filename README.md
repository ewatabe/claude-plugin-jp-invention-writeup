# jp-invention-writeup (Claude Code plugin)

日本特許出願の **発明者→特許事務所の引き渡し資料一式** を作成する Claude Code プラグイン。

発明アイデアを膨らませ、出願審議会・特許事務所打合せ用の **発明説明資料PPTX**、**請求項**、**図面PPTX**、**技術説明書DOCX** を JPO実務に沿った形式で揃える。

## インストール

### Claude Code の marketplace 経由（推奨）

このリポジトリは Claude Code のマーケットプレイス兼プラグインとして動く。Claude Code のプロンプトで:

```
/plugin marketplace add https://github.com/ewatabe/claude-plugin-jp-invention-writeup
/plugin install jp-invention-writeup@jp-invention-writeup
```

1行目でリポジトリをマーケットプレイス登録、2行目で `<plugin名>@<marketplace名>` 形式でインストール。

ローカルにクローン済みのものを使うなら:

```
/plugin marketplace add ~/claude-plugin-jp-invention-writeup
/plugin install jp-invention-writeup@jp-invention-writeup
```

### 手動 (clone + symlink)

```bash
git clone https://github.com/ewatabe/claude-plugin-jp-invention-writeup.git ~/claude-plugin-jp-invention-writeup
# Claude Code がプラグインディレクトリとして認識する場所へリンク
ln -s ~/claude-plugin-jp-invention-writeup ~/.claude/plugins/jp-invention-writeup
```

### 依存環境

プラグイン本体の install 後、Python と Node の依存を別途インストールする：

```bash
cd ~/.claude/plugins/jp-invention-writeup/skills/jp-invention-writeup
pip install -r requirements.txt
cd render-tools && npm install
```

#### 必要環境

- Python 3.10+
- Node.js 18+（Puppeteer 24 系の要件）
- 日本語フォント：
  - 推奨: `fonts-noto-cjk`（`sudo apt install fonts-noto-cjk`）
  - WSL 環境では `/mnt/c/Windows/Fonts/` 経由で Yu Gothic UI が使える
- （任意）`GEMINI_API_KEY` — banana 経由のオプション画像生成を使う場合のみ。https://aistudio.google.com/apikey で取得

## できること（4フェーズ）

| Phase | 内容 | 出力 |
|---|---|---|
| 1. アイデア膨らまし | 対話的に発明を深掘り、公知例の初期スクリーニング、構造化メモ化 | `work/idea-expanded.md` |
| 2. 発明説明資料PPTX | 5セクション構成。実施例UIモックは HTML/CSS + Puppeteer で高品質生成。詳細実施例は対話ヒアリング（Q-0〜Q-7）で構築 | `output/発明説明資料.pptx` |
| 3. 請求項作成 | 独立項1個＋従属項複数、サンプル準拠の (イ)(ロ)(ハ) ラベル構造 | `output/請求項.txt` |
| 4. 図面PPTX & 技術説明書DOCX | JSON仕様→HTML→PNG→pptx 埋込ルートで参照符号・キャプション整合を担保、markdown 除去・全 typeface 対応フォント統一 | `output/図面.pptx`, `output/技術説明書.docx` |

## 使い方

Claude Code でこのプラグインを認識させたあと、以下のいずれかを依頼するとスキルが起動する：

- 「特許のアイデアを膨らませたい」「発明のテクニカルライトを書きたい」
- 「出願審議会／特許事務所打合せ用の説明資料を作りたい」
- 「請求項を書きたい」「図面と技術説明書を作りたい」

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

詳細は `skills/jp-invention-writeup/SKILL.md` と `skills/jp-invention-writeup/phases/*.md` を参照。

## ライセンス

MIT License — 詳細は `LICENSE` 参照。

## 注意

- 本プラグインは **発明者向けの作業支援** であり、特許事務所による正式な公知例調査・明細書作成の代替ではない
- 生成された資料は必ず人間が PowerPoint / Word で最終調整してから事務所に渡すこと
- 公知例調査は Phase 1 で Web/論文検索による初期スクリーニングを行うが、最終判断は事務所に委ねる
