# 実装イメージ画面（UIモック）のHTML/CSS記法

実施例スライドの「実装時の画面」を **HTML/CSS + SVG** で記述する規約。
Puppeteer で 1920x1080 PNG にレンダリングして PPTX に埋め込む。

## なぜ HTML/CSS なのか（banana 画像生成を使わない理由）

- AI 生成画像は「それっぽい絵」になり、ボタン名や項目名が微妙に変わる／実装と一致しない
- 引出線・符号が再生成のたびに位置変動 → 明細書文章との整合が取れない
- テキスト編集不可、ベクター性なし
- 特許庁提出図面はベクター線画が基本

HTML/CSS で書けば：実装したWebアプリのスクショと同等の証拠性／再現性／編集性が得られる。

## 出発点

スキル同梱の `templates/ui-mockup.template.html` をコピーして編集する：

```bash
cp ${SKILL_DIR}/templates/ui-mockup.template.html \
   ~/patent/<案件名>/work/html-mockups/A_実施例名.html
```

## ベースHTMLテンプレート

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>実施例N: タイトル</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Noto Sans JP', 'Yu Gothic UI', system-ui, sans-serif; }
  .slide { width: 1920px; height: 1080px; background: #FAFBFC; display: flex; flex-direction: column; }
  .header { height: 72px; background: #1F6FEB; display: flex; align-items: center; padding: 0 32px; color: #fff; }
  .tabs { height: 56px; background: #fff; border-bottom: 1px solid #E1E4E8; display: flex; padding: 0 32px; align-items: center; gap: 4px; }
  .tab { padding: 14px 22px; font-size: 16px; color: #57606A; border-bottom: 3px solid transparent; }
  .tab.active { color: #1F6FEB; border-bottom-color: #1F6FEB; font-weight: 600; }
  .main { flex: 1; display: flex; padding: 24px; gap: 24px; }
  .panel { background: #fff; border: 1px solid #E1E4E8; border-radius: 8px; padding: 20px; }
  .footer { height: 32px; background: #F6F8FA; border-top: 1px solid #E1E4E8; padding: 0 32px; font-size: 11px; color: #6E7781; }
</style>
</head>
<body>
<div class="slide">
  <div class="header">...</div>
  <div class="tabs">...</div>
  <div class="main">
    <div class="panel">...</div>
    <div class="panel">...</div>
  </div>
  <div class="footer">...</div>
</div>
</body>
</html>
```

## 必須ルール

1. **サイズ**: スライドは必ず `1920px × 1080px`（16:9）
2. **フォント**: `Noto Sans JP` を Google Fonts CDN から読み込む。Yu Gothic UI もフォールバックに
3. **絵文字を使わない**: 一部の絵文字（👁📞📅🔬等）はChromiumで豆腐になる場合あり。Unicode 記号（◉ ⚭ ✉ ⚗ ↺ ▣ ⏸ 等）で代替するか SVG アイコンを使う
4. **チャート・図形は SVG で記述**: 散布図、家系図、フローチャート等は `<svg viewBox="...">` で記述。テキストラベルも SVG 内の `<text>` で
5. **架空のサンプル名は「山田 花子」等の中立名で統一**: 症例・ユーザー名が必要な場面では `山田花子`（姓名スペースなし）または `山田 花子`（スペースあり）を既定とし、家族なら `山田 由美` 等で姓を揃える。`pptx_helpers.SAMPLE_USER_NAME` 定数に同じ値が定義されているので、Python側のスライドビルダでも同じ名前を参照する。実在の人物・組織を想起させる固有名は避ける
6. **アクセント色は専門領域に合わせる**: 1スライドに1主色を選んで全体（ヘッダ・タブactive・主要バッジ）に適用すると統一感が出る

| 主領域の例 | 主色 | 用例 |
|---|---|---|
| データ解析 / 分析系 | 青系 `#1F6FEB` | 解析ダッシュボード、診断支援 |
| アラート / 通知 / 重要イベント | 暖色 `#D9534F` | 警告画面、要対応リスト |
| 同意 / 法務 / 契約 | 緑系 `#10A37F` | 承認管理画面、契約フロー |
| 推奨 / マッチング | 紫系 `#7C4DFF` | レコメンド、マッチング |
| 知識ベース / 参照 | ティール `#0EA5A8` | 文献参照、知識データ管理 |

※ 上記は1例。案件のドメインに応じて主色マッピングを変えてよい。

副色（バッジ・ピル）は **緑=確定／黄=要対応／赤=重要** の3色で統一すると認知負荷が下がる。
6. **タブの active 状態**: 該当機能のタブを `.tab.active` で強調表示。実装イメージの整合性

## 構成パターン

### パターンA: 左メイン + 右リスト
- 左 60-65%: メイン可視化（チャート/図/テーブル）
- 右 35-40%: リスト・詳細情報・状態カード

例: 解析結果の散布図 + 候補リスト

### パターンB: 左可視化 + 右リスト + 上部通知
- 上部: 通知バナー（イベント情報）
- 左 60-70%: 関係図 / 図表
- 右 30-40%: 行動候補リスト

例: 関係図（家系図・組織図など）+ 行動推奨リスト

### パターンC: 左テーブル + 右フロー
- 左 55%: データテーブル（属性項目等）
- 右 45%: 判断フローチャート + 出力先カード

例: 属性プロファイル + 配信範囲決定フロー

## オフライン環境でのフォント取得

Google Fonts CDN にアクセスできない環境では、Noto Sans JP をローカルに配置して `@font-face` で読み込む：

```bash
# Noto Sans JP を一度だけダウンロード
mkdir -p ~/.local/share/fonts/NotoSansJP
cd ~/.local/share/fonts/NotoSansJP
curl -LO https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansJP-Regular.otf
curl -LO https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansJP-Bold.otf
fc-cache -f
```

または apt: `sudo apt install fonts-noto-cjk`（500MB+）。

HTML 側で `<link>` を外して、システム経由で読ませる：
```html
<style>
  body { font-family: 'Noto Sans JP', 'Yu Gothic UI', sans-serif; }
</style>
```

## レンダリング

```bash
node ${SKILL_DIR}/render-tools/render_html.js \
  <input.html> <output.png> \
  [--width 1920 --height 1080 --dpi 2]
```

DPI 2 で 3840x2160 の高解像度PNG が出力される（PPTX 埋め込み後も鮮明）。

## PPTX への埋め込み

`scripts/build_explainer_pptx.py` または個別のビルドスクリプトで：
- 'タイトルのみ' レイアウトでスライド追加
- タイトル：「４．発明の実施例」
- サブタイトル: 機能名と関連請求項
- 中央に PNG を配置（高さ約 4.4 inch）
- **ROUNDED_RECTANGULAR_CALLOUT**（角丸＋しっぽ付き吹き出し図形）で機能説明を追加。`add_speech_bubble(..., anchor=(tx, ty))` を呼ぶと、しっぽが anchor 座標を指すよう adj 値が自動調整される。separate な connector / 引出線は不要
- 噴き出し内テキストは v2 UI に出てくる要素名（タブ名・パネル名等）を参照すると整合性が出る
- 噴き出し本文の文字色は **黒**（`pptx_helpers.DEFAULT_BUBBLE_TEXT = (0,0,0)`）が既定。タイトル・サブタイトル・アクセントテキスト以外は基本黒で書く
