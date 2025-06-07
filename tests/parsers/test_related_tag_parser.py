import pytest
import os
from scripts.parsers.related_tag_parser import DanbooruRelatedTagParser

# プロジェクトのルートディレクトリを基準にフィクスチャのパスを解決
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')

@pytest.fixture
def related_tags_cosine_html():
    """related_tags_cosine.htmlのコンテンツを読み込むpytestフィクスチャ"""
    with open(os.path.join(FIXTURE_DIR, 'related_tags_cosine.html'), 'r', encoding='utf-8') as f:
        return f.read()

@pytest.fixture
def related_tags_jaccard_html():
    """related_tags_jaccard.htmlのコンテンツを読み込むpytestフィクスチャ"""
    with open(os.path.join(FIXTURE_DIR, 'related_tags_jaccard.html'), 'r', encoding='utf-8') as f:
        return f.read()

def test_parse_related_tags_cosine(related_tags_cosine_html):
    """
    related_tags_cosine.htmlを正しくパースできるかテストする。
    """
    parser = DanbooruRelatedTagParser(related_tags_cosine_html)
    data = parser.parse(limit=5) # 上位5件をテスト

    assert len(data) == 5
    
    # 最初の行 (lying) のデータを確認
    first_row = data[0]
    assert first_row['tag'] == 'lying'
    assert first_row['post_count'] == 486973
    assert first_row['cosine'] == 100.00
    assert first_row['jaccard'] == 100.00
    assert first_row['overlap'] == 100.00
    assert first_row['frequency'] == 100.00

    # 2番目の行 (on_back) のデータを確認
    second_row = data[1]
    assert second_row['tag'] == 'on_back'
    assert second_row['post_count'] == 276839
    assert second_row['cosine'] == 74.83
    assert second_row['jaccard'] == 56.18
    assert second_row['overlap'] == 99.25
    assert second_row['frequency'] == 56.42

    # 5番目の行 (pillow) のデータを確認
    fifth_row = data[4]
    assert fifth_row['tag'] == 'pillow'
    assert fifth_row['post_count'] == 159778
    assert fifth_row['cosine'] == 27.93
    assert fifth_row['jaccard'] == 13.70
    assert fifth_row['overlap'] == 48.76
    assert fifth_row['frequency'] == 16.00

def test_parse_post_count_with_m(related_tags_cosine_html):
    """
    ポスト数が 'M' (百万) を含む場合に正しくパースできるかテストする。
    """
    parser = DanbooruRelatedTagParser(related_tags_cosine_html)
    data = parser.parse() # 全件パース

    breasts_tag = next((item for item in data if item["tag"] == "breasts"), None)
    assert breasts_tag is not None
    assert breasts_tag['post_count'] == 3778621

def test_parse_empty_html():
    """
    空のHTML文字列を渡した場合に、エラーなく空のリストを返すかテストする。
    """
    parser = DanbooruRelatedTagParser("")
    data = parser.parse()
    assert data == []

def test_table_not_found():
    """
    テーブルが存在しないHTMLを渡した場合に、エラーなく空のリストを返すかテストする。
    """
    invalid_html = "<html><body><h1>No table here</h1></body></html>"
    parser = DanbooruRelatedTagParser(invalid_html)
    data = parser.parse()
    assert data == []