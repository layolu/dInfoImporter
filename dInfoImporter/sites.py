from abc import ABCMeta, abstractmethod
import re
from bs4 import BeautifulSoup as BeSo
import jaconv
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


class Site(metaclass=ABCMeta):
    def __init__(self, site_name='') -> None:
        self.ses = requests.Session()
        self.site_name = site_name

    @abstractmethod
    def import_url(self, url: str) -> Doujinshi:
        pass


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

        res = self.ses.get(url)
        soup = BeSo(res.text, 'html.parser')

        d.name = soup.h1.text
        d.romanized_title = '' # TODO: find nice romanization lib

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
        d.convention_name = td_extractor('イベント').text.strip()
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
        return d


class Toranoana(Site):
    def __init__(self):
        super().__init__('toranoana')
        # NOTE: Toranoana's adult content pages can be inspected
        # without having to go through the adult verification page like melonbooks.

    RE_LINK_PATH = re.compile(r'^/tora_r/ec/app/catalog/list')

    def import_url(self, url: str) -> Doujinshi:
        d = Doujinshi()
        d.source_site = self.site_name
        d.source_url = url

        res = self.ses.get(url)
        soup = BeSo(res.text, 'html.parser')

        d.name = soup.h1.span.text

        d.circle_name = soup.find('div', class_='sub-circle').find('span', class_='sub-p').a.text.strip()
        d.artist_names = [a.text.strip() for a in soup.find('div', class_='sub-name').find_all('span', class_='sub-p')]
        
        d.is_adult = soup.find('span', class_='mk-rating') is not None
        # TODO: because the definition of 'anthology' is not clear in the site, set to False for the moment
        d.is_anthology = False

        d.price = int(soup.find('li', class_='pricearea__price').text.strip()
                      .replace('円 （＋税）','').replace(',', ''))

        table = soup.find('table', class_='detail4-spec')

        def td_extractor(s: str):
            try:
                header_td = table.find('td', string=s) or table.find('span', string=s).parent
                return header_td.find_next_sibling('td')
            except AttributeError:
                return None

        d.series_names = [a.span.text.strip() for a in
                          td_extractor('ジャンル/サブジャンル').find_all('a', href=Toranoana.RE_LINK_PATH)]

        td_coupling = td_extractor('カップリング')
        d.coupling_names = td_coupling.a.span.text.split('、') if td_coupling else []

        td_characters = td_extractor('メインキャラ')
        d.character_names = [a.span.text.strip() for a in
                             td_characters.find_all('a', href=Toranoana.RE_LINK_PATH)] if td_characters else []

        d.date_released = td_extractor('発行日').span.a.span.text.strip().replace('/', '-')

        td_type = td_extractor('種別/サイズ')
        if td_type is not None:
            type_list = td_type.text.replace('-', '').replace('/', '').split()
            d.is_copybook = type_list[0] == 'コピー誌'
            d.is_novel = type_list[1] == '小説'
            d.size = jaconv.z2h(type_list[2], ascii=True, digit=True)
            if len(type_list) == 4:
                d.pages = int(type_list[3].replace('p', '').replace(',', ''))

        image_urls = [img['data-src'] for img in soup.select_one('#thumbs').find_all('img')]
        d.cover_url = image_urls[0]
        d.sample_urls = image_urls[1:]
        d.cover_image = self.ses.get(d.cover_url).content
        d.sample_images = [self.ses.get(url).content for url in d.sample_urls]

        tags = soup.find('div', class_='tag')
        if tags is not None:
            # TODO: using toranoana's general tags for other .info's tags?
            d.general_tags = [a.span.text.strip() for a in
                              tags.find_all('a', href=Toranoana.RE_LINK_PATH)]

        td_conv = td_extractor('初出イベント')
        if td_conv is not None:
            d.convention_name = td_conv.a.span.text.split()[1].strip()

        return d
