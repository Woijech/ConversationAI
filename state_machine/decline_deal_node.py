from typing import Optional

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from logger.logging_tool import logger
from state_machine.user_state import UserState
from utils.create_llm import llm

class BloggerPrice(BaseModel):
    blogger_price: Optional[float] = Field(
        None, description="Сумма в долларах без знака $"
    )

async def decline_offer(state:UserState):
    last_message = state.messages[-1]
    logger.info(f"Last message in decline_offer: {last_message}")
    structured_llm = llm.with_structured_output(BloggerPrice)
    result = await structured_llm.ainvoke(last_message)
    state.blogger_offer = result.blogger_price
    await state.add_message((
        f"Решение: {state.solution}. Цена от блогера: {state.blogger_offer}. Последний наш прайc: {state.price}. Причина отказа - не сошлись в цене."))
    return state