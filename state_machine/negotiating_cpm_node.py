from typing import Literal
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from logger.logging_tool import logger
from state_machine.user_state import UserState
from utils.create_llm import llm


class DealAgreement(BaseModel):
    agreed: bool = Field(...,
                         description="Готовность блогера работать с cpm")


class CpmReaction(BaseModel):
    reaction: Literal["price_ok", "cpm_low", "reject_cpm", "enlarge_cap"] = Field(
        ...,
        description="Мнение блогера сmp"
    )


prompt_deal_agreement = """
Текст объявления:
{last_message}

Извлеки следующие данные из текста:
        - Ответ: "True", если блогер согласен работать или если он согласен, но имеет замечания по цене.
        - Ответь "False" в следующих случаях:
            - Если блогер не согласен работать.
            - Если блогер не готов работать по модели CPM.

Ответ ДОЛЖЕН быть строго в формате JSON:
{{
    "agreed": true | false
}}

Пример правильного ответа:
{{
    "agreed": false
}}

"""

prompt_cpm_reaction = """
Текст объявления:
{last_message}

Извлеки следующие данные из текста:
        - Ответ: 
            - "price_ok", если блогер согласен с предложенной ценой.
            - "cpm_low", если блогер не согласен с предложенной ставкой CPM (ставка слишком маленькая для него).
            - "enlarge_cap", если блогер хочет увеличить cap.

Ответ ДОЛЖЕН быть строго в формате JSON: 
{{
    "reaction": "price_ok" | "cpm_low" | "reject_cpm" | "enlarge_cap"
}}

Пример правильного ответа:
{{
    "reaction": "cpm_low"
}}

"""


async def negotiating_cpm(state: UserState):
    logger.info("Starting negotiating CPM")
    last_message = state.messages[-1]
    logger.info(f"Last message in negotiating_cpm: {last_message}")

    prompt_deal = PromptTemplate(input_variables=["last_message"], template=prompt_deal_agreement)
    structured_llm = llm.with_structured_output(DealAgreement)
    chain_deal = prompt_deal | structured_llm
    result = await chain_deal.ainvoke({"last_message": last_message})

    logger.info(f"Result neg_cpm {result}, {result.agreed}")

    if not result.agreed:
        state.deal_type = 'fix'
        if state.cpm_discount is not None:
            logger.info(f"CPM {state.cpm_discount} , {state.cpm}")
            state.cpm /= state.cpm_discount
            state.cpm_discount = None
        state.price= await state.get_min_price()
        await state.add_message(
                f"Можем предложить фиксированую сделку,{state.price}")
        return state
    else:
        prompt_opinion = PromptTemplate(input_variables=["last_message"], template=prompt_cpm_reaction)
        structured_llm = llm.with_structured_output(CpmReaction)
        chain_deal = prompt_opinion | structured_llm
        result = await chain_deal.ainvoke({"last_message": last_message})
        logger.info(f"Реакция на cpm: {result}")

        if result.reaction == "price_ok":
            state.solution = "accepted"
            await state.add_message("Сделка заключена")
        elif result.reaction == "cpm_low":
            state.cpm_discount = 1.15
            state.cpm *= state.cpm_discount
            await state.add_message(f"Предлагаю повышение cpm на 15 процентов {state.cpm}, cap {state.price}")
        elif result.reaction == "enlarge_cap":
            if state.cap_discount is not None:
                await state.add_message("Мы не можем предложить cap больше")
                return state
            state.cap_discount = 1.3
            state.price *= 1.3
            await state.add_message(f"Увеличиваю cap до {state.price}")
        return state
