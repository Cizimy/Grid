import pytest
import os
from scripts.parsers.wiki_page_parser import DanbooruWikiPageParser

# プロジェクトのルートディレクトリを基準にフィクスチャのパスを解決
# このテストファイルは `tests/parsers/` にあるため、2階層上がる
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')

@pytest.fixture
def lying_html_content():
    """lying.htmlのコンテンツを読み込むpytestフィクスチャ"""
    with open(os.path.join(FIXTURE_DIR, 'lying.html'), 'r', encoding='utf-8') as f:
        return f.read()

@pytest.fixture
def leg_up_html_content():
    """leg_up.htmlのコンテンツを読み込むpytestフィクスチャ"""
    with open(os.path.join(FIXTURE_DIR, 'leg_up.html'), 'r', encoding='utf-8') as f:
        return f.read()

def test_parse_lying_page(lying_html_content):
    """
    lying.htmlを正しくパースできるかテストする。
    エイリアスと含意の両方が存在する場合。
    """
    parser = DanbooruWikiPageParser(lying_html_content)
    data = parser.parse()

    assert data['tag_name'] == 'lying'
    assert data['wiki_description'] == 'Lying down flat on a surface, mainly being supported by the back, side or the stomach.'
    assert data['aliases'] == ['laying', 'laying_down', 'lying_down']
    assert data['implicates_this_tag'] == ['on_back', 'on_side', 'on_stomach']
    assert data['see_also'] == [
        'lying on person',
        'on back',
        'on side',
        'on stomach',
        'reclining',
        'Tag Group:Posture'
    ]

def test_parse_leg_up_page(leg_up_html_content):
    """
    leg_up.htmlを正しくパースできるかテストする。
    含意(implicates)が存在しない場合。
    """
    parser = DanbooruWikiPageParser(leg_up_html_content)
    data = parser.parse()

    assert data['tag_name'] == 'leg up'
    assert data['wiki_description'] == 'Any position where a single leg is lifted into the air.'
    assert data['aliases'] == ['one_leg_raised']
    assert data['implicates_this_tag'] == []  # このケースでは空リストが返されるべき
    assert data['see_also'] == [
        'arm up',
        'leg lift',
        'legs up',
        'standing on one leg',
        'stepping'
    ]

def test_parse_empty_html():
    """
    空のHTML文字列を渡した場合に、エラーなく安全な値を返すかテストする。
    """
    parser = DanbooruWikiPageParser("")
    data = parser.parse()

    assert data['tag_name'] is None
    assert data['wiki_description'] is None
    assert data['aliases'] == []
    assert data['implicates_this_tag'] == []
    assert data['see_also'] == []

def test_parse_invalid_html():
    """
    構造が全く異なるHTMLを渡した場合に、エラーなく安全な値を返すかテストする。
    """
    invalid_html = "<html><body><h1>Just a title</h1><p>Some text.</p></body></html>"
    parser = DanbooruWikiPageParser(invalid_html)
    data = parser.parse()

    assert data['tag_name'] is None
    assert data['wiki_description'] is None # 厳密なセレクタのため、この構造ではNoneが返るのが正しい
    assert data['aliases'] == []
    assert data['implicates_this_tag'] == []
    assert data['see_also'] == []