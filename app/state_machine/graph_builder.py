from app.state_machine.accept_deal_node import accept
from app.state_machine.decline_deal_node import decline_offer
from app.state_machine.negotiating_node import negotiating
from app.state_machine.negotiating_cpm_node import negotiating_cpm
from app.state_machine.negotiating_fix_node import negotiating_fix
from app.state_machine.rate_node import rate
from app.state_machine.start_node import start
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.state_machine.user_state import UserState


def decide(state: UserState):
    if state.solution == "accepted":
        return "accept"
    elif state.solution == "rejected":
        return "decline_offer"
    else:
        if state.deal_type == "fix":
            return "negotiating_fix"
        elif state.deal_type == "cpm":
            return "negotiating_cpm"
        else:
            return "negotiating"


memory = MemorySaver()
workflow = StateGraph(state_schema=UserState)
workflow.add_node("start", start)
workflow.add_node("rate", rate)

workflow.add_node("negotiating", negotiating)
workflow.add_node("negotiating_fix", negotiating_fix)
workflow.add_node("negotiating_cpm", negotiating_cpm)

workflow.add_node("accept", accept)
workflow.add_node("decline_offer", decline_offer)

workflow.set_entry_point("start")
workflow.add_edge("start", "rate")
workflow.add_edge("rate", "negotiating")
workflow.add_conditional_edges(
    "negotiating",
    decide,
    {
        "accept": "accept",
        "decline_offer": "decline_offer",
        "negotiating": "negotiating",
        "negotiating_fix": "negotiating_fix",
        "negotiating_cpm": "negotiating_cpm"
    }
)
workflow.add_conditional_edges(
    "negotiating_fix",
    decide,
    {
        "accept": "accept",
        "decline_offer": "decline_offer",
        "negotiating_fix": "negotiating_fix",
    }
)
workflow.add_conditional_edges(
    "negotiating_cpm",
    decide,
    {
        "accept": "accept",
        "negotiating_cpm": "negotiating_cpm",
        "negotiating": "negotiating",
        "negotiating_fix": "negotiating_fix"
    }
)
workflow.add_edge("accept", END)
workflow.add_edge("decline_offer", END)
app = workflow.compile(checkpointer=memory,
                       interrupt_before=["rate", "negotiating", "negotiating_fix", "negotiating_cpm", "decline_offer"])
