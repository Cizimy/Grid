import re
from bs4 import BeautifulSoup, Tag

class DanbooruRelatedTagParser:
    """
    Danbooruの「Related Tags」ページのHTMLコンテンツを解析し、
    関連タグの完全な統計情報を抽出するクラス。
    """

    def __init__(self, html_content: str):
        """
        コンストラクタ。HTMLコンテンツを受け取り、BeautifulSoupオブジェクトを初期化する。
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')

    def parse(self, limit: int = 100) -> list[dict]:
        """
        テーブル全体をパースし、関連タグ情報の辞書のリストを返す。

        Args:
            limit: 取得するタグの最大数。

        Returns:
            抽出された関連タグ情報のリスト。
        """
        return self._parse_table(limit)

    def _parse_table(self, limit: int) -> list[dict]:
        """
        `table.striped`内の各行を走査し、`_parse_row`を呼び出して結果をリストにまとめる。
        """
        table = self.soup.select_one('table.striped')
        if not isinstance(table, Tag):
            return []

        rows = table.select('tbody tr')
        parsed_data = []
        for row in rows[:limit]:
            if isinstance(row, Tag):
                parsed_row = self._parse_row(row)
                if parsed_row:
                    parsed_data.append(parsed_row)
        return parsed_data

    def _parse_row(self, row_element: Tag) -> dict | None:
        """
        単一のテーブル行(`tr`)から、タグ名、ポスト数、4つの統計指標を抽出し、
        一つの辞書として返す。
        """
        try:
            name_cell = row_element.select_one('.name-column')
            if not name_cell: return None

            # タグ名は2番目の 'a' タグ
            tag_name_element = name_cell.select('a')[1]
            tag_name = tag_name_element.get_text(strip=True)

            # ポスト数
            post_count_span = name_cell.select_one('span.post-count')
            post_count = self._clean_post_count(post_count_span) if post_count_span else 0

            # 各指標
            def get_metric_value(column_class: str) -> str:
                element = row_element.select_one(f'.{column_class} span')
                return element.get_text() if element else "0"

            cosine = self._clean_percentage(get_metric_value('cosine-column'))
            jaccard = self._clean_percentage(get_metric_value('jaccard-column'))
            overlap = self._clean_percentage(get_metric_value('overlap-column'))
            frequency = self._clean_percentage(get_metric_value('frequency-column'))

            return {
                "tag": tag_name,
                "post_count": post_count,
                "cosine": cosine,
                "jaccard": jaccard,
                "overlap": overlap,
                "frequency": frequency,
            }
        except (IndexError, AttributeError, ValueError):
            # 必須要素が見つからない、またはデータ形式が不正な行はスキップ
            return None

    def _clean_post_count(self, post_count_span: Tag) -> int:
        """
        span要素からポスト数を抽出し、'k'や'M'を考慮して整数に変換する。
        title属性に正確な数値が含まれているため、それを優先する。
        """
        if post_count_span.has_attr('title'):
            try:
                title_attr = post_count_span['title']
                # title属性がリストの場合でも最初の要素を取得
                title_str = title_attr[0] if isinstance(title_attr, list) else title_attr
                return int(str(title_str).replace(',', ''))
            except (ValueError, TypeError, IndexError):
                pass # title属性が不正な場合はテキストからの変換を試みる

        text = post_count_span.get_text(strip=True).lower()
        try:
            if 'k' in text:
                return int(float(text.replace('k', '')) * 1000)
            if 'm' in text:
                return int(float(text.replace('m', '')) * 1000000)
            return int(text)
        except ValueError:
            return 0

    def _clean_percentage(self, text: str) -> float:
        """パーセント表記の文字列（例: "99.25%"）をfloatに変換する。"""
        try:
            return float(text.replace('%', '').strip())
        except (ValueError, AttributeError):
            return 0.0

if __name__ == '__main__':
    # このスクリプトを直接実行した際の動作確認用コード
    # 事前に 'related_tags_cosine.html' をダウンロードして配置してください。
    import json
    try:
        with open('related_tags_cosine.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = DanbooruRelatedTagParser(html_content)
        # 上位5件だけパースしてみる
        parsed_data = parser.parse(limit=5)

        print("--- Parsed data from related_tags_cosine.html (top 5) ---")
        print(json.dumps(parsed_data, indent=2, ensure_ascii=False))

    except FileNotFoundError:
        print("\nWarning: 'related_tags_cosine.html' not found. Skipping test.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")