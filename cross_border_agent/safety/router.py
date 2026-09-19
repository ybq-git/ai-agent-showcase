# 这是我们的"工具库"——所有能调的东西都在这
def tool_search_products(keyword: str) -> str:
    """搜商品。"""
    return f"搜到了 {keyword} 的商品"

def tool_generate_listing(asin: str) -> str:
    """生成 Listing。"""
    return f"为 {asin} 生成了 Listing"

def tool_publish_listing(asin: str) -> str:
    """【写操作】上架到店铺。"""
    return f"已上架 {asin}"

def tool_change_price(asin: str, price: float) -> str:
    """【写操作】改价。"""
    return f"已将 {asin} 价格改为 {price}"

ALL_TOOLS = {
    "search_products": tool_search_products,
    "generate_listing": tool_generate_listing,
    "publish_listing": tool_publish_listing,
    "change_price": tool_change_price,
}
def plan(intent: str) -> list[str]:
    """意图 → 工具白名单。写死在代码里，模型只能在白名单里选。"""
    if intent == "research":
        return ["search_products"]
    if intent == "listing":
        return ["search_products", "generate_listing"]   # 只能搜和生成，不能上架！
    return []   # 未知意图，不给任何工具
def guard_tools(intent: str) -> dict:
    """物理裁剪：只把白名单里的工具交给模型，白名单外模型看都看不到。"""
    allowed = plan(intent)
    return {name: fn for name, fn in ALL_TOOLS.items() if name in allowed}
