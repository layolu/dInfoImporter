from urllib.parse import parse_qs, urlparse
import re
from bs4 import BeautifulSoup as BeSo
from dInfoImporter.model import Doujinshi
from .site import Site


class Melonbooks(Site):
    def __init__(self) -> None:
        super().__init__('melonbooks')
        # set adult_view=1
        self.ses.get('https://www.melonbooks.co.jp/?&adult_view=1')

    RE_LINK_PATH = re.compile('^https://www.melonbooks.co.jp/search/search.php')

    def import_url(self, url: str) -> Doujinshi:
        d = Doujinshi()
        d.source_site = self.site_name
        d.source_url = url

        d.item_id = parse_qs(urlparse(d.source_url).query)['product_id'][0]

        res = self.ses.get(url)
        soup = BeSo(res.text, 'html.parser')

        d.name = soup.h1.text
        d.romanized_title = ''  # TODO: find nice romanization lib

        d.circle_name = soup.select_one('#title').find('a', class_='circle').text
        d.price = int(soup.find('td', class_='price').text.replace('¥','').replace(',',''))

        table = soup.select_one("#description")

        def td_extractor(s: str) -> str:
            return table.find('th', string=s).find_next_sibling('td')

        d.artist_names = [a.text.strip() for a in td_extractor('作家名').find_all('a', href=Melonbooks.RE_LINK_PATH)]
        d.series_names = [i.strip() for i in td_extractor('ジャンル').text.strip().split(',')]
        d.date_released = td_extractor('発行日').text.strip().replace('/', '-')
        d.size = td_extractor('版型・メディア').text.strip()
        d.pages = int(td_extractor('総ページ数・CG数・曲数').text.strip())
        td_convention = td_extractor('イベント')
        if td_convention is not None:
            d.convention_name = td_convention.text.strip()
        d.is_adult = td_extractor('作品種別').text.strip() == '18禁'

        # TODO: melonbooks also sells copybooks, but it seems hard to determine each book is it or not
        d.is_copybook = False

        # TODO: using melonbooks' general tags for other .info's tags?
        tags = soup.select_one('#related_tags').ul.find_all('li')
        d.general_tags = [li.text for li in tags]
        d.coupling_names = []
        d.character_names = []
        d.is_novel = '小説' in d.general_tags
        d.is_anthology = 'アンソロジー' in d.general_tags

        d.cover_url = 'https:' + soup.find('a', class_='tag_sample1')['href']
        d.cover_image = self.ses.get(d.cover_url).content

        div_thumbs = soup.select_one('#thumbs')
        if div_thumbs is not None:
            d.sample_urls = ['https:' + a['href'] for a in div_thumbs.ul.find_all('a')]
            d.sample_images = [self.ses.get(url).content for url in d.sample_urls]

        d.description = soup.select_one('#description').p.text.strip()

        return d
