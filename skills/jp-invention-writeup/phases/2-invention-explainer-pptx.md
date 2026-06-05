# Phase 2: 発明説明資料PPTX

社内の発明説明資料でアイデアを説明する初期スライドを作る。
`~/patent/sample/発明説明資料.pptx` が配置されていればそれを見本とする。未配置でも以下の構成案で生成できる。

## 入力
- `~/patent/<案件名>/work/idea-expanded.md`

## 出力
- `~/patent/<案件名>/output/発明説明資料.pptx`

## ★ 既定方式：リッチスライド ★

Phase 2 の発明説明資料は **常にリッチスライド方式で作る**。社内発明審議会・経営陣説明・特許事務所打合せのいずれにも耐えるビジュアル品質を最初から確保する。

- 作り方の詳細：`references/rich-slide-design.md`（必ず開く）
- デザインシステム：`templates/rich-slide.common.css`
- 通常スライド骨格：`templates/rich-slide.template.html`
- 表紙スライド骨格：`templates/rich-slide.cover.html`
- 並列レンダ：`scripts/render_all_slides.sh`
- PPTX 組立：`scripts/build_rich_pptx.py`

### 組織テンプレートが配置されている場合

`inputs/template.pptx`（または `~/patent/sample/template.pptx`）が見つかった場合は、
**着手前に必ず以下を実行** してビジュアルを組織の標準に合わせる:

1. `pptx-task-ops` スキルでテンプレ全スライドを PNG 画像化
2. Claude が画像を `Read` して **配色・ロゴ・フォント・章扉デザイン** を目視抽出
3. `work/html-slides/common.css` の CSS 変数（`--primary` / `--accent` / `--text` 等）を
   テンプレの配色に書き換える
4. テンプレからロゴ画像を抽出して `work/html-slides/logo.png` に配置、各 HTML の
   `slide-header` または `cover-slide` で読み込む
5. 表紙・章扉は **テンプレの該当スライドをそのまま流用** するか、本スキルの
   `templates/rich-slide.cover.html` を組織デザインに合わせて改変するかを
   `AskUserQuestion` で選ばせる（2択。それぞれの長所を説明に書く）

詳細手順は `references/rich-slide-design.md` の「組織テンプレートとの統合」節を参照。

公知例論文の図を背景セクション等で引用したい場合は `references/figure-from-papers.md` を参照。
**社内資料限定の引用利用**で、特許明細書・図面 PPTX への転載は厳禁。

### 簡素 markdown モード（フォールバック）

ユーザーが「クイックに文言だけ確認したい」「リッチ化は不要」と明示した場合のみ、
`scripts/build_explainer_pptx.py`（markdown → 簡素 PPTX）を使うフォールバックを許容する。
既定では使わない。

## スライド構成（サンプル準拠の5セクション）

過去発明説明資料PPTXのサンプルが `~/patent/sample/` にあればその章立てを踏襲。なくても以下の構成で構わない：

| # | セクション | 内容 |
|---|---|---|
| 1 | 表紙 | 日付、所属、案件名（仮） |
| 2 | アジェンダ | 1.背景と課題 2.目的 3.発明概要とポイント 4.実施例 5.クレーム＆公知例 |
| 3-N | 1. 背景と発明で解決したい問題と課題 | 業界状況・現状の課題（1〜3枚） |
| N+1 | 2. 本発明の目的 | 課題を踏まえた目的を1枚で |
| N+2〜 | 3. 発明概要と発明のポイント | システム概要図＋ポイント箇条書き（2〜3枚） |
| 〜 | 4. 発明の実施例 | 主要な実施形態を図解（2〜4枚） |
| 〜 | 5. クレームおよび公知例調査結果 | 独立項のサマリ、公知例との差別化表（2枚） |

## 手順

### 0. 既存成果物の検出（差分作業モード判定）

着手前に以下を確認：
- `work/invention-explainer-draft.md` が既にあれば、それを **編集対象** として続行（再生成しない）
- `inputs/invention-explainer-wip.pptx` があれば、`pptx-task-ops` スキルで内容を抽出してから手順を進める：
  1. `pptx-task-ops` でスライド構成（タイトル・本文・図のインデックス）を抽出
  2. 抽出結果を `work/invention-explainer-draft.md` に変換（既存スライドを保持）
  3. 不足セクション（5構成のうち未着手のもの）だけを補完案として提示
- `output/発明説明資料.pptx` が既にあれば、上書き前にユーザーに確認

### 1. スライド構成案を作る（または既存案を編集する）

新規の場合：`work/idea-expanded.md` を元に上記5セクションを markdown で草案化し、`templates/invention-explainer.template.md` を `work/invention-explainer-draft.md` にコピーして埋める。

差分作業モードの場合：手順0で作成・抽出した `work/invention-explainer-draft.md` を出発点に、不足セクションのみ追記する。**既存スライドの内容や順序は勝手に変えない。**

### 2. ユーザー確認

`work/invention-explainer-draft.md` をユーザーに見せて、構成・順序・内容にOKをもらう。
**この段階で骨子を確定させる。** pptx化後の修正は手間がかかる。
確認は `AskUserQuestion` で「この構成でPPTX化に進む／修正する（自由入力）」を明示的に選ばせ、平文で同意を待たない。

### 3. PPTX生成（既定：リッチスライド方式）

**詳細は `references/rich-slide-design.md` を必ず読んで進める。** 概略は以下のとおり：

```bash
WORK=~/patent/<案件名>/work
mkdir -p $WORK/html-slides $WORK/figures-rendered

# Step A. 共通 CSS をコピー
cp ${SKILL_DIR}/templates/rich-slide.common.css $WORK/html-slides/common.css

# Step B. 個別スライドを HTML で記述
#   ・templates/rich-slide.template.html を起点に編集
#   ・表紙だけは templates/rich-slide.cover.html を起点
#   ・命名規約: NN-name.html （01-cover, 02-agenda, ... 18-closing）
#   ・スライド間に追加挿入したい場合は 04b-extra.html のように "b/c" で命名

# Step C. 全 HTML を 1920x1080 PNG に並列レンダ
bash ${SKILL_DIR}/scripts/render_all_slides.sh \
    $WORK/html-slides/ \
    $WORK/figures-rendered/

# Step D. PNG を PPTX に 1 スライド 1 画像でフルブリード配置
python3 ${SKILL_DIR}/scripts/build_rich_pptx.py \
    --rendered-dir $WORK/figures-rendered/ \
    --output ~/patent/<案件名>/output/発明説明資料.pptx
```

#### スライド構成例（中規模発明 18 枚）

| # | 内容 | テンプレ |
|---|---|---|
| 01 | 表紙 | `rich-slide.cover.html` |
| 02 | アジェンダ | `rich-slide.template.html` |
| 03 | 1.1 業界の状況（数値ファクト＋構造図） | template |
| 04 | 1.2 現状の課題（6 課題カード） | template |
| 04b | 1.3 公知例の代表例（論文 Fig 引用） | template + `figure-from-papers.md` |
| 05 | 2.1 本発明の目的（ヒーロー＋4 目的） | template |
| 06 | 3.1 発明概要（アーキ全体図） | template |
| 07-09 | 3.2-3.4 発明のポイント（独立項・従属項） | template |
| 10-14 | 4. 実施例（UI モック・概念図） | template |
| 15 | 5.1 独立請求項のサマリ | template |
| 16 | 5.2 公知例差別化表 | template（`table.compare` 利用） |
| 17 | 5.3 実測ベンチマーク | template |
| 18 | クロージング | template |

#### レビュー観点

ユーザに見せる前に、Claude 自身が以下を必ず Read で目視チェック:

- [ ] 文字が画面から溢れていないか（1920x1080 内に収まる）
- [ ] 配色が `common.css` のデザインシステムに沿っているか
- [ ] 各スライドのフッタにページ番号と注記が入っているか
- [ ] 論文図を引用しているスライドは出典枠が完備されているか
- [ ] 日本語フォントが正しくレンダされているか（豆腐がないか）

問題があれば HTML を修正して 1 枚だけ再レンダ（Step C 相当を該当ファイルだけ実行）。

### 3.5. （任意）表紙／概念図を banana で生成する

ユーザーが「表紙の絵を AI で作って」「概要図を bananaで生成して」のように **明示的に依頼した場合のみ** 実施する。デフォルトはスキップ。

**用途と範囲:**
- ✅ 表紙のヒーロー画像、コンセプトイラスト、ワークフロー俯瞰図
- ❌ 実施例のUIモック（次項 §4 の HTML/CSS 方式を使う）
- ❌ 図面（Phase 4 で扱うため）

**必ず二段階方式：** Gemini は日本語フォントの描画が崩れやすいため、画像内に直接日本語を入れさせない。

```bash
# Step A. JSON 仕様を作る（templates/banana-spec.example.json を雛形に複製）
cp ${SKILL_DIR}/templates/banana-spec.example.json \
   ~/patent/<案件名>/work/banana-specs/overview.json
# overview.json を編集：prompt（テキストなし英文）と labels（日本語ラベル）を書く

# Step B. テキストなしのブランクレイアウトを Gemini で生成
python3 ${SKILL_DIR}/scripts/build_banana_image.py \
  --spec ~/patent/<案件名>/work/banana-specs/overview.json \
  --output ~/patent/<案件名>/work/banana-blank/overview.png

# Step C. ブランクPNGに日本語ラベルを PIL で合成
python3 ${SKILL_DIR}/scripts/compose_jp_labels.py \
  --image ~/patent/<案件名>/work/banana-blank/overview.png \
  --spec ~/patent/<案件名>/work/banana-specs/overview.json \
  --output ~/patent/<案件名>/work/figures-rendered/overview.png
```

仕様の書き方・色設計・ラベル overrides・トラブルシューティングは `references/banana-image-gen.md` 参照。

生成した PNG は `output/発明説明資料.pptx` のスライドに `add_image_with_bubbles()` などで埋め込む。

### 4. 実施例スライドのUIモック（HTML/CSS方式）

**実施例（発明の動作・画面例）のUIは AI画像生成（banana等）を使わない。** 代わりに HTML/CSS でモックを記述し、Puppeteer で PNG にレンダリングして埋め込む。これは「実装した画面」としての証拠性、再現性、編集性を担保するため。

#### 4.1 簡易UIモック（請求項1〜2の概念図レベル）

最低限の構造（ヘッダ・タブ・メインパネル）でアイデアの動作を示せれば十分なケース：

1. `work/html-mockups/<実施例名>.html` を作成（`templates/ui-mockup.template.html` をベースに）
2. `render_html.js` で PNG 化:
   ```bash
   node ${SKILL_DIR}/render-tools/render_html.js \
     ~/patent/<案件名>/work/html-mockups/A.html \
     ~/patent/<案件名>/work/figures-v2/A.png
   ```
3. PNG を `output/発明説明資料.pptx` のスライドに埋め込み、ネイティブの噴き出し（**ROUNDED_RECTANGULAR_CALLOUT＝角丸＋しっぽ付き吹き出し図形**）で機能説明を追加。`add_speech_bubble(..., anchor=(tx, ty))` を使うと、しっぽの先端が anchor 座標を指すよう adj 値が自動調整される

#### 4.2 詳細実施例スライド（推奨：5〜7枚で実装イメージを完全に伝える）

請求項対象がWebアプリ・業務システム・データ可視化システムである場合、**実装が想像できるレベルの詳細UIモック** を複数枚（推奨5〜7枚）作ると、進歩性主張と説明会（社内出願審議会・特許事務所打合せ等）の説得力が大幅に上がる。

**作り方は `references/detailed-exhibit-design.md` の対話的ヒアリングフロー（Q-0〜Q-7）に従う**。要点：

1. **Q-0**: 機能領域とサブ画面の一覧を発明者にヒアリングし、企画表で確認
2. **Q-1〜Q-7** をスライドごとに3〜5問ずつ対話：主張・画面種別・エンティティ・インタラクション・吹き出し・サンプルデータ・デザイントーン
3. **デザインシステム**を統一（主色・バッジ色・余白・タイポグラフィ）
4. **HTML→PNG→ユーザレビュー** を2〜3イテレーション回す
5. **吹き出し2〜4個**でanchor付きcalloutを追加し、各callout テキストに対応請求項要素を明記
6. **品質チェックリスト**（11項目）で最終確認

Claudeはこのフローを **一度に全部聞かず**、`AskUserQuestion` で3〜5問ずつ（ツール上限4問）に分けて段階的にヒアリングする。画面種別・レイアウト・デザイントーンのように候補が列挙できる問いは必ず選択肢で提示する。詳細は `references/detailed-exhibit-design.md` を必ず読んでから開始。

### 5. レイアウトの注意点

- 新規追加スライドは **'タイトルのみ' レイアウト** を使う（`prs.slide_layouts[2]`）。
  `4_白紙` レイアウトは末尾の closing logo スライド用で、コンテンツに使わない
- フォントは **Yu Gothic UI** に統一（全テキストランに対して `run.font.name = "Yu Gothic UI"` を一括適用）
- **テキストボックスの文字色は基本黒（`#000000`）**。タイトル・サブタイトル・アクセント色（青系の見出しなど）は例外として明示的に色指定するが、本文・吹き出し本文・キャプション類はすべて黒で書く（`pptx_helpers.DEFAULT_BUBBLE_TEXT = (0,0,0)`）。背景色とのコントラスト確保と、印刷時の判読性のため
- **ページ番号** はテンプレ内の個別テキストボックスにハードコードされている場合があり、スライド並べ替え後に番号がずれる。`scripts/pptx_helpers.py` の `update_hardcoded_page_numbers()` で一括補正できる

### 5.1. 共通ヘルパーの利用

繰り返し使う処理は `scripts/pptx_helpers.py` に集約済み。新規案件のビルドスクリプトでは import して使う：

```python
from pptx_helpers import (
    find_layout, add_content_slide,
    find_shape_by_substring, replace_text_preserving_style,
    add_textbox, add_speech_bubble, add_leader_line,
    add_image_with_bubbles, reorder_slides, unify_font,
    update_hardcoded_page_numbers,
)

prs = Presentation("inputs/invention-explainer-wip.pptx")
# テキスト改訂
s = list(prs.slides)[10]
t = find_shape_by_substring(s, "古い文")
replace_text_preserving_style(t, "新しい文")
# 実施例スライド追加
s = add_content_slide(prs, "４．発明の実施例")
add_textbox(s, 0.5, 0.95, 12.3, 0.4, "サブタイトル", size=14, bold=True, color=(0x00,0x70,0xC0))
add_image_with_bubbles(s, "work/figures-v2/A.png", img_top=1.55, img_max_h=4.4,
    bubbles=[(0.3, 5.95, 5.5, 1.2, "説明文", (4.0, 5.5))])
# 各 bubbles エントリは (x, y, w, h, text, anchor) の 6-tuple。
# anchor=(tx, ty) を指定すると ROUNDED_RECTANGULAR_CALLOUT が使われ、
# しっぽの先端が anchor を指すよう adj 値が自動調整される。
# anchor=None の場合は ROUNDED_RECTANGLE（しっぽなし）にフォールバック。
# 並べ替え
reorder_slides(prs, [0,1,...])
# フォント統一
unify_font(prs)
# ページ番号補正
update_hardcoded_page_numbers(prs, start_page=1)
```

### 5.2. よくあるレイアウト失敗とその回避

以下は germline 案件で実際に発生した不具合と対応。汎用的に気をつけたい。

#### (a) 既存タイトルを更新するとき、複数runにわたるテキストが重複する
- 症状: title placeholder のテキストに新タイトルが2回出現（例「がんゲノム検査における…再評価支援システム(仮)がんゲノム検査における…」）
- 原因: 元タイトルが複数の `<a:r>` (run) に分かれているとき、各 run を個別に `run.text = "新タイトル"` で置き換えると、それぞれが全文に膨らみ重複する
- 回避: **タイトル置換は `replace_text_preserving_style(shape, new_text)`** を使う。内部で text_frame を `tf.clear()` してから1段落で再構築するので重複しない

#### (b) サブタイトル/メモが title placeholder と重なる
- 症状: 旧スライドに「請求項X対応」などのサブタイトルを top-left に追加すると、`タイトルのみ` レイアウトの **title placeholder（x=0.17, 幅 5.81 inch）** と重なる
- 回避: 既存タイトルが top-left の場合、サブタイトルは **x=6.0 以上** に配置し、`align=PP_ALIGN.RIGHT` で右寄せして title PH と並列にする
  ```python
  add_textbox(slide, x=6.1, y=0.25, w=6.9, h=0.5, text=...,
              size=12, bold=True, align=PP_ALIGN.RIGHT, color=(0x00,0x70,0xC0))
  ```

#### (c) スライド並べ替えで orphan XML ファイルが残る
- 症状: `reorder_slides()` で `desired_order` から外したスライドが、ZIP 内の `slide{N}.xml` として残り続ける（python-pptx が ZIP の物理削除を自動で行わないため）
- 影響: PowerPoint では参照されないので開く分には問題ないが、ファイルサイズに数十KB上乗せ
- 回避: 完全クリーンが必要なら、`inputs/invention-explainer-wip.pptx` から **一度のスクリプト実行** で完結する build script を書く（途中でファイルを上書き保存しながら段階的に組み立てない）

#### (d) ページ番号が並べ替え後にズレる
- 元WIPの各スライドにはハードコードされた番号テキストボックスが含まれる場合がある
- `update_hardcoded_page_numbers(prs, start_page=1)` を最終ステップで呼ぶと、「1〜3桁の数字だけのテキストボックス」を現在の位置の番号で上書きする
- ⚠ 数字だけのテキスト（例: "9" のような有意味な数値）も対象になるリスクがあるので、新規追加スライドにはそういうテキストを置かない

### 6. 視覚確認

approx バックエンドで PNG 化（レイアウト確認用、日本語と画像は描画されない）:
```bash
python3 ~/.claude/skills/pptx-task-ops/scripts/pptx_rasterize.py \
  ~/patent/<案件名>/output/発明説明資料.pptx \
  --out-dir ~/patent/<案件名>/work/slide-previews \
  --backend approx
```

最終的な視覚確認は PowerPoint で実機確認、または LibreOffice インストール後の `soffice` バックエンドで行う。

### 4. 仕上げ

- 生成された .pptx は機械的なレイアウト。**最終調整はPowerPointで人間が行う前提。**
- ユーザーに「PowerPointで開いて見栄えを調整してください」と必ず伝える。
- スクリプトは表紙の日付を today の `YYYY/M/D` 形式で自動挿入する。

## サンプルから抜き出した推奨スタイル

- フォント: Yu Gothic / Meiryo（CJK 対応）
- 表紙の日付フォーマット: `YYYY/M/D` （例 `2026/2/3`）
- スライド比率: 16:9
- セクション扉スライドを各セクション冒頭に入れる（オプション）
