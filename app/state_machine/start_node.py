from app.logger.logging_tool import logger
from app.state_machine.user_state import UserState


async def start(state: UserState):
    logger.info("[start] Starting the start node.")
    try:
        await state.add_message(
            "Tell me about advertising: CPM, viewer range (for example, 100-300) and fixed rate ($), if relevant. Thank you!")
        logger.info("[start] Message added successfully to state.")
    except Exception as e:
        logger.error(f"[start] Failed to add message: {e}")
    return state
