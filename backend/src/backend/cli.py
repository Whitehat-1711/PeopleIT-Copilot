import argparse
import asyncio
import json
import os

from backend.agent import build_agent_graph, run_agent
from backend.log import log


def format_display_answer(answer: str) -> str:
    """Formats raw model or structured guardrail JSON response for the terminal."""
    if isinstance(answer, str) and answer.strip().startswith('{"status": "blocked"'):
        try:
            data = json.loads(answer)
            return f"{data.get('message', 'Request blocked.')} [Reason: {data.get('reason')}]"
        except Exception:
            pass
    return answer


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
        answer = await run_agent(user_input, emp_id, graph=graph)
        display = format_display_answer(answer)
        print(f"\nAssistant:\n{display}\n" + "-" * 50 + "\n")


async def single_query(question: str, emp_id: str) -> None:
    graph = await build_agent_graph(emp_id)
    answer = await run_agent(question, emp_id, graph=graph)
    print(format_display_answer(answer))


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
