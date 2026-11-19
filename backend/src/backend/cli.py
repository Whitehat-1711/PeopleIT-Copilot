import argparse
import asyncio
import os

from backend.agent import build_agent_graph, run_agent
from backend.log import log


def format_display_answer(resp) -> str:
    """Formats structured AgentResponse object for CLI terminal rendering."""
    if isinstance(resp, dict):
        answer = resp.get("answer", "")
        status = resp.get("status", "allowed")
        reason = resp.get("reason")
        route = resp.get("route", "direct")
        confidence = resp.get("confidence", 0.9)
        sources = resp.get("sources", [])

        if status == "blocked":
            return f"{answer} [Blocked: {reason}]"

        lines = [answer]
        meta_lines = []
        if sources:
            chips = "  ".join(
                [f"[{s.get('document', '')} #{s.get('section', '')}]" for s in sources]
            )
            meta_lines.append(f"📚 Sources: {chips}")
        meta_lines.append(f"🧭 Route: {route} | Confidence: {int(confidence * 100)}%")

        if meta_lines:
            lines.append("\n" + "\n".join(meta_lines))
        return "\n".join(lines)
    return str(resp)


async def interactive_loop(emp_id: str) -> None:
    groq_status = "✅ Groq primary active" if os.getenv("GROQ_API_KEY") else "⚠️  No GROQ_API_KEY — Gemini only"
    log(f"Starting HR & IT Assistant for {emp_id} | {groq_status}")
    graph = await build_agent_graph(emp_id)
    print("\nReady! Type your HR/IT question below (type 'exit' or 'quit' to stop).\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            break

        log(f"💬 Question received for {emp_id}")
        resp = await run_agent(user_input, emp_id, graph=graph)
        display = format_display_answer(resp)
        print(f"\nAssistant:\n{display}\n" + "-" * 50 + "\n")


async def single_query(question: str, emp_id: str) -> None:
    graph = await build_agent_graph(emp_id)
    resp = await run_agent(question, emp_id, graph=graph)
    print(format_display_answer(resp))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="HR & IT AI Assistant CLI",
    )
    parser.add_argument(
        "--as",
        dest="emp_id",
        required=True,
        metavar="EMP_ID",
        help="Your employee ID, e.g. --as E102",
    )
    parser.add_argument(
        "question",
        nargs="*",
        help="Optional one-shot question. Omit to enter interactive mode.",
    )
    args = parser.parse_args()

    if args.question:
        asyncio.run(single_query(" ".join(args.question), args.emp_id))
    else:
        asyncio.run(interactive_loop(args.emp_id))


if __name__ == "__main__":
    main()
