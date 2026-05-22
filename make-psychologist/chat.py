#!/usr/bin/env python3
"""Interactive AI psychologist chat loop.

Usage:
    python chat.py

Run `python ingest.py` first to build the vector store.
"""
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from psychologist.vectorstore import get_vectorstore, get_retriever
from psychologist.chain import build_chain

load_dotenv()


def main() -> None:
    vs = get_vectorstore()
    retriever = get_retriever(vs)
    chain = build_chain(retriever)
    chat_history: list = []

    print("AI Psychologist — type 'quit' to exit\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break
        if not user_input:
            continue

        result = chain.invoke({"input": user_input, "chat_history": chat_history})
        answer = result["answer"]
        print(f"\nPsychologist: {answer}\n")

        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=answer))


if __name__ == "__main__":
    main()
