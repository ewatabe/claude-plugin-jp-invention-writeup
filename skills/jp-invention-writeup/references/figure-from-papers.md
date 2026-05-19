# 論文の図をスライドに引用するパイプライン

公知例論文や標準ガイドライン論文の図（アーキテクチャ図・フローチャート等）を、
**社内発明審議会・特許事務所打合せ用** の発明説明資料に引用する際の標準パイプラインを示す。

## 重要：用途と法的制約

| 用途 | 可否 | 根拠 |
|---|---|---|
| **特許明細書の図面** として転載 | ✗ 厳禁 | 他社著作物を出願書類に組み込むのは特許性と無関係にトラブル要因。図面は自作のみ |
| **社内発明審議会・事務所打合せ用スライド** で引用 | ◯ 引用要件を満たせば可 | 公表せず内部資料／出典明記／必要最小限なら著作権法第32条の「引用」に該当 |
| **論文・学会発表** で転載 | △ 多くは要許諾 | Nature/Elsevier 系は RightsLink で要許諾、arXiv/bioRxiv は CC 系で多くが可 |
| **特許出願後のプレスリリース・記者発表** | △ 著作権者許諾必要 | 必ず別途確認 |

→ **既定方針：「社内発明説明資料・事務所打合せ用」に限定し、出典を必ず明記**。
特許出願書類（明細書、図面 PPTX）への転載は行わない。

## ライセンス判定の早見表

| 媒体 | 通常ライセンス | 引用扱い |
|---|---|---|
| **arXiv** | CC BY 4.0 など（投稿者選択） | 出典明記で社内・対外問わず利用しやすい |
| **bioRxiv / medRxiv** | CC BY / CC0 など（プレプリント標準） | 概ね arXiv と同等 |
| **PMC（Open Access）** | 個別記事の OA ライセンスに依存 | 記事ページの "License" を確認 |
| **Elsevier / Nature 系 published 版** | 多くは要許諾 | プレプリント版があればそちらを優先 |
| **特許文献の図** | パブリックドメインに準ずる扱い | 出典明記すれば自由 |

スライド引用時は、図のキャプション枠に **著者・タイトル・誌名・年・URL ／ ライセンス** を必ず付ける。

## 標準パイプライン

### Step 1: 論文 PDF を取得

可能なら **CC ライセンスのプレプリント版**（arXiv / bioRxiv / medRxiv）から取得する。

```bash
mkdir -p ~/patent/<案件名>/inputs/references
cd ~/patent/<案件名>/inputs/references

# arXiv
curl -sL -o paper.pdf "https://arxiv.org/pdf/<arxiv-id>"

# bioRxiv / medRxiv (推定 PDF URL)
curl -sL -o paper.pdf "https://www.biorxiv.org/content/<doi>v1.full.pdf"
```

PMC は直接 PDF URL を返さないケースが多い。`PMC<id>` のページから手動で PDF をダウンロードして配置するのが確実。

### Step 2: 図のあるページを特定して画像化

```bash
# 図 1 を含むページ範囲を 200dpi で PNG レンダ
pdftoppm -r 200 -f 1 -l 5 paper.pdf paper-page -png
ls paper-page-*.png
```

`-f N -l M` で N〜M ページを指定。Figure の番号と論文の冒頭ページ数を見て決める。

### Step 3: 図領域を切り抜き（PIL）

ページ画像（例: 1700x2200 px）から、図がある領域を相対座標で指定して切り抜く。

```python
from PIL import Image
img = Image.open("paper-page-2.png")
w, h = img.size

# 例: ページ上部 4-32% の領域に Figure 2 がある
crop = img.crop((int(w*0.04), int(h*0.04), int(w*0.96), int(h*0.32)))
crop.save("fig2.png")
```

切り抜き範囲はページを目視 (`Read` ツールで画像表示) で確認しながら調整する。
**キャプション行（"Figure N: ..."）も含めて切り抜く** と引用元が PNG 内で自己完結して便利。

### Step 4: スライド HTML に埋め込み

`templates/rich-slide.common.css` に用意した `.paper-figframe` と `.paper-src` を使う。

```html
<div class="card">
  <div class="ph">PRIOR ART / <論文略称></div>
  <div class="ti"><論文タイトル></div>

  <div class="paper-figframe">
    <img src="fig2.png" alt="Figure 2">
  </div>

  <div class="paper-src">
    <b>Source:</b> <著者>, <i>"<論文タイトル>"</i>, <誌名> <id> (<年>), Fig. N.
    <span class="lic">CC BY 4.0</span><br/>
    <b>本発明との差：</b> <差別化要素を 1-2 行>
  </div>
</div>
```

切り抜いた PNG（`fig2.png`）は HTML と同じディレクトリ（`work/html-slides/`）に置くか、相対パスで参照する。

### Step 5: 引用注記をスライドフッタに追加

スライド `slide-footer` に以下を必ず入れる:

```html
<div class="slide-footer">
  <div>出典の図は引用目的（著作権法第32条）に基づく、社内検討資料での参照。商用配布・公表時は別途許諾を確認。</div>
  <div>P. N</div>
</div>
```

## 推奨対象論文（領域別）

| 領域 | 推奨論文 | 用途 |
|---|---|---|
| 自己進化型エージェント全般 | Voyager (arXiv:2305.16291) | Fig. 2 = 3 要素アーキテクチャ（汎用エージェントの代表例） |
| 生体医学自己進化エージェント | STELLA (arXiv:2507.02004) | Fig. 1 = 4-agent + Template Library + Tool Ocean |
| 推論戦略蓄積 | ExpeL (AAAI 2024) | insight 抽出アーキテクチャ |
| スキル獲得（最新） | CASCADE (arXiv:2512.23880) | "LLM + tool use → skill acquisition" の概念図 |
| 臨床ガイドライン点数制 | Horak et al. 2022 (Genet Med) / Li et al. 2017 (JMD) | VICC oncogenicity / AMP-ASCO-CAP 標準フローチャート |
| 変異解釈自動化 | CancerVar / InterVar | ルールベース型自動分類のアーキテクチャ |

## チェックリスト

引用前に確認:

- [ ] 論文の正式ライセンスを確認（PDF 1 ページ目またはホストページ）
- [ ] 自社が **公表する資料** には埋め込まない（社内・事務所限定）
- [ ] 図のキャプションに **著者・誌名・年・Fig 番号** を明記
- [ ] **ライセンス表記**（CC BY 4.0 等）を併記
- [ ] スライドフッタに **引用目的の注記** を入れる
- [ ] 切り抜きで **トリミング・改変** が過度でない（原図の趣旨が伝わる範囲）
- [ ] **本発明との差** を 1-2 行で添えて、引用が単なる装飾でないことを示す（引用の必然性）

## サンプル実装

`shinka-skill-acquisition` 案件で実装した 04b スライド（Voyager Fig 2 + STELLA Fig 1）が参考実装。
`work/html-slides/04b-prior-art-figures.html` と切り抜き済の `voyager-fig2.png` / `stella-fig1.png` の組合せ。
