import argparse
import asyncio
import os

from backend.agent import build_agent_graph, run_agent
from backend.log import log


async def interactive_loop(emp_id: str) -> None:
    groq_status = "✅ Groq fallback active" if os.getenv("GROQ_API_KEY") else "⚠️  No GROQ_API_KEY — Gemini only"
    log(f"Starting HR & IT Assistant for {emp_id} | {groq_status}")
    graph = await build_agent_graph()
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
        print(f"\nAssistant:\n{answer}\n" + "-" * 50 + "\n")


async def single_query(question: str, emp_id: str) -> None:
    graph = await build_agent_graph()
    answer = await run_agent(question, emp_id, graph=graph)
    print(answer)


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
