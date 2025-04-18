from typing import Optional, Literal
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from app.logger.logging_tool import logger
from app.state_machine.user_state import UserState
from app.utils.create_llm import llm


class BloggerResponse(BaseModel):
    deal_type: Optional[Literal['fix', 'cpm']] = Field(default=None,
                                                       description="The type of deal the blogger is willing to work with.")
    price: Optional[float] = Field(default=None, description="Price proposed by the blogger in USD.")
    solution: Literal["rejected", None] = Field(default=None,
                                                description='"rejected" if the blogger is not interested or does not want to continue negotiations, else None.')


prompt_blogger_response = """
Text of the ad:
{last_message}

Extract the following data from the text:
        - Deal type: "fix" or "cpm", if the blogger agrees to work with these terms, or leave empty if not.
        - Price in dollars (just a number), if the blogger provides a price for their services.
        - Solution: "rejected", if the blogger refuses to work or does not want to continue negotiations, or leave empty if the blogger is willing to continue discussions.

The answer MUST be strictly in JSON format:
{{
    "deal_type": "fix" | "cpm" | null,
    "price": number | null,
    "solution": "rejected" | null
}}

Example of a correct answer:
{{
    "deal_type": "cpm",
    "price": 300,
    "solution": null
}}
"""


async def negotiating(state: UserState):
    logger.info("[NEGOTIATING] State in negotiating: {}".format(state))

    last_message = state.messages[-1]
    logger.info(f"[NEGOTIATING] Last message in negotiating: {last_message}")

    prompt_deal = PromptTemplate(input_variables=["last_message"], template=prompt_blogger_response)
    structured_llm = llm.with_structured_output(BloggerResponse)
    chain_deal = prompt_deal | structured_llm

    try:
        result = await chain_deal.ainvoke({"last_message": last_message})
        logger.info(f"[NEGOTIATING] Result of AI response in negotiating: {result}, solution: {result.solution}")

        if result.solution == "rejected":
            state.solution = "rejected"
            if state.blogger_offer:
                await state.add_message("Could you please share the reason for your rejection?")
                return state
            await state.add_message(
                """Please share your budget expectations — I'll check with the client if additional funds can be allocated for advertising.""")
            logger.info(f"[NEGOTIATING] State after rejection: {state}")
            return state

        blogger_offer = result.price
        state.deal_type = result.deal_type
        if blogger_offer:
            state.blogger_offer = blogger_offer
            logger.info(f"[NEGOTIATING] Blogger offer on negotiation node: {blogger_offer}")

        if not state.fixprice:
            state.fixprice = await state.get_standard_price()

        client_price = state.fixprice
        state.price = await state.get_min_price()
        logger.info(f"[NEGOTIATING] Standard price: {client_price}, minimal_price: {state.price}")

        if not blogger_offer and not state.blogger_offer:
            state.blogger_offer = client_price

        if state.blogger_offer < state.price:
            state.price = state.blogger_offer
            state.solution = "accepted"
            state.deal_type = "fix"
            await state.add_message("We accept this deal.")
        else:
            state.solution = "negotiating"
            if state.deal_type == "fix":
                state.price = client_price
                state.deal_type="cpm"
                await state.add_message(
                    f"We propose to consider an alternative collaboration with payment per 1000 views (CPM). It better aligns with the client's benchmarks. Current rate: {state.cpm}, total cost: {state.price}. Please let us know if you are interested and, if the offer is still relevant, provide your preferences for the CPM rate.")
            else:
                state.price = await state.get_standard_price()
                await state.add_message(
                    f"Collaboration with payment per 1000 views (CPM). Current rate: {state.cpm}, cap: {state.price}. Please let us know if you are interested and, if the offer is still relevant, provide your preferences for the CPM rate.")

        return state

    except Exception as e:
        logger.error(f"[NEGOTIATING] Error during negotiation process: {e}")
