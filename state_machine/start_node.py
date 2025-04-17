from langchain_core.messages import AIMessage

from logger.logging_tool import logger
from state_machine.user_state import UserState


async def start(state: UserState):
    logger.info(f"Starting the start node")
    await state.add_message("""Hi! To calculate your custom influencer campaign offer, please share:\nYour desired price per 1000 views ("
        "CPM)\nThe creator's typical view count (exact number like 100000 or range like 5000-10000)\nOptional fixed "
        "price if preferred""")
    return state

