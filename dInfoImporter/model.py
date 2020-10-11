from dataclasses import dataclass, field


@dataclass()
class Doujinshi:
    name: str = ''
    romanized_title: str = ''
    date_released: str = ''
    circle_name: str = ''
    artist_name: str = ''
    series_names: list = field(default_factory=list)
    size: str = ''
    pages: int = 0
    price: int = 0
    convention_name: str = ''
    is_adult: bool = False
    is_anthology: bool = False
    is_copybook: bool = False
    is_novel: bool = False
    source_site: str = ''
    source_url: str = ''
    cover_url: str = ''
    sample_urls: list = field(default_factory=list)
    cover_image: bytes = field(default_factory=bytes)
    sample_images: list = field(default_factory=list)

