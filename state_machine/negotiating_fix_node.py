from typing import Optional

from langchain.chains.llm import LLMChain
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from logger.logging_tool import logger
from state_machine.user_state import UserState
from utils.create_llm import llm


class DealAgreement(BaseModel):
    agreed: bool = Field(...,
                         description='Блогер согласен ли на текущую сделку')
    price : Optional[float] = Field(...,
                                    description="Блогер называет свою цену")


prompt_deal_agreement = """Текст объявления:
{last_message}

Извлеки следующие данные из текста:
        - Ответ: "True", если блогер согласен на текущие условия сделки или если он согласен, но без замечаний.
        - Ответь "False" в следующих случаях:
            - Если блогер считает предложенную сумму слишком низкой и предлагает другую.
            - Если блогер указывает минимальную цену, за которую он готов работать, например: "Я предлагаю 15 долларов", "Моя минимальная цена 10 долларов" и так далее.
            - Если блогер не согласен с условиями сделки и не готов принять предложение.

Ответ ДОЛЖЕН быть строго в формате JSON:
{{
    "agreed": true | false
}}

Пример правильного ответа:
{{
    "agreed": false
}}
"""


async def negotiating_fix(state: UserState):
    logger.info("Starting negotiating fix")
    last_message = state.messages[-1]
    logger.info(f"Last message in negotiating_fix: {last_message}")
    prompt_deal = PromptTemplate(input_variables=["last_message"], template=prompt_deal_agreement)
    structured_llm = llm.with_structured_output(DealAgreement)
    chain_deal = prompt_deal | structured_llm
    result = await chain_deal.ainvoke({"last_message": last_message})
    logger.info(f"Result of AI in negotiating fix {result}")
    if result.agreed:
        state.solution = "accepted"
        return state
    else:
        if not state.discount:
            if state.price <= state.blogger_offer < state.price * 1.2:
                state.solution = "accepted"
                state.price = state.blogger_offer
                await state.add_message(
                    f"Готовы согласиться с вашими условиями и утвердить сумму {state.blogger_offer}$ за интеграцию")
                return state
            logger.info("Поднимаем цену на 20 проц")
            state.discount = 20
            state.price = state.fixprice * 1.2
            await state.add_message(f"Готовы предложить на 20 процентов больше {state.price}")
        elif state.discount == 20:
            logger.info("Поднимаем цену на 30 проц")
            state.price = state.fixprice * 1.3
            if state.blogger_offer < state.price:
                logger.info(f"Согласны с сделкой {state.blogger_offer} и {state.price}")
                state.solution = "accepted"
                state.price = state.blogger_offer
                await state.add_message(
                    f"Готовы согласиться с вашими условиями и утвердить сумму {state.blogger_offer}$ за интеграцию")
                return state
            logger.info("Предлагаем на 30 проц больше")
            state.discount = 30
            await state.add_message(f"Предлагаю Вам на 30% больше от первоначальной суммы, {state.price}$")



        else:
            state.solution="rejected"
            await state.add_message("Поделитесь, пожалуйста, вашими бюджетными ожиданиями — я уточню у клиента возможность выделения дополнительных средств на рекламу")
    return state
