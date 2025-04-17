from typing import Optional, List
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from logger.logging_tool import logger
from state_machine.user_state import UserState
from utils.create_llm import llm


class ExtractedData(BaseModel):
    """Извлеченные данные из рекламного текста."""
    cpm: float = Field(description="Цена за 1000 просмотров (CPM) в долларах (только число)")
    viewers_range: Optional[List[int]] = Field(
        description="Количество просмотров (только число или два числа через дефис). Пример 100-300,записывать [100,300]")
    fixprice: Optional[float] = Field(default=None,
                                      description="Фиксированная ставка в долларах (только число), которую хочет отдать клиент за рекламу")

prompt_extracted_data=""""Текст объявления:
{last_message}

Извлеки следующие данные из текста:
        - Цена за 1000 просмотров (CPM) в долларах (только число) если не в долларах, то посмотри по нынешнему курсу нац. банка
        - Количество просмотров (только число или два числа через дефис)
        - Если есть фиксированная ставка в долларах (только число) которую хочет отдать клиент за рекламу, то выгрузи и ее
        Ответ ДОЛЖЕН быть строго в формате JSON:
        {{
            "cpm": число,
            "viewers_range": [число] | [число, число]
            "fixprice": число | null
        }}

        Пример правильного ответа:
        {{"cpm": 100, "viewers_range": [120000], "fixprice": 500}}
"""
async def rate(state: UserState):
    last_message = state.messages[-1]
    logger.info(f"last_message: {last_message}")
    last_message = state.messages[-1]
    prompt_deal = PromptTemplate(input_variables=["last_message"], template=prompt_extracted_data)
    structured_llm = llm.with_structured_output(ExtractedData)
    chain_deal = prompt_deal | structured_llm
    result = await chain_deal.ainvoke({"last_message": last_message})
    logger.info(f"Result of structured output: {result}")
    try:
        state.cpm = result.cpm
        state.viewers_range = result.viewers_range if isinstance(result.viewers_range, list) else [state.viewers_range]
        state.fixprice = result.fixprice
        await state.add_message(
            """Могли бы вы, пожалуйста, указать стоимость рекламной интеграции, а также предпочтительный формат сделки — фиксированная оплата или CPM?""")
        logger.debug(f"State in rate node: {state}")
        return state
    except Exception as e:
        logger.error("Error in rate node: {}".format(e))



