from .base import BaseAgent
from ..graph.state import TravelState


class ImageSearchAgent(BaseAgent):
    name = "image"
    description = "搜索目的地相关图片"

    async def run(self, state: TravelState) -> dict:
        destination = state["destination"]
        attractions = state.get("attractions", [])

        urls = []
        for a in attractions[:6]:
            name = a.get("name", "")
            urls.append(f"https://picsum.photos/seed/{destination}-{name}/800/400")

        return {"image_urls": urls}
