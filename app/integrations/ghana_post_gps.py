from typing import Any, Dict, Optional

import httpx
from loguru import logger

from app.core.config import settings


class GhanaPostGPSService:
    def __init__(self):
        self.base_url = settings.GHANA_POST_GPS_BASE_URL

    async def get_location(self, gps_code: str) -> Optional[Dict[str, Any]]:
        """Get location details from Ghana Post GPS code"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/get-location", params={"address": gps_code}, timeout=10.0
                )

                response.raise_for_status()
                data = response.json()

                if data.get("found"):
                    return {
                        "latitude": data["data"]["Table"][0]["CenterLatitude"],
                        "longitude": data["data"]["Table"][0]["CenterLongitude"],
                        "area": data["data"]["Table"][0]["Area"],
                        "region": data["data"]["Table"][0]["Region"],
                        "district": data["data"]["Table"][0]["District"],
                    }

                return None

        except httpx.HTTPError as e:
            logger.error(f"Ghana Post GPS lookup failed: {e}")
            return None
