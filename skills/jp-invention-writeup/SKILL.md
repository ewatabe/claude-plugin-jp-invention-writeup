---
name: jp-invention-writeup
description: 日本の特許事務所に提出する技術説明書（テクニカルライト）と発明説明資料PPTXを作成する。発明アイデアを公知情報・参考資料を踏まえて膨らませ、請求項・図面PPTX・図面ごとの説明＋請求項を含むWordを生成する。社内発明者が、特許事務所に明細書ドラフトを依頼するための材料一式を仕上げる場面で使用。
type: workflow
---

# jp-invention-writeup

日本の特許出願に向けた **発明者→特許事務所の引き渡し資料一式** を作るスキル。
事務所が明細書をドラフトするための材料を、JPO実務に沿った形式で整える。

## いつ使うか

ユーザーが以下のいずれかを依頼してきたとき：
- 「特許のアイデアを膨らませたい」「発明のテクニカルライトを書きたい」
- 「発明説明資料の資料を作りたい」
- 「請求項を書きたい」「図面と明細書のもとを作りたい」
- 上記の追記・修正（既存案件のフェーズ続き）

## 成果物（最終的に揃えるもの）

| 成果物 | ファイル名 | 役割 |
|---|---|---|
| アイデア構造化メモ | `work/idea-expanded.md` | フェーズ間の共通入力。直接の納品物ではない |
| 発明説明資料PPTX | `output/発明説明資料.pptx` | 社内出願審議会・特許事務所打合せなどで発明を説明する資料 |
| 請求項 | `output/請求項.txt` | 独立項＋従属項。(イ)(ロ)(ハ)構成 |
| 図面PPTX | `output/図面.pptx` | 図１〜図N。参照符号付与済み |
| 技術説明書 | `output/技術説明書.docx` | 図ごとの詳細説明＋請求項を含むWord。事務所提出メイン資料 |

## パス規約（重要）

このスキル内のドキュメント・コード例では、スキル本体の配置先を **`${SKILL_DIR}`** と表記する。
Claude は実行時にこれを実際のパスに解決する。典型的には以下のいずれか:

- 単体スキルとして配置: `${SKILL_DIR}` = `~/.claude/skills/jp-invention-writeup`
- プラグイン経由: `${SKILL_DIR}` = `~/.claude/plugins/<plugin-name>/skills/jp-invention-writeup`

Claude が bash コマンドを生成する際は、`${SKILL_DIR}` を上記の実体パスに展開して実行する。シェル側で `SKILL_DIR=$(dirname <SKILL.mdのフルパス>)` のように設定して使うか、Claude が直接フルパスを埋め込む。

ユーザの案件ディレクトリ（`~/patent/<案件名>/`）は別概念で、こちらはそのまま記述する。

## 案件ディレクトリの規約

新規案件は `~/patent/<案件名>/` 配下に以下の構造を作る：

```
~/patent/<案件名>/
├── inputs/
│   ├── idea.md            # 発明者のラフなアイデア（必須）
│   ├── brainstorming.md   # Claude等との壁打ち履歴（任意）
│   ├── claims-draft.txt   # 既に書きかけの請求項（任意）
│   ├── invention-explainer-wip.pptx # 作りかけの発明説明資料（任意・pptx or md）
│   ├── template.pptx      # 組織の発明説明資料テンプレート（任意。配色・ロゴ・フォントの参考に）
│   ├── prior-art.txt      # 特許事務所の公知例調査結果（任意・テキスト）
│   └── references/        # その他参考資料（論文・社内資料など）
├── work/
│   └── idea-expanded.md   # Phase 1で生成
└── output/
    ├── 発明説明資料.pptx
    ├── 請求項.txt
    ├── 図面.pptx
    └── 技術説明書.docx
```

案件名が未指定ならユーザーに確認する。既存の `~/patent/<案件名>/` があれば再開とみなす。

## 既存成果物がある場合の再開ルート

ユーザーが既に部分的に作業している場合、対応するフェーズは **ゼロから作らず差分作業モード** に切り替える。
各フェーズ冒頭で `inputs/` と `work/` を必ずスキャンし、以下のファイルがあれば該当処理を行う：

| 既存ファイル | 検出フェーズ | モード切替後の挙動 |
|---|---|---|
| `inputs/brainstorming.md` | Phase 1 | 壁打ち履歴を一次情報として読み、`idea-expanded.md` のドラフトを先に提示してから不足のみヒアリング。十分充実していれば深掘り対話をスキップ |
| `inputs/claims-draft.txt` | Phase 3 | ゼロから書かず、既存ドラフトを読み込んだ上で公知例差別化チェック→改訂提案を生成 |
| `inputs/invention-explainer-wip.pptx` | Phase 2 | `pptx-task-ops` スキルで内容抽出 → 既存スライドを保持しつつ未着手セクションのみ補完案を出す |
| `inputs/template.pptx` | Phase 2 | `pptx-task-ops` で表紙・章扉等を画像化 → カラー・ロゴ・フォントを抽出して `work/html-slides/common.css` に反映。表紙等はテンプレを流用する案も提示（詳細：`references/rich-slide-design.md` §組織テンプレートとの統合） |
| `work/invention-explainer-draft.md` | Phase 2 | mdベースの作りかけがあれば、それをそのまま編集対象として続行 |
| `work/idea-expanded.md` | Phase 1 | 既にPhase 1が完了済みとみなす。ユーザーに「内容更新が必要か」だけ確認 |
| `output/*` | 各 | 既に納品物がある場合は、上書き前に必ずユーザーに確認 |

差分作業モードでは **既存内容の流用を最優先**。改訂は最小限にとどめ、変更点は要約してユーザーに提示してからファイルを書き換える。

## ワークフロー（4フェーズ）

このスキルは段階的に進める。各フェーズの詳細手順は `phases/` 配下を参照する。

### Phase 1: アイデア膨らまし
- 詳細: `phases/1-expand.md`
- 入力: `inputs/idea.md`（必須）、`inputs/brainstorming.md`（任意：壁打ち履歴）、`inputs/prior-art.txt`（任意）、`inputs/references/`（任意）
- 出力: `work/brainstorming.md`（深掘り議論記録）、`work/idea-expanded.md`（構造化メモ）、`work/prior-art-web.txt`（任意：Web検索による公知例候補）
- やること:
  1. 初期ヒアリング（11項目）でアイデア素案を作る
  2. **仮独立項を起こしてユーザーと弱点を議論**
  3. **Web/論文検索で公知例の当たりをつける**（事務所調査前の初期スクリーニング）
  4. **公知例との重なり分析→差別化戦略を3層構造で構築**
  5. **採用技術要素・実施形態バリエーション・残課題を深掘り**
  6. brainstorming.md（生の議論記録）と idea-expanded.md（構造化メモ）を生成

### Phase 2: 発明説明資料PPTX
- 詳細: `phases/2-invention-explainer-pptx.md`
- 入力: `work/idea-expanded.md`
- 出力: `output/発明説明資料.pptx`
- やること: 5セクション構成（背景／目的／概要・ポイント／実施例／クレーム＆公知例）でアイデア説明スライドを作る

### Phase 3: 請求項作成
- 詳細: `phases/3-claims.md`
- 入力: `work/idea-expanded.md`、`inputs/prior-art.txt`（あれば）
- 出力: `output/請求項.txt`
- やること: 独立項1つ＋従属項複数を、サンプル準拠の (イ)(ロ)(ハ) 構成で書く

### Phase 4: 図面PPTXと技術説明書DOCX
- 詳細: `phases/4-figures-and-spec.md`
- 入力: `work/idea-expanded.md`、`output/請求項.txt`
- 出力: `output/図面.pptx`、`output/技術説明書.docx`
- やること: 図面リストを設計→各図のJSON仕様を作成→`scripts/build_figure_pptx.py` でpptx化→ `scripts/build_spec_docx.py` で技術説明書を組み立てる

## 参照すべきルール

書式や用語法に迷ったら `references/` を読む：
- `references/jpo-style.md` — 明細書の章立てと文体（サンプル準拠）
- `references/claim-rules.md` — 請求項の書き方（独立項・従属項・(イ)(ロ)構成）
- `references/figure-conventions.md` — 図番号・参照符号・キャプションのルール
- `references/ui-mockup-html.md` — 実装画面UIモックのHTML/CSS記法（実施例スライド用）
- `references/detailed-exhibit-design.md` — 詳細実施例スライドを高品質に作るための **対話的ヒアリング Q-0〜Q-7** とデザインシステム・反復ループ・品質チェックリスト
- `references/rich-slide-design.md` — **役員説明レベルのリッチ発明説明資料**の作り方（HTML+CSS→Chromeヘッドレス→1920x1080 PNG→PPTXフルブリード方式）
- `references/figure-from-papers.md` — 公知例論文の図をスライドに **引用** する標準パイプライン（pdftoppm + PIL 切り抜き、ライセンス注記、社内資料限定の指針）
- `references/banana-image-gen.md` — **(オプション)** banana 経由の概念図生成：二段階方式・JSON仕様・トラブルシューティング

## ツールスタック

スキル本体に同梱する補助ツール：
- `scripts/build_figure_pptx.py` — JSON仕様から特許図面PPTX（block / flowchart / table / image モード、`--rendered-dir` でHTMLレンダPNGを1スライド1図のフル画像埋込モードに切替可能）
- `scripts/build_figure_html.py` — JSON仕様 → 高品質HTML（SVG+CSS）→ Puppeteerで PNG レンダ用。Yu Gothic UI を全 typeface に適用
- `scripts/build_rich_pptx.py` — **Phase 2 既定** の発明説明資料 PPTX 組立て。1920x1080 PNG を 1 スライド 1 画像でフルブリード配置
- `scripts/render_all_slides.sh` — `work/html-slides/*.html` を Chrome ヘッドレスで 1920x1080 PNG に並列レンダ（4 並列）
- `scripts/build_explainer_pptx.py` — **(フォールバック)** markdown → 簡素 PPTX。ユーザーが明示的に「クイックモード」指定したときのみ使う
- `scripts/build_spec_docx.py` — 各種素材 → 技術説明書DOCX。**markdown記法を除去**して整形、Yu Gothic UI を全 typeface に適用
- `scripts/pptx_helpers.py` — python-pptx共通ヘルパー（噴き出し・引出線・テキスト置換・フォント統一・並べ替え・ページ番号補正）
  - 重要: `set_run_font_full(run, font_name)` を使うと latin/ea/cs typeface 全てを設定。日本語が別フォントで描画される問題を回避
  - 共通定数:
    - `DEFAULT_BUBBLE_TEXT = (0, 0, 0)` — 噴き出し・テキストボックスの本文は **黒** が既定
    - `SAMPLE_USER_NAME = "山田 花子"`／`SAMPLE_USER_NAME_KANJI = "山田花子"` — 架空のサンプル患者・ユーザー名が必要なときに使う中立の既定値
  - `add_speech_bubble(slide, x, y, w, h, text, anchor=(tx, ty))` は **ROUNDED_RECTANGULAR_CALLOUT**（角丸＋しっぽ付き吹き出し）を生成し、しっぽが anchor を指すよう adj を自動調整する。anchor=None なら ROUNDED_RECTANGLE（しっぽなし）にフォールバック
- `scripts/build_banana_image.py` — **(オプション)** Gemini Nano Banana 経由でテキストなしのブランクレイアウトPNGを生成。Phase 2 の発明説明資料ヒーロー画像／概念図でのみ使用
- `scripts/compose_jp_labels.py` — **(オプション)** ブランクPNGの暗いティール枠を自動検出し、PIL + Yu Gothic/Noto Sans JP で日本語ラベルを上から合成。Geminiの日本語フォント崩れを完全に回避する
- `render-tools/render_html.js` — Puppeteer で HTML → PNG レンダ（実施例UIモック用）
- `templates/ui-mockup.template.html` — 実施例UIモックの出発点HTML
- `templates/rich-slide.common.css` — リッチスライド方式の共通スタイル（デザインシステム、CSS変数、コンポーネント）
- `templates/rich-slide.template.html` — リッチスライド方式の通常スライド出発点HTML（ヘッダ/タイトル/メイン/フッタの4領域構造）
- `templates/rich-slide.cover.html` — リッチスライド方式の表紙スライド出発点HTML（グラデーション背景・ロゴ・メタ情報）
- `templates/banana-spec.example.json` — banana 画像生成＋ラベル合成の仕様サンプル
- `templates/brainstorming.template.md` — Phase 1 深掘りの記録テンプレ（germline案件を範に章立て）

外部依存（既存）:
- `python-pptx`, `python-docx` (pip)
- Node.js + `puppeteer`（`render-tools/` 配下に local install 済み）
- 公式 `pptx` Skill（`~/.claude/skills/pptx/`）を参照資産として保持

外部依存（リッチスライド方式 — モード B 利用時のみ）:
- `google-chrome` または `google-chrome-stable`（ヘッドレスで 1920x1080 PNG レンダリング）
- 日本語フォント（Noto Sans CJK JP 推奨。Linux なら `fonts-noto-cjk`）
- `Pillow`（pip） — 論文図引用時の切り抜きで使用
- `poppler-utils`（`pdftoppm` / `pdfimages`） — 論文 PDF からのページ画像化

外部依存（オプション — `--use-banana` を有効にした場合のみ）:
- `Pillow` (pip) — 日本語ラベル合成
- 環境変数 `GEMINI_API_KEY` または `GOOGLE_AI_API_KEY` — Gemini Nano Banana 呼び出し
- 日本語フォント — Noto Sans CJK（Linuxなら `fonts-noto-cjk`）または WSL 経由の Windows フォント（Yu Gothic / Meiryo）

## オプション機能：banana（画像生成）の使用可否

**デフォルトは banana 不使用。** ユーザーが明示的に「banana で表紙画像を作って」「概念図を AI で生成して」のように依頼した場合のみオプトイン。

| 用途 | banana 利用 | 理由 |
|---|---|---|
| **Phase 2 — 発明説明資料の表紙／概念図／ワークフロー絵** | ✅ 可（オプトイン） | 社内資料で絵的な訴求力が役立つ |
| **Phase 2 — 実施例のUIモック** | ❌ 使わない | HTML+CSS 方式を維持（再現性・編集性・証拠性） |
| **Phase 4 — 図面.pptx** | ❌ 使わない | 参照符号・編集可能性・線画性が必須 |
| **Phase 4 — 技術説明書.docx** | ❌ 使わない | テキスト中心、画像は figure-html 経由 |

**必ず二段階方式で生成する：**
1. `build_banana_image.py` で **テキストなしのブランクレイアウト** を Gemini に生成させる
2. `compose_jp_labels.py` で PIL + 日本語フォント により ラベル・タイトル・説明文を合成する

Gemini はマルチバイトCJKのレンダリングが不安定（文字化け頻発）なため、画像内に日本語を直接描画させてはならない。**この方式はテンプレ化されており、`templates/banana-spec.example.json` を出発点に JSON 1個で完結する。** 詳細は `references/banana-image-gen.md` を参照。

## 過去サンプルの扱い（任意）

ユーザーが自分の組織で過去に書いた優良サンプル（明細書.docx、図面.pptx、発明説明資料.pptx、請求項.txt）を `~/patent/sample/` 配下に配置していれば、**文体・粒度・図の作り方の見本として常に参照する**。案件固有の内容を流用してはならず、あくまでスタイル参考に留める。

サンプルが配置されていなくてもこのスキルは動作する。その場合は `references/jpo-style.md` `references/claim-rules.md` `references/figure-conventions.md` に書かれた一般ルールのみに従う。

## 重要な原則

1. **対話的に進める。** Phase 1で発明者からヒアリングする項目は決まっている（`phases/1-expand.md`参照）。勝手に埋めず、不足は必ず聞く。
2. **公知例調査は二段構え。** 事務所提供の `inputs/prior-art.txt` が **正式調査** 。Phase 1 で行う Web/論文検索は **発明者の初期スクリーニング** であり、最終判断は事務所に委ねる。両者を混同しない。
3. **JPO実務の文体に寄せる。** 「〜である」「〜を備える」などの語尾・章立てに合わせる（`references/jpo-style.md` 参照）。組織内の過去サンプルがあれば優先的にそれに寄せる。
4. **参照符号は二桁刻みの慣例。** 主要構成要素を10, 20, 30…で振り、その下位部品を11, 12, 21, 22…で振る（`references/figure-conventions.md`参照）。
5. **フェーズはスキップ可能。** ユーザーが「Phase 3だけ」と言えばそこから始めてよい。ただし前段の成果物が無ければ簡略版を口頭で確認してから進める。

## 開始時のチェックリスト

ユーザーがスキルを呼んだら、以下を確認してから着手する：

1. 案件名は？（`~/patent/<案件名>/` を確定）
2. 既存案件の続き？新規？
3. どのフェーズから？（全フェーズ／Phase X から）
4. `inputs/idea.md` はあるか？無ければまずそれを作る支援から
5. **組織の発明説明資料 PPTX テンプレートはあるか？**
   - `~/patent/<案件名>/inputs/template.pptx` または `~/patent/sample/template.pptx` を確認
   - あれば、`references/rich-slide-design.md` の「組織テンプレートとの統合」節に従い、
     テンプレからカラー・ロゴ・フォント・表紙レイアウトを抽出して反映する
   - 抽出方法は `pptx-task-ops` スキルでスライド画像化 → Claude が目視確認 → `common.css`
     の CSS 変数を書き換え、ロゴ画像を `work/html-slides/` に配置
6. **公知例論文の図を引用したいか？**
   - 業界状況・課題セクションに論文の概念図を埋めると説得力が増す
   - 既定は不使用。利用時は `references/figure-from-papers.md` の引用ライセンス指針に従う
7. **オプション:** 発明説明資料PPTXの表紙／概念図を画像生成（banana）で作りたいか？
   - 既定は不使用。明示の依頼があれば Phase 2 の所定手順で利用する

注：Phase 2 の発明説明資料 PPTX は **既定でリッチスライド方式**（HTML+CSS → Chrome
ヘッドレス 1920x1080 PNG → PPTX フルブリード）で作る。ユーザーから明示的に「クイック
モード」「簡素でよい」と指定された場合のみ、markdown ベース（`build_explainer_pptx.py`）に
切り替える。
