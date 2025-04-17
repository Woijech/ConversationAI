from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from logger.logging_tool import logger
from state_machine.graph_builder import app
from state_machine.user_state import UserState

message_router = Router()

@message_router.message()
async def handle_message(msg: Message):
    checkpoint = {
        "configurable": {"thread_id": msg.chat.id}
    }
    current_state = await app.aget_state(checkpoint)

    logger.debug(f"current_state: {current_state}")
    if not current_state.values:
        await msg.answer("Пожалуйста, начните с команды /start")
        return

    updated_state = current_state.values.copy()
    updated_state["messages"].append(msg.text)

    logger.debug(f"updated_state: {updated_state}")

    new_checkpoint = await app.aupdate_state(
        config=checkpoint,
        values={"messages": updated_state["messages"]}
    )
    logger.debug(f"Branch config: {new_checkpoint}")
    async for step in app.astream(None,new_checkpoint):
        logger.debug(f"Step: {step}")
        for node_name,node_data in step.items():
            if isinstance(node_data, dict) and "messages" in node_data:
                messages = node_data["messages"]
                if messages:
                    last_message = messages[-1]
                    logger.debug(f"Found message in node {node_name}: {last_message}")
                    await msg.answer(last_message)
                    break
