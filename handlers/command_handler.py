from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from logger.logging_tool import logger
from state_machine.graph_builder import app
from state_machine.user_state import UserState

command_router = Router()


@command_router.message(Command("start"))
async def start_command(msg: Message):
    state = UserState()
    thread_context  = {
        "configurable": {"thread_id": msg.chat.id},
        "values": state.initializate_state(),
    }
    answer = await app.ainvoke({"messages": ["/start"]}, config=thread_context )
    logger.info(f"Sent message to user {answer}")
    await msg.answer(answer["messages"][-1])
