from typing import Any, Dict

import httpx
from loguru import logger

from app.core.config import settings


class GhanaCardService:
    def __init__(self):
        self.base_url = settings.GHANA_CARD_BASE_URL
        self.api_key = settings.GHANA_CARD_API_KEY

    async def verify_card(
        self, ghana_card_number: str, surname: str, first_names: str
    ) -> Dict[str, Any]:
        """Verify Ghana Card with NIA"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/verify",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "card_number": ghana_card_number,
                        "surname": surname,
                        "first_names": first_names,
                    },
                    timeout=30.0,
                )

                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Ghana Card verification failed: {e}")
            return {"status": "error", "message": str(e)}
