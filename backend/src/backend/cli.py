import asyncio
import sys
from backend.agent import ask_agent, build_agent_graph


async def interactive_loop() -> None:
    print("Initializing HR & IT Assistant (connecting to Postgres MCP & ChromaDB)...")
    graph = await build_agent_graph()
    print("Ready! Type your HR/IT question below (type 'exit' or 'quit' to stop).\n")

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

        answer = await ask_agent(user_input, graph)
        print(f"\nAssistant:\n{answer}\n" + "-" * 50 + "\n")


async def single_query(question: str) -> None:
    graph = await build_agent_graph()
    answer = await ask_agent(question, graph)
    print(answer)


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        asyncio.run(single_query(question))
    else:
        asyncio.run(interactive_loop())


if __name__ == "__main__":
    main()