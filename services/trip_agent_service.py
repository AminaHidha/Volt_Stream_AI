import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.errors import GraphRecursionError

from .trip_tools import make_trip_tools

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """You are the VoltStream Trip Planning Assistant.

Your job is to help the user plan an EV road trip using the tools provided.
Rules:

- ALWAYS call plan_route FIRST for any trip request â€” never invent
  distances, durations, or station names.
- NEVER claim there is a "connection issue," "API error," or "technical
  problem" unless a tool result you actually received literally contains
  an "error" field. If a tool call returns real data, you MUST use that
  data and continue — do not invent excuses instead of reading the result.
- "Cheapest" means lowest min_price_per_kwh among stations_near_route.
  "Fastest charger" means highest max_power_kw.
- Only call get_chargers_for_station / check_slot_availability /
  create_booking if the user explicitly asked to BOOK a charging stop
  along the way, not just plan or view the route.
- Do NOT call the same tool with the same arguments more than once.
- To book a SPECIFIC station mentioned earlier in this conversation (e.g.
  from a plan_route result), you must follow this exact sequence and may
  not skip steps:
    1. Find that station's station_id in the plan_route tool result already
       in this conversation.
    2. Call get_chargers_for_station with that real station_id to get the
       charger's real id.
    3. Call check_slot_availability with that real charger id.
    4. Only then call create_booking with the real slot_id you just saw.
- NEVER invent a charger_id, slot_id, or station_id at any point. If you
  are about to call a tool with a number you did not literally see in an
  earlier tool result in this conversation, STOP and call
  get_chargers_for_station again instead.
- Before calling create_booking, you must already have slot_id, date,
  price_per_kwh, and power_output from earlier tool results â€” never guess.
- Once you've answered the user's actual question (route info, or a
  completed booking), STOP calling tools and give your final answer.
- If a location can't be found or no stations are near the route, STOP
  and tell the user plainly instead of retrying tools.
- Always state prices in â‚¹ (INR), never as cents or dollars.
- Keep your final answer short (2-4 sentences), plain text, no markdown.
"""


def build_graph(token: str):
    tools = make_trip_tools(token)

    llm = ChatOpenAI(
        model="openrouter/free",
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.1,
        max_tokens=500,
        default_headers={
            "HTTP-Referer": "https://voltstream.app",
            "X-Title": "VoltStream Trip Agent",
        },
    ).bind_tools(tools)

    def agent_node(state: MessagesState):
        response = llm.invoke(state["messages"])
        if isinstance(response, AIMessage) and response.tool_calls:
            for tc in response.tool_calls:
                print(f"[TRIP AGENT] calling tool: {tc['name']}  args: {tc['args']}")
        else:
            print(f"[TRIP AGENT] final answer: {response.content}")
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


def run_trip_agent(user_message: str, token: str, today_date: str, history: list = None):
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
        print("[TRIP AGENT] Hit recursion limit.")
        return (
            "I'm having trouble planning that trip â€” could you give clearer start and end locations?",
            None,
        )
    except Exception as e:
        print(f"[TRIP AGENT] Unexpected error: {e}")
        return (
            "Something went wrong while planning that trip â€” please try again.",
            None,
        )

    messages_out = final_state["messages"]
    final_reply = messages_out[-1].content or "I've got the information but I'm having trouble putting it into words right now â€” could you ask me to confirm the booking again?"

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