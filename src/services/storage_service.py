import os
import httpx
import asyncio
from typing import List

class StorageService:
    def __init__(self, upload_dir="storage/archive"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    async def _download_single(self, client: httpx.AsyncClient, url: str, filename: str) -> str:
        try:
            resp = await client.get(url, timeout=7.0)
            if resp.status_code == 200:
                path = os.path.join(self.upload_dir, filename)
                with open(path, "wb") as f:
                    f.write(resp.content)
                return path
        except Exception as e:
            print(f"Archive Fail: {url} -> {e}")
        return None

    async def archive_images(self, listing_id: int, urls: List[str]) -> List[str]:
        if not urls: return []
        async with httpx.AsyncClient() as client:
            tasks = []
            for i, url in enumerate(urls):
                filename = f"listing_{listing_id}_{i}.jpg"
                tasks.append(self._download_single(client, url, filename))
            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]
