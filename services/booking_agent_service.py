import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.errors import GraphRecursionError

from .booking_tools import make_booking_tools

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """You are the VoltStream Booking Assistant.

Your job is to help the user find and book an EV charging slot using the
tools provided. Rules:

- ALWAYS use the tools to get real data. Never invent station names,
  prices, charger IDs, or slot times.
- NEVER claim there is a "connection issue," "API error," or "technical
  problem" unless a tool result you actually received literally contains
  an "error" field. If a tool call returns real data, you MUST use that
  data and continue — do not invent excuses instead of reading the result.
- "Cheapest" means the lowest price_per_kwh among the chargers you found.
- Do NOT call the same tool with the same arguments more than once — you
  already have that result from earlier in this conversation, look back
  at it instead of calling again.
- NEVER invent a charger_id, slot_id, or station_id at any point. If you
  are about to call a tool with a number you did not literally see in an
  earlier tool result in this conversation, STOP and call the appropriate
  search/lookup tool again instead of guessing.
- Before calling create_booking, you must already have a specific slot_id,
  date, price_per_kwh, and power_output from earlier tool results in this
  conversation — never guess these values.
- Once you have booked a slot (create_booking succeeded), STOP calling
  tools and give your final answer immediately.
- If no matching station/charger/slot exists, STOP and tell the user
  plainly instead of retrying tools.
- If the user says a relative date like "tomorrow", resolve it yourself
  using today's date given below, and mention the resolved date back to
  the user in your final answer.
- Keep your final answer short (2-3 sentences), plain text, no markdown.
- After a successful booking, tell the user the booking ID, the price,
  and that a payment window will open next.
"""


def build_graph(token: str):
    tools = make_booking_tools(token)

    llm = ChatOpenAI(
        model="openrouter/free",
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.1,
        max_tokens=500,
        default_headers={
            "HTTP-Referer": "https://voltstream.app",
            "X-Title": "VoltStream Booking Agent",
        },
    ).bind_tools(tools)

    def agent_node(state: MessagesState):
        response = llm.invoke(state["messages"])
        if isinstance(response, AIMessage) and response.tool_calls:
            for tc in response.tool_calls:
                print(f"[BOOKING AGENT] calling tool: {tc['name']}  args: {tc['args']}")
        else:
            print(f"[BOOKING AGENT] final answer: {response.content}")
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


def run_booking_agent(user_message: str, token: str, today_date: str, history: list = None):
    app = build_graph(token)

    messages = [SystemMessage(content=f"{SYSTEM_PROMPT}\nToday's date is {today_date}.")]

    for turn in (history or []):
        if turn.role == "user":
            messages.append(HumanMessage(content=turn.content))
        elif turn.role == "assistant":
            messages.append(AIMessage(content=turn.content))

    messages.append(HumanMessage(content=user_message))

    initial_state = {"messages": messages}

    try:
        final_state = app.invoke(initial_state, config={"recursion_limit": 20})
    except GraphRecursionError:
        print("[BOOKING AGENT] Hit recursion limit.")
        return (
            "I'm having trouble completing that request — could you try being more specific about the city and date?",
            None,
        )
    except Exception as e:
        print(f"[BOOKING AGENT] Unexpected error: {e}")
        return (
            "Something went wrong while processing that — please try again.",
            None,
        )

    messages_out = final_state["messages"]
    final_reply = messages_out[-1].content or "I've processed your request — could you confirm what you'd like to do next?"

    booking_result = None
    for msg in messages_out:
        if isinstance(msg, ToolMessage) and msg.name == "create_booking":
            try:
                parsed = json.loads(msg.content)
                if "error" not in parsed:
                    booking_result = parsed
            except (json.JSONDecodeError, TypeError):
                pass

    return final_reply, booking_result