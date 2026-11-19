"""
Central LLM factory with Gemini-primary / Groq-fallback.

Usage:
    llm = make_llm()                          # plain chat LLM
    llm = make_llm(tools=all_tools)           # tool-bound LLM
    llm = make_llm(structured=MyModel)        # structured output LLM

Fallback activates on any exception from the primary (rate-limit,
model-not-found, quota exhausted, network error, etc.).

Key design: Gemini is configured with max_retries=0 so it fails FAST
and immediately hands off to the Groq fallback, instead of spending
15–20 s on internal tenacity retries first.
"""

import os
import warnings
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from backend.log import log

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def _gemini(temperature: float = 0) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=temperature,
        max_retries=0,  # fail fast → let LangChain fallback take over immediately
    )


def _groq(temperature: float = 0) -> ChatGroq | None:
    """Returns a ChatGroq instance, or None if GROQ_API_KEY is not configured."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return ChatGroq(model=GROQ_MODEL, temperature=temperature, api_key=api_key)


def _logged_fallback(groq_runnable: Any, label: str) -> Any:
    """Wraps a Groq runnable so it logs when it's actually used."""
    original_invoke = groq_runnable.invoke
    original_ainvoke = groq_runnable.ainvoke

    def invoke_with_log(input, config=None, **kwargs):
        log(f"⚠️  Gemini unavailable — switching to Groq fallback ({GROQ_MODEL}) [{label}]")
        return original_invoke(input, config, **kwargs)

    async def ainvoke_with_log(input, config=None, **kwargs):
        log(f"⚠️  Gemini unavailable — switching to Groq fallback ({GROQ_MODEL}) [{label}]")
        return await original_ainvoke(input, config, **kwargs)

    groq_runnable.invoke = invoke_with_log
    groq_runnable.ainvoke = ainvoke_with_log
    return groq_runnable


def make_llm(
    *,
    temperature: float = 0,
    tools: list[Any] | None = None,
    structured: type | None = None,
    label: str = "llm",
) -> Any:
    """
    Returns a LangChain runnable: Gemini primary with Groq fallback.

    Pass `tools` for tool-bound usage (agent node).
    Pass `structured` for structured output (guardrail classifier).
    Do not pass both.
    """
    if tools and structured:
        raise ValueError("Pass either tools or structured, not both.")

    if tools:
        primary = _gemini(temperature).bind_tools(tools)
        groq_inst = _groq(temperature)
        fallbacks = [_logged_fallback(groq_inst.bind_tools(tools), label)] if groq_inst else []
    elif structured:
        primary = _gemini(temperature).with_structured_output(structured)
        groq_inst = _groq(temperature)
        fallbacks = [_logged_fallback(groq_inst.with_structured_output(structured), label)] if groq_inst else []
    else:
        primary = _gemini(temperature)
        groq_inst = _groq(temperature)
        fallbacks = [_logged_fallback(groq_inst, label)] if groq_inst else []

    if not fallbacks:
        warnings.warn(
            "GROQ_API_KEY not set — running Gemini-only with no fallback. "
            "Add GROQ_API_KEY to backend/.env to enable automatic failover.",
            stacklevel=2,
        )
        return primary

    return primary.with_fallbacks(
        fallbacks,
        exceptions_to_handle=(Exception,),
    )
