from typing import Annotated, Literal, Optional, List

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph import add_messages
from pydantic import BaseModel

from logger.logging_tool import logger


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
    cap_discount : Optional[float]=None

    async def get_min_price(self):
        return float(self.cpm * self.viewers_range[0]) / 1000

    async def get_standard_price(self):
        return (self.cpm * (((self.viewers_range[0] + self.viewers_range[-1]) / 2) + self.viewers_range[-1]) / 2) / 1000

    async def add_message(self, text: str):
        self.messages.append(text)
        logger.info(f"Added message to context: {text}")
        logger.info(f"Now message context: {list(self.messages)}")
        return self

    def initializate_state(self):
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
            "cap_discount" :None
        }
