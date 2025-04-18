from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.logger.logging_tool import logger
from app.state_machine.graph_builder import app
from app.state_machine.user_state import UserState

command_router = Router()


@command_router.message(Command("start"))
async def start_command(msg: Message):
    logger.info("[START_COMMAND] Received start command from user: {}".format(msg.chat.id))

    state = UserState()
    thread_context = {
        "configurable": {"thread_id": msg.chat.id},
        "values": state.initializate_state(),
    }

    try:
        answer = await app.ainvoke({"messages": ["/start"]}, config=thread_context)
        logger.info(f"[START_COMMAND] Sent message to user with response: {answer}")
        await msg.answer(answer["messages"][-1])
    except Exception as e:
        logger.error(f"[START_COMMAND] Error processing start command: {e}")
