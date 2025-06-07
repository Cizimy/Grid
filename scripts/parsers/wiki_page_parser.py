import json
from bs4 import BeautifulSoup, Tag

class DanbooruWikiPageParser:
    """
    DanbooruのWikiページのHTMLコンテンツを解析し、構造化されたデータを抽出するクラス。
    """

    def __init__(self, html_content: str):
        """
        コンストラクタ。HTMLコンテンツを受け取り、BeautifulSoupオブジェクトを初期化する。

        Args:
            html_content: パース対象のHTML文字列。
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')

    def parse(self) -> dict:
        """
        全ての抽出メソッドを呼び出し、結果を単一の辞書オブジェクトに集約して返す。

        Returns:
            抽出されたデータを含む辞書。
        """
        return {
            'tag_name': self._extract_tag_name(),
            'wiki_description': self._extract_wiki_description(),
            'aliases': self._extract_aliases(),
            'implicates_this_tag': self._extract_implicates_this_tag(),
            'see_also': self._extract_see_also(),
        }

    def _extract_tag_name(self) -> str | None:
        """ページの中心となるタグ名を抽出する。"""
        tag_element = self.soup.select_one('h1#wiki-page-title a')
        return tag_element.get_text(strip=True) if tag_element else None

    def _extract_wiki_description(self) -> str | None:
        """タグの主な説明文を抽出する。"""
        description_element = self.soup.select_one('div#wiki-page-body > p')
        # 'leg up' のように説明文中にリンクが含まれる場合、get_text()が単語を結合してしまう問題の対策
        return description_element.get_text(separator=' ', strip=True) if description_element else None

    def _extract_aliases(self) -> list[str]:
        """エイリアスタグのリストを抽出する。"""
        aliases = []
        p_tags = self.soup.find_all('p', class_='fineprint')
        for p_tag in p_tags:
            if isinstance(p_tag, Tag) and 'The following tags are aliased to this tag:' in p_tag.get_text():
                # "learn more" のリンクを除外する
                aliases = [
                    a.get_text(strip=True) for a in p_tag.select('a.wiki-link')
                    if a.has_attr('href') and 'help:tag_aliases' not in a['href']
                ]
                break
        return aliases

    def _extract_implicates_this_tag(self) -> list[str]:
        """このタグを含意する子タグのリストを抽出する。"""
        implicates = []
        p_tags = self.soup.find_all('p', class_='fineprint')
        for p_tag in p_tags:
            if isinstance(p_tag, Tag) and 'The following tags implicate this tag:' in p_tag.get_text():
                # "learn more" のリンクを除外する
                implicates = [
                    a.get_text(strip=True) for a in p_tag.select('a.wiki-link')
                    if a.has_attr('href') and 'help:tag_implications' not in a['href']
                ]
                break
        return implicates

    def _extract_see_also(self) -> list[str]:
        """「See Also」セクションの関連タグリストを抽出する。"""
        see_also_header = self.soup.find('h4', string='See also')
        if not see_also_header:
            # "See also" が見つからない場合、大文字小文字を区別しない検索を試みる
            import re
            see_also_header = self.soup.find('h4', string=re.compile(r'See also', re.I))

        if see_also_header:
            ul_element = see_also_header.find_next_sibling('ul')
            # Pylanceの型推論エラーを回避するため、ul_elementがTagインスタンスであることを確認
            if isinstance(ul_element, Tag):
                return [a.get_text(strip=True) for a in ul_element.select('a')]
        return []

if __name__ == '__main__':
    # このスクリプトを直接実行した際の動作確認用コード
    # 事前に 'lying.html' と 'leg_up.html' をダウンロードして同じディレクトリに配置してください。
    
    # --- lying.html のテスト ---
    try:
        with open('lying.html', 'r', encoding='utf-8') as f:
            html_content_lying = f.read()
        
        parser_lying = DanbooruWikiPageParser(html_content_lying)
        parsed_data_lying = parser_lying.parse()
        
        print("--- Parsed data from lying.html ---")
        print(json.dumps(parsed_data_lying, indent=2, ensure_ascii=False))

    except FileNotFoundError:
        print("\nWarning: 'lying.html' not found. Skipping test.")
    except Exception as e:
        print(f"\nAn error occurred while parsing lying.html: {e}")

    # --- leg_up.html のテスト ---
    try:
        with open('leg_up.html', 'r', encoding='utf-8') as f:
            html_content_leg_up = f.read()

        parser_leg_up = DanbooruWikiPageParser(html_content_leg_up)
        parsed_data_leg_up = parser_leg_up.parse()

        print("\n--- Parsed data from leg_up.html ---")
        print(json.dumps(parsed_data_leg_up, indent=2, ensure_ascii=False))

    except FileNotFoundError:
        print("\nWarning: 'leg_up.html' not found. Skipping test.")
    except Exception as e:
        print(f"\nAn error occurred while parsing leg_up.html: {e}")