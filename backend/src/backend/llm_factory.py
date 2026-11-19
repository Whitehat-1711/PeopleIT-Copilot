"""
Central LLM factory — Groq primary, Gemini fallback.

Usage:
    llm = make_llm()                          # plain chat LLM
    llm = make_llm(tools=all_tools)           # tool-bound LLM
    llm = make_llm(structured=MyModel)        # structured output LLM
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

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def _groq(temperature: float = 0) -> ChatGroq | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return ChatGroq(model=GROQ_MODEL, temperature=temperature, api_key=api_key)


def _gemini(temperature: float = 0) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=temperature,
        max_retries=1,
    )


def _wrap_with_log(runnable: Any, label: str, provider: str) -> Any:
    """Wrap a runnable in a RunnableLambda that logs before invoking."""

    def invoke_logged(input, config=None, **kwargs):
        log(f"⚠️  Groq unavailable — falling back to {provider} [{label}]")
        return runnable.invoke(input, config, **kwargs)

    async def ainvoke_logged(input, config=None, **kwargs):
        log(f"⚠️  Groq unavailable — falling back to {provider} [{label}]")
        return await runnable.ainvoke(input, config, **kwargs)

    return RunnableLambda(invoke_logged, afunc=ainvoke_logged)


def make_llm(
    *,
    temperature: float = 0,
    tools: list[Any] | None = None,
    structured: type | None = None,
    label: str = "llm",
) -> Any:
    """
    Returns a LangChain runnable: Groq primary, Gemini fallback.
    If GROQ_API_KEY is not set, runs Gemini-only with a warning.
    """
    if tools and structured:
        raise ValueError("Pass either tools or structured, not both.")

    groq_inst = _groq(temperature)
    gemini_inst = _gemini(temperature)

    if not groq_inst:
        warnings.warn(
            "GROQ_API_KEY not set — running Gemini-only (no Groq primary). "
            "Add GROQ_API_KEY to backend/.env.",
            stacklevel=2,
        )
        if tools:
            return gemini_inst.bind_tools(tools)
        if structured:
            return gemini_inst.with_structured_output(structured)
        return gemini_inst

    # Build Groq primary + Gemini fallback
    if tools:
        primary = groq_inst.bind_tools(tools)
        fallback = _wrap_with_log(gemini_inst.bind_tools(tools), label, GEMINI_MODEL)
    elif structured:
        primary = groq_inst.with_structured_output(structured)
        fallback = _wrap_with_log(gemini_inst.with_structured_output(structured), label, GEMINI_MODEL)
    else:
        primary = groq_inst
        fallback = _wrap_with_log(gemini_inst, label, GEMINI_MODEL)

    return primary.with_fallbacks(
        [fallback],
        exceptions_to_handle=(Exception,),
    )
