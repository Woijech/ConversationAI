from langchain_core.messages import AIMessage

from state_machine.user_state import UserState


async def accept(state: UserState):
    state.blogger_offer = state.price
    await state.add_message(f"Решение: {state.solution}. Итоговый формат сделки: {state.deal_type}, Стоимость сделки: {state.price}")
    return state