from typing import Any, Dict

import httpx
from loguru import logger

from app.core.config import settings


class XDSDataService:
    def __init__(self):
        self.base_url = settings.XDS_DATA_BASE_URL
        self.api_key = settings.XDS_DATA_API_KEY

    async def get_credit_report(
        self, surname: str, first_names: str, ghana_card_number: str
    ) -> Dict[str, Any]:
        """Get credit report from XDS Data Ghana"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/credit-report",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "surname": surname,
                        "first_names": first_names,
                        "id_number": ghana_card_number,
                    },
                    timeout=30.0,
                )

                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Credit check failed: {e}")
            return {"status": "error", "message": str(e)}
