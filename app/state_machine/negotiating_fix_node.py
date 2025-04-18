from typing import Optional
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from app.logger.logging_tool import logger
from app.state_machine.user_state import UserState
from app.utils.create_llm import llm


class DealAgreement(BaseModel):
    agreed: bool = Field(...,
                         description='Whether the blogger agrees to the current deal')
    price: Optional[float] = Field(...,
                                   description="The price the blogger proposes")


prompt_deal_agreement = """Text of the ad:
{last_message}

Extract the following data from the text:
        - Response: "True", if the blogger agrees to the current terms of the deal or agrees but without any objections.
        - Respond "False" in the following cases:
            - If the blogger thinks the proposed amount is too low and offers another amount.
            - If the blogger states the minimum price they are willing to work for, e.g., "I offer 15 dollars", "My minimum price is 10 dollars", and so on.
            - If the blogger disagrees with the terms of the deal and is not willing to accept the offer.

The answer MUST be strictly in JSON format:
{{
    "agreed": true | false
}}

Example of a correct answer:
{{
    "agreed": false
}}
"""


async def negotiating_fix(state: UserState):
    logger.info("[NEGOTIATING_FIX] Starting negotiating fix")

    last_message = state.messages[-1]
    logger.info(f"[NEGOTIATING_FIX] Last message in negotiating_fix: {last_message}")

    prompt_deal = PromptTemplate(input_variables=["last_message"], template=prompt_deal_agreement)
    structured_llm = llm.with_structured_output(DealAgreement)
    chain_deal = prompt_deal | structured_llm

    try:
        result = await chain_deal.ainvoke({"last_message": last_message})
        logger.info(f"[NEGOTIATING_FIX] Result of AI in negotiating fix: {result}")

        if result.agreed:
            state.solution = "accepted"
            return state
        else:
            if not state.discount:
                if state.price <= state.blogger_offer < state.price * 1.2:
                    state.solution = "accepted"
                    state.price = state.blogger_offer
                    await state.add_message(
                        f"Ready to agree with your terms and confirm the amount of {state.blogger_offer}$ for the integration")
                    return state

                logger.info("[NEGOTIATING_FIX] Raising the price by 20%")
                state.discount = 20
                state.price = state.fixprice * 1.2
                await state.add_message(f"Ready to offer 20% more: {state.price}$")

            elif state.discount == 20:
                logger.info("[NEGOTIATING_FIX] Raising the price by 30%")
                state.price = state.fixprice * 1.3
                if state.blogger_offer < state.price:
                    logger.info(f"[NEGOTIATING_FIX] Agreeing to the deal at {state.blogger_offer} and {state.price}")
                    state.solution = "accepted"
                    state.price = state.blogger_offer
                    await state.add_message(
                        f"Ready to agree with your terms and confirm the amount of {state.blogger_offer}$ for the integration")
                    return state

                logger.info("[NEGOTIATING_FIX] Offering 30% more")
                state.discount = 30
                await state.add_message(
                    f"Offering you 30% more than the initial amount. This is the maximum the client is willing to offer: {state.price}$")
            else:
                state.solution = "rejected"
                await state.add_message("Please provide the reason for rejecting the collaboration.")

    except Exception as e:
        logger.error(f"[NEGOTIATING_FIX] Error during negotiating process: {e}")

    return state
