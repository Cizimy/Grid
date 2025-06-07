# Pythonスクリプト設計書： DanbooruRelatedTagParser (v1.2)

**バージョン:** 1.2
**更新概要:** 4指標（`Cosine`, `Jaccard`, `Overlap`, `Frequency`）それぞれでソートされたページを個別にパースすることを前提とした設計に修正。

## 1. 概要
このスクリプトは、Danbooruの「Related Tags」ページのHTMLを**単一の指標でソートされた状態で**入力として受け取り、テーブル情報を解析する。各関連タグについて、4つ全ての統計指標とポスト数を抽出した辞書のリストを生成する。
**このパーサーは、4回の異なるリクエストから得られる4つのHTMLそれぞれに対して個別に実行されることを想定する。**

## 2. 前提条件
- 入力は、特定の`order`パラメータ（`Cosine`, `Jaccard`, `Overlap`, `Frequency`のいずれか）でソートされたDanbooruのRelated Tagsページの完全なHTMLソースコード。

## 3. 使用ライブラリ
- `bs4` (BeautifulSoup4)

## 4. 設計方針
- **単一テーブル責務:** このクラスは、渡された**単一のHTMLページ（＝単一のソート順）**のテーブルをパースすることにのみ責任を持つ。どの指標でソートされたページなのかを意識する必要はない。
- **完全なデータ抽出:** 設計書v1.1を踏襲し、各行から4つ全ての統計指標とポスト数を抽出する。
- **堅牢なデータ変換:** 設計書v1.1を踏襲し、ポスト数の接尾辞（k, M）やパーセント表記を正しく数値に変換する。

## 5. クラスとメソッド設計
**クラス名:** `DanbooruRelatedTagParser`

| メソッド名 | public/private | 目的 | 返り値 |
| :--- | :--- | :--- | :--- |
| `__init__(self, html_content)` | public | コンストラクタ | `None` |
| `parse(self, limit=100)` | public | テーブル全体をパースし、関連タグ情報の辞書のリストを返す。 | `list[dict]` |
| `_parse_table(self, limit)` | private | `table.striped`内の各行を走査する。 | `list[dict]` |
| `_parse_row(self, row_element)` | private | 単一のテーブル行から全情報を抽出する。 | `dict` or `None` |
| `_clean_post_count(self, post_count_span)` | private | ポスト数を整数に変換する。 | `int` |
| `_clean_percentage(self, text)` | private | パーセント表記を`float`に変換する。 | `float` |

## 6. 最終的な出力データ構造
`parse()` メソッドが返すリスト内の各辞書の構造。
```json
[
  {
    "tag": "on_back",
    "post_count": 276839,
    "cosine": 74.83,
    "jaccard": 56.18,
    "overlap": 99.25,
    "frequency": 56.42
  }
]
```

## 7. 上位の統合クラス (`DanbooruScraper`) での実装方針（v1.2更新版）
4回のリクエストと、その結果をマージするロジックが必要になる。

1.  **非同期リクエスト:**
    - `asyncio`と`httpx`を使い、1つのタグに対して**4つのURL**（`order=Cosine`, `order=Jaccard`, `order=Overlap`, `order=Frequency`）へのリクエストを**並列で実行**する。
2.  **並列パース:**
    - 4つのHTMLコンテンツが取得できたら、それぞれに対して`DanbooruRelatedTagParser`をインスタンス化し、`parse()`を実行する。このパース処理も並列で実行可能。
3.  **スマートマージ処理:**
    - 4つのリスト（最大`100件 * 4`のデータ）を取得したら、**`tag`名をキーとして1つの辞書にマージ**する。これにより、重複するタグは1つにまとめられ、各指標の値がすべて格納されたマスターデータが完成する。
4.  **最終データ生成:**
    - `DanbooruWikiPageParser`から得たWiki情報と、このマスターデータを結合し、AIへの最終的な入力JSONを生成する。