from abc import ABCMeta, abstractmethod
import requests
from dInfoImporter.model import Doujinshi

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
