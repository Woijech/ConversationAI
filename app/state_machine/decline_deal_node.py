from typing import Optional
from pydantic import BaseModel, Field

from app.logger.logging_tool import logger
from app.state_machine.user_state import UserState
from app.utils.create_llm import llm


class BloggerPrice(BaseModel):
    blogger_price: Optional[float] = Field(
        None, description="Amount in dollars without the $ sign")
    why_delcine: Optional[str] = Field(None, description="Why blogger declined")


async def decline_offer(state: UserState):
    logger.info(f"[DECLINE_OFFER] Last message in decline_offer: {state.messages[-1]}")

    structured_llm = llm.with_structured_output(BloggerPrice)

    try:
        result = await structured_llm.ainvoke(state.messages[-1])
        logger.info(
            f"[DECLINE_OFFER] Blogger's offer: {result.blogger_price}, Reason for decline: {result.why_delcine}")

        state.blogger_offer = result.blogger_price

        await state.add_message((
            f"Decision: {state.solution}. Blogger's price: {state.blogger_offer}. Last our price: {state.price}. "
            f"Reason for decline: {result.why_delcine}."))

        logger.info(f"[DECLINE_OFFER] State updated with blogger's offer and decline reason.")

    except Exception as e:
        logger.error(f"[DECLINE_OFFER] Error processing the decline offer: {e}")

    return state
