from aiogram import Router
from aiogram.types import Message

from app.logger.logging_tool import logger
from app.state_machine.graph_builder import app

message_router = Router()


@message_router.message()
async def handle_message(msg: Message):
    logger.info(f"[HANDLE_MESSAGE] Received message from {msg.chat.id}: {msg.text}")

    checkpoint = {
        "configurable": {"thread_id": msg.chat.id}
    }

    current_state = await app.aget_state(checkpoint)
    logger.debug(f"[HANDLE_MESSAGE] Current state: {current_state}")

    if not current_state.values:
        await msg.answer("Please start with the /start command.")
        return

    updated_state = current_state.values.copy()
    updated_state["messages"].append(msg.text)
    logger.debug(f"[HANDLE_MESSAGE] Updated state: {updated_state}")

    new_checkpoint = await app.aupdate_state(
        config=checkpoint,
        values={"messages": updated_state["messages"]}
    )
    logger.debug(f"[HANDLE_MESSAGE] New checkpoint: {new_checkpoint}")

    async for step in app.astream(None, new_checkpoint):
        logger.debug(f"[HANDLE_MESSAGE] Step: {step}")
        for node_name, node_data in step.items():
            if isinstance(node_data, dict) and "messages" in node_data:
                messages = node_data["messages"]
                if messages:
                    last_message = messages[-1]
                    logger.debug(f"[HANDLE_MESSAGE] Found message in node {node_name}: {last_message}")
                    await msg.answer(last_message)
                    break
