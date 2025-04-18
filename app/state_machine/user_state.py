from typing import Literal, Optional, List
from pydantic import BaseModel
from app.logger.logging_tool import logger


class UserState(BaseModel):
    messages: List[str] = []
    viewers_range: Optional[List[int]] = None
    blogger_offer: Optional[float] = None
    price: Optional[float] = None
    deal_type: Optional[Literal['fix', 'cpm']] = None
    cpm: Optional[float] = None
    cpm_discount: Optional[float] = None
    fixprice: Optional[float] = None
    solution: Optional[Literal["accepted", "rejected", "negotiating"]] = None
    discount: Optional[Literal[20, 30]] = None
    cap_discount: Optional[float] = None

    def _log_prefix(self) -> str:
        """Generates a prefix for logs to make it easy to find context."""
        return f"[UserState]"

    async def get_min_price(self):
        if self.cpm is None or not self.viewers_range:
            logger.warning(f"{self._log_prefix()} Cannot calculate min price, CPM or viewers_range is missing.")
            return None
        min_price = float(self.cpm * self.viewers_range[0]) / 1000
        logger.debug(f"{self._log_prefix()} Min price calculated: {min_price}")
        return min_price

    async def get_standard_price(self):
        if self.cpm is None or not self.viewers_range:
            logger.warning(f"{self._log_prefix()} Cannot calculate standard price, CPM or viewers_range is missing.")
            return None
        avg = (((self.viewers_range[0] + self.viewers_range[-1]) / 2) + self.viewers_range[-1]) / 2
        standard_price = (self.cpm * avg) / 1000
        logger.debug(f"{self._log_prefix()} Standard price calculated: {standard_price}")
        return standard_price

    async def add_message(self, text: str):
        self.messages.append(text)
        logger.info(f"{self._log_prefix()} Message added: \"{text}\" | Total messages: {len(self.messages)}")
        return self

    def initializate_state(self):
        logger.info(f"{self._log_prefix()} State initialized to defaults.")
        return {
            "messages": [],
            "viewers_range": None,
            "blogger_offer": None,
            "price": None,
            "deal_type": None,
            "cpm": None,
            "cpm_discount": None,
            "fixprice": None,
            "solution": None,
            "discount": None,
            "cap_discount": None
        }
