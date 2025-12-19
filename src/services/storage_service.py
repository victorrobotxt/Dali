import os
import httpx
from typing import List

class StorageService:
    """Handles archival of listing images to prevent data loss when ads disappear."""
    def __init__(self, upload_dir="storage/archive"):
        self.upload_dir = upload_dir
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)

    async def archive_images(self, listing_id: int, urls: List[str]) -> List[str]:
        archived_paths = []
        async with httpx.AsyncClient() as client:
            for i, url in enumerate(urls):
                try:
                    resp = await client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        filename = f"listing_{listing_id}_{i}.jpg"
                        path = os.path.join(self.upload_dir, filename)
                        with open(path, "wb") as f:
                            f.write(resp.content)
                        archived_paths.append(path)
                except Exception as e:
                    print(f"Archive fail: {e}")
        return archived_paths
