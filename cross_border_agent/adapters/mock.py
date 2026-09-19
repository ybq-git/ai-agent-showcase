from adapters.base import ProductListing, BasePlatformAdapter

# 示例目录的品类：只有保温杯这一类。查别的品类就如实返回空，不拿保温杯冒充
CATALOG_CATEGORY = "保温杯"
CATEGORY_ALIASES = {"insulated water bottle", "water bottle", "bottle", "保温杯", "水杯", "水壶"}


class MockAmazonAdapter(BasePlatformAdapter):
    @property
    def platform_name(self)->str:
        return "mock-amazon"

    def _matches(self, query: str) -> bool:
        """示例目录只覆盖保温杯；别名命中才算匹配。"""
        q = (query or "").strip().lower()
        if not q:
            return True
        return q in CATEGORY_ALIASES or CATALOG_CATEGORY in q or q in CATALOG_CATEGORY

    def search_products(self,keyword:str,limit:int = 20)->list[ProductListing]:
        if not self._matches(keyword):
            return []
        return self._all_products()[:limit]

    def get_best_sellers(self, category: str, limit: int = 20) -> list[ProductListing]:
        if not self._matches(category):
            return []
        return self._all_products()[:limit]

    def _all_products(self)->list[ProductListing]:
        return [
            ProductListing(
                asin="B0WATER01",
                title="隔热不锈钢保温杯 500ml 真空防漏",
                brand="慕野",
                price=89,
                currency="USD",
                review_count=1284,
                rating=4.6,
                bullet_points=[
                    "500ml容量，双层真空保温",
                    "304不锈钢内胆，不含BPA的杯盖",
                    "螺旋防漏盖，带硅胶密封圈",
                    "保温12小时 / 保冷24小时",
                    "磨砂防滑外壳，可放入车载杯架",
                ],
                description="慕野500ml保温杯，双层真空设计，保温12小时、保冷24小时。食品级304不锈钢内胆搭配防漏杯盖，适合办公、通勤和日常饮水。",
            ),
            ProductListing(
                asin="B0WATER02",
                title="保温保冷两用健身运动水壶 1L",
                brand="RidgePace",
                price=69,
                currency="USD",
                review_count=872,
                rating=4.3,
                bullet_points=[
                    "1L大容量，双层真空保温",
                    "保温12小时 / 保冷24小时",
                    "304不锈钢内胆，不含BPA的杯盖",
                    "防漏翻盖设计，可放入车载杯架",
                    "可机洗，磨砂质感易握持",
                ],
                description="RidgePace 1L运动水壶，双层真空保温，保冷24小时、保温12小时。304不锈钢内胆搭配防漏翻盖，是健身房、徒步和办公场景的补水伴侣。",
            ),
            ProductListing(
                asin="B0WATER03",
                title="便携随行保温杯 咖啡杯 双层真空",
                brand="WarmGo",
                price=55,
                currency="USD",
                review_count=2051,
                rating=4.7,
                bullet_points=[
                    "350ml纤细杯身，双层真空",
                    "适配标准车载杯架",
                    "304不锈钢内胆，不含BPA",
                    "滑锁杯盖，可单手饮水",
                    "保温6小时 / 保冷12小时",
                ],
                description="WarmGo 350ml随行咖啡杯，纤细双层杯身适配任意杯架。滑锁杯盖支持单手开合，304不锈钢内胆让咖啡保温6小时、冰饮保冷12小时。",
            ),
            ProductListing(
                asin="B0WATER04",
                title="大容量保温壶 1.5L 户外露营保温杯",
                brand="Summit",
                price=119,
                currency="USD",
                review_count=633,
                rating=4.4,
                bullet_points=[
                    "1.5L大容量，适合户外出行",
                    "保温24小时 / 保冷48小时",
                    "粉末涂层钢材外壳，坚固耐用",
                    "广口设计，方便加冰块和清洗",
                    "附带提手和肩带",
                ],
                description="Summit 1.5L户外保温壶，专为露营和自驾设计。粉末涂层钢体保温24小时、保冷48小时，广口可加冰块，附带提手与肩带便于携带。",
            ),


        ]
