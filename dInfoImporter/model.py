from dataclasses import dataclass, field


@dataclass()
class Doujinshi:
    source_site: str = ''
    source_url: str = ''
    item_id: str = ''

    name: str = ''
    romanized_title: str = ''
    date_released: str = ''  # YYYY-MM-dd
    circle_name: str = ''
    artist_names: list = field(default_factory=list)

    is_adult: bool = False
    is_anthology: bool = False
    is_copybook: bool = False
    is_novel: bool = False

    cover_url: str = ''
    sample_urls: list = field(default_factory=list)
    cover_image: bytes = field(default_factory=bytes)
    sample_images: list = field(default_factory=list)

    size: str = ''  # melonbooks, toranoana
    pages: int = 0  # melonbooks, toranoana
    price: int = 0  # melonbooks, toranoana, booth
    convention_name: str = ''  # melonbooks, toranoana, booth

    general_tags: list = field(default_factory=list)  # melonbooks, toranoana, booth
    series_names: list = field(default_factory=list)  # melonbooks, toranoana
    character_names: list = field(default_factory=list)  # toranoana
    coupling_names: list = field(default_factory=list)  # toranoana

