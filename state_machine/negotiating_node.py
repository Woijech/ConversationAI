from typing import Optional, Literal

from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from logger.logging_tool import logger
from state_machine.user_state import UserState
from utils.create_llm import llm


class BloggerResponse(BaseModel):
    deal_type: Optional[Literal['fix', 'cpm']] = Field(default=None,
                                                       description="Вид сделки, по которой готов работать блогер.")
    price: Optional[float] = Field(default=None, description="Цена, предложенная блогером, в долларах США")
    solution: Literal["rejected", None] = Field(default=None,
                                                description='"rejected" если блогер не хочет общаться, иначе None')


prompt_blogger_response = """
Текст объявления:
{last_message}

Извлеки следующие данные из текста:
        - Тип сделки: "fix" или "cpm", если блогер согласен работать по этим условиям, или оставь пустым, если нет.
        - Цена в долларах (только число), если блогер указывает цену за свои услуги.
        - Решение: "rejected", если блогер не согласен работать или не хочет продолжать переговоры, или оставь пустым, если блогер готов продолжить общение.

Ответ ДОЛЖЕН быть строго в формате JSON:
{{
    "deal_type": "fix" | "cpm" | null,
    "price": число | null,
    "solution": "rejected" | null
}}

Пример правильного ответа:
{{
    "deal_type": "cpm",
    "price": 300,
    "solution": null
}}

"""


async def negotiating(state: UserState):
    logger.info(f"State in negotiating: {state}")
    last_message = state.messages[-1]
    logger.info(f"Last message in negotiating: {last_message}")
    prompt_deal = PromptTemplate(input_variables=["last_message"], template=prompt_blogger_response)
    structured_llm = llm.with_structured_output(BloggerResponse)
    chain_deal = prompt_deal | structured_llm
    result = await chain_deal.ainvoke({"last_message": last_message})
    logger.info(f"Result of AI response in negotiating {result},{result.solution}")

    if result.solution == "rejected":
        state.solution = "rejected"
        await state.add_message(
            """Поделитесь, пожалуйста, вашими бюджетными ожиданиями — я уточню у клиента возможность выделения дополнительных средств на рекламу""")
        logger.info(state)

        return state
    blogger_offer = result.price
    state.deal_type = result.deal_type
    if blogger_offer:
        state.blogger_offer = blogger_offer
        logger.info(f"Blogger offer on negotiation node: {blogger_offer}")
    if not state.fixprice:
        state.fixprice = await state.get_standard_price()
    client_price = state.fixprice
    state.price = await state.get_min_price()
    logger.info(f"Standard price: {client_price}, minimal_price: {state.price}")
    if not blogger_offer and not state.blogger_offer:
        state.blogger_offer = client_price
    if state.blogger_offer < state.price:
        state.price = state.blogger_offer
        state.solution = "accepted"
        state.deal_type = "fix"
        await state.add_message("Мы согласны на эту сделку")
    else:
        state.solution = "negotiating"
        if state.deal_type == "fix":
            state.price = client_price
            await state.add_message(
                f"Мы предлагаем рассмотреть альтернативный вариант сотрудничества с оплатой за 1000 просмотров (CPM). Текущая ставка: {state.cpm}, общая стоимость: {state.price}. Просим сообщить о вашей заинтересованности и, если предложение актуально, обозначить ваши предпочтения по CPM-ставке")
        else:
            state.price = await state.get_standard_price()
            state.deal_type = "cpm"
            await state.add_message(
                f" сотрудничества с оплатой за 1000 просмотров (CPM). Текущая ставка: {state.cpm}, общая стоимость: {state.price}. Просим сообщить о вашей заинтересованности и, если предложение актуально, обозначить ваши предпочтения по CPM-ставке")

    return state
