from app.state_machine.user_state import UserState
from app.logger.logging_tool import logger


async def accept(state: UserState):
    logger.info("[ACCEPT] Starting accept function")

    state.blogger_offer = state.price
    logger.info(
        f"[ACCEPT] Final offer from blogger: {state.blogger_offer}, deal type: {state.deal_type}, price: {state.price}")

    await state.add_message(f"Decision: {state.solution}. Final deal type: {state.deal_type}, Deal cost: {state.price}")

    logger.info("[ACCEPT] Deal successfully accepted")
    return state
