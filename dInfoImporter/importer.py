from abc import ABCMeta, abstractmethod
from bs4 import BeautifulSoup as BS
import requests
from .model import Doujinshi

# cf. https://stackoverflow.com/questions/38015537/python-requests-exceptions-sslerror-dh-key-too-small
requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass


class Shop(metaclass=ABCMeta):
    def __init__(self, site_name='') -> None:
        self.ses = requests.Session()
        self.site_name = site_name

    @abstractmethod
    def import_url(self, url: str) -> Doujinshi:
        pass


class Melonbooks(Shop):
    def __init__(self) -> None:
        super().__init__('melonbooks')
        # set adult_view=1
        self.ses.get('https://www.melonbooks.co.jp/?&adult_view=1')

    def import_url(self, url: str) -> Doujinshi:
        d = Doujinshi()
        d.source_site = self.site_name
        d.source_url = url

        res = self.ses.get(url)
        soup = BS(res.text, 'html.parser')

        d.name = soup.h1.text
        d.romanized_title = '' # TODO: find nice romanization lib

        d.circle_name = soup.select_one('#title').find('a', class_='circle').text
        d.price = int(soup.find('td', class_='price').text.replace('¥','').replace(',',''))

        table = soup.select_one("#description")

        def td_extractor(s: str) -> str:
            return table.find('th', string=s).find_next_sibling('td').text.strip()

        d.artist_name = td_extractor('作家名').split('\n')[0].strip()
        d.series_names = [i.strip() for i in td_extractor('ジャンル').split(',')]
        d.date_released = td_extractor('発行日').replace('/', '-')
        d.size = td_extractor('版型・メディア')
        d.pages = int(td_extractor('総ページ数・CG数・曲数'))
        d.convention_name = td_extractor('イベント')
        d.is_adult = True if td_extractor('作品種別') == '18禁' else False

        # TODO: because the definition of 'anthology' is not clear in the site, set to False for the moment
        d.is_anthology = False
        # TODO: melonbooks also sells copybooks, but it's hard to determine each book is it or not
        d.is_copybook = False

        # TODO: using melonbooks' tags for other .info's tags?
        tags = soup.select_one('#related_tags').ul.find_all('li')
        tags_text = [li.text for li in tags]
        d.is_novel = True if '小説' in tags_text else False

        d.cover_url = 'https:' + soup.find('a', class_='tag_sample1')['href']
        d.sample_urls = ['https:' + a['href'] for a in soup.select_one('#thumbs').ul.find_all('a')]

        d.cover_image = self.ses.get(d.cover_url).content
        d.sample_images = [self.ses.get(url).content for url in d.sample_urls]
        return d
