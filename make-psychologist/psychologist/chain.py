import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
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


def build_chain(retriever, model: str | None = None):
    llm = _build_llm(model)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    combine_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, combine_chain)
