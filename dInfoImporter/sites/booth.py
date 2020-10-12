import json
import re
from bs4 import BeautifulSoup as BeSo
from dInfoImporter.model import Doujinshi
import requests
from .site import Site


class Booth(Site):
    def __init__(self) -> None:
        super().__init__('boothpm')
        # set the adult cookie
        self.ses.cookies.set_cookie(
            requests.cookies.create_cookie(domain='booth.pm', name='adult', value='t'))

    RE_ITEM_URL_ROOT_DOMAIN = re.compile(r'https://booth\.pm/([^/]+)/items/(.+)$')
    RE_ITEM_URL_SUBDOMAIN = re.compile(r'https://([^.]+)\.booth\.pm/items/(.+)$')

    def import_url(self, url: str) -> Doujinshi:
        d = Doujinshi()
        d.source_site = self.site_name

        # There are two domain types of item page URLs on BOOTH;
        # Type 1: booth.pm root domain, format: https://booth.pm/{lang_code}/items/{item_id_num}
        #     this is the 'canonical' URL because <link rel="canonical"> announce it
        # Type 2: artists' subdomain, format: https://{artist_id?}.booth.pm/items/{item_id_num}
        # Currently doujinshi.info only accepts the Type 2 URLs as the correct value.
        # Therefore, if url is a Type 1, it must be converted to Type 2.
        match_root_domain = Booth.RE_ITEM_URL_ROOT_DOMAIN.match(url)
        match_subdomain = Booth.RE_ITEM_URL_SUBDOMAIN.match(url)
        if match_root_domain:
            d.item_id = match_root_domain.group(2)
            # get artists' root page URL
            soup2artist = BeSo(self.ses.get(url).text, 'html.parser')
            artists_root_url = soup2artist.find('div', class_='shop-items-owner-info').a['href']
            d.source_url = artists_root_url + 'items/' + d.item_id
        elif match_subdomain:
            d.item_id = match_subdomain.group(2)
            d.source_url = url
        else:
            pass  # TODO: raise some malformed url exception (we need to do the same for other sites)?

        res = self.ses.get(d.source_url)
        soup = BeSo(res.text, 'html.parser')

        # booth.pm enables to get some very basic data from json-ld in header
        # so firstly I tried to get some info from it,
        # but adult (R-18) item pages don't include json-ld tag...
        # json_ld = json.loads(soup.find('script', {'type': 'application/ld+json'}).string)
        # d.name = json_ld['name']
        # some pages also sells the special version of a book with extras, so choose lower price.
        # if json_ld['offers']['@type'] == 'AggregateOffer':
        #     d.price = json_ld['offers']['lowPrice']
        # else:
        #     d.price = json_ld['offers']['price']

        div_shop_head = soup.find('div', class_='shop-head')
        # Unlike other doujinshi online shopping sites, BOOTH is a personal online shopping service
        # for doujinshi authors, so we can get not the name of the circle but the name of the shop.
        # However, in many cases, the shop name and the circle name are the same,
        # so we treat it as a circle name for convenience.
        d.circle_name = div_shop_head.h1.text
        # also, we only get one name of the shop's owner (nickname), so treat it as a artist name.
        # some shops' pages have no owner's name.
        div_nickname = div_shop_head.find('div', class_='home-link-container__nickname')
        d.artist_names = [div_nickname.text] if div_nickname else []

        div_summary = soup.find('div', class_='summary')
        d.is_adult = div_summary.select_one('div.badge.adult') is not None
        div_event = div_summary.select_one('div.badge.event')
        d.convention_name = div_event.text if div_event else ''
        d.is_novel = div_summary.find('div', class_='category').text == '小説・ライトノベル'
        d.name = div_summary.h1.text
        # some pages also sells the special version of a book with extras, so choose the lowest price.
        prices = [int(div.text.replace('¥ ', '').replace(',', '')) for div in
                  div_summary.find_all('div', class_='variation-price')]
        d.price = min(prices)

        # surprisingly, I can't find any hints from source when it was released...
        d.date_released = ''

        # the values below are often written by the artist in the description by natural language,
        # but to get the right value, natural language processing would be required...
        d.size = ''
        d.pages = 0
        tags = soup.select_one('#tags').find_all('li')
        d.general_tags = [li.text for li in tags]
        d.coupling_names = []
        d.character_names = []
        d.is_anthology = 'アンソロジー' in d.general_tags
        # even if an artist tagged a book as a "コピー本" (copybook),
        # in some cases it's actually a collection of previous copybooks,
        # which is not actually a copybook. so it's hard to determine automatically.
        d.is_copybook = False

        res_images = self.ses.get(d.source_url + '/images')
        if res_images.ok:
            images = res_images.json()
            d.cover_url = images[0]['file']['url']
            d.cover_image = self.ses.get(d.cover_url).content
            if len(images) > 1:
                d.sample_urls = [i['file']['url'] for i in images[1:]]
                d.sample_images = [self.ses.get(url).content for url in d.sample_urls]

        d.description = div_summary.select_one('div.description').text
        return d
