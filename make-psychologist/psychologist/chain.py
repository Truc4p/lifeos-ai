import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from .config import LLM_PROVIDER, LLM_MODEL, OPENROUTER_MODEL, OPENROUTER_BASE_URL
from .prompts import SYSTEM_PROMPT


def _build_llm(model: str | None = None):
    # An explicit model ID containing "/" is always an OpenRouter model
    use_openrouter = LLM_PROVIDER == "openrouter" or (model and "/" in model)
    if use_openrouter:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model or OPENROUTER_MODEL,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=OPENROUTER_BASE_URL,
            temperature=0.7,
        )
    from langchain_groq import ChatGroq
    return ChatGroq(model=model or LLM_MODEL, temperature=0.7)


def _format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


class _AnswerDict:
    """Wraps the LCEL chain to return {"answer": ...} matching the api.py interface."""
    def __init__(self, chain):
        self._chain = chain

    def invoke(self, inputs: dict) -> dict:
        answer = self._chain.invoke(inputs)
        return {"answer": answer}


def build_chain(retriever, model: str | None = None):
    llm = _build_llm(model)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    chain = (
        RunnablePassthrough.assign(
            context=lambda x: _format_docs(retriever.invoke(x["input"]))
        )
        | prompt
        | llm
        | StrOutputParser()
    )
    return _AnswerDict(chain)
