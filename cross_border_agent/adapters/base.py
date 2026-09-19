from dataclasses import dataclass, field
@dataclass
class ProductListing:
    asin:str
    title:str
    brand:str
    price:float
    currency:str
    review_count:int
    rating:float
    image_urls:list[str]=field(default_factory=list)
    bullet_points:list[str]=field(default_factory=list)
    description:str=""

@dataclass
class ReviewItem:
    review_id: str
    asin: str
    rating: int
    title: str
    body: str
    author: str
    date: str
    verified_purchase: bool
    helpful_votes: int

from abc import ABC ,abstractmethod
class BasePlatformAdapter(ABC):
    @property
    @abstractmethod
    def platform_name(self)->str:
       ...
    @abstractmethod
    def search_products(self,keyword:str,limit:int = 20)->list[ProductListing]:

        ...
    @abstractmethod
    def get_best_sellers(self, category:str, limit:int = 20)->list[ProductListing]:

        ...
    