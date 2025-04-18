from typing import Literal
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from app.logger.logging_tool import logger
from app.state_machine.user_state import UserState
from app.utils.create_llm import llm


class DealAgreement(BaseModel):
    agreed: bool = Field(...,
                         description="Whether the blogger agrees to work with CPM")


class CpmReaction(BaseModel):
    reaction: Literal["price_ok", "cpm_low", "reject_cpm", "enlarge_cap"] = Field(
        ...,
        description="The blogger's opinion on CPM"
    )


prompt_deal_agreement = """
Text of the ad:
{last_message}

Extract the following data from the text:
        - Response: "True", if the blogger agrees to work or agrees but has concerns about the price.
        - Respond "False" in the following cases:
            - If the blogger does not agree to work.
            - If the blogger is not willing to work with CPM.

The answer MUST be strictly in JSON format:
{{
    "agreed": true | false
}}

Example of a correct answer:
{{
    "agreed": false
}}
"""

prompt_cpm_reaction = """
Text of the ad:
{last_message}

Extract the following data from the text:
        - Response: 
            - "price_ok", if the blogger agrees with the proposed price.
            - "cpm_low", if the blogger does not agree with the proposed CPM rate (it's too low for them).
            - "enlarge_cap", if the blogger wants to increase the cap.

The answer MUST be strictly in JSON format: 
{{
    "reaction": "price_ok" | "cpm_low" | "reject_cpm" | "enlarge_cap"
}}

Example of a correct answer:
{{
    "reaction": "cpm_low"
}}
"""


async def negotiating_cpm(state: UserState):
    logger.info("[NEGOTIATING_CPM] Starting negotiating CPM")

    last_message = state.messages[-1]
    logger.info(f"[NEGOTIATING_CPM] Last message in negotiating_cpm: {last_message}")

    prompt_deal = PromptTemplate(input_variables=["last_message"], template=prompt_deal_agreement)
    structured_llm = llm.with_structured_output(DealAgreement)
    chain_deal = prompt_deal | structured_llm

    try:
        result = await chain_deal.ainvoke({"last_message": last_message})
        logger.info(f"[NEGOTIATING_CPM] Result of AI in negotiating_cpm: {result}, {result.agreed}")

        if not result.agreed:
            state.deal_type = 'fix'
            if state.cpm_discount is not None:
                logger.info(f"[NEGOTIATING_CPM] CPM {state.cpm_discount} , {state.cpm}")
                state.cpm /= state.cpm_discount
                state.cpm_discount = None
            state.price = await state.get_min_price()
            await state.add_message(
                f"Can offer a fixed deal, {state.price}")
            return state
        else:
            prompt_opinion = PromptTemplate(input_variables=["last_message"], template=prompt_cpm_reaction)
            structured_llm = llm.with_structured_output(CpmReaction)
            chain_deal = prompt_opinion | structured_llm

            result = await chain_deal.ainvoke({"last_message": last_message})
            logger.info(f"[NEGOTIATING_CPM] Blogger reaction to CPM: {result}")

            if result.reaction == "price_ok":
                state.solution = "accepted"
                await state.add_message("Deal confirmed")
            elif result.reaction == "cpm_low":
                if state.cpm_discount == 1.15:
                    await state.add_message(
                        "The client cannot increase the CPM price further. Are you willing to accept this deal?")
                    return state
                state.cpm_discount = 1.15
                state.cpm *= state.cpm_discount
                await state.add_message(f"Offering a 15% increase in CPM: {state.cpm}, cap {state.price}")
            elif result.reaction == "enlarge_cap":
                if state.cap_discount is not None:
                    await state.add_message("We cannot offer a higher cap. Are you willing to cooperate at this price?")
                    return state
                state.cap_discount = 1.3
                state.price *= 1.3
                await state.add_message(f"Increasing cap to {state.price}")

        return state

    except Exception as e:
        logger.error(f"[NEGOTIATING_CPM] Error during negotiating process: {e}")
        return state
