from typing import Optional, List
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from app.logger.logging_tool import logger
from app.state_machine.user_state import UserState
from app.utils.create_llm import llm


class ExtractedData(BaseModel):
    cpm: float = Field(description="CPM price per 1000 views in dollars (only number)")
    viewers_range: Optional[List[int]] = Field(
        description="Number of views (either a single number or two numbers separated by a hyphen).")
    fixprice: Optional[float] = Field(default=None,
                                      description="Fixed price in dollars that the client wants to pay for the ad (only a number).")


prompt_extracted_data = """Text of the ad:
{last_message}

Extract the following data from the text:
        - CPM (cost per 1000 views) in dollars (just a number), if it's not in dollars, convert it based on the current national bank exchange rate
        - Number of views (either a single number or two numbers separated by a hyphen)
        - If a fixed price in dollars (just a number) that the client wants to pay for the ad is specified, extract it as well
        The answer MUST be strictly in JSON format:
        {{
            "cpm": number,
            "viewers_range": [number] | [number, number],
            "fixprice": number | null
        }}

        Examples of a correct answer:
        {{"cpm": 100, "viewers_range": [120,150], "fixprice": 500}}
        {{"cpm": 10, "viewers_range": [120], "fixprice": 50}}
"""


async def rate(state: UserState):
    last_message = state.messages[-1]
    logger.info(f"[RATE NODE] last_message: {last_message}")

    prompt_deal = PromptTemplate(input_variables=["last_message"], template=prompt_extracted_data)
    structured_llm = llm.with_structured_output(ExtractedData)
    chain_deal = prompt_deal | structured_llm

    try:
        result = await chain_deal.ainvoke({"last_message": last_message})
        logger.info(f"[RATE NODE] Result of structured output: {result}")

        state.cpm = result.cpm
        state.viewers_range = result.viewers_range if isinstance(result.viewers_range, list) else [state.viewers_range]
        state.fixprice = result.fixprice
        await state.add_message("Hey, please, provide your desired rate")

        logger.debug(f"[RATE NODE] State in rate node: {state}")
        return state
    except Exception as e:
        logger.error(f"[RATE NODE] Error in rate node: {e}")
