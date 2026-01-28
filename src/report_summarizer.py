"""Summarization utilities for ReCOGnAIze PDF reports.

Workflow:
- Split long report text into several manageable chunks
- Call the OpenAI chat model to summarize each chunk
- Combine chunk summaries into a compact overall summary

The final overall summary is what will be injected into the
chatbot context instead of the full raw PDF text.
"""

import math
import os
from typing import List, Dict

from openai import OpenAI


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


def _chunk_text(text: str, target_chunks: int = 6, min_chunk_chars: int = 1200) -> List[str]:
    """Split text into roughly `target_chunks` pieces on paragraph boundaries.

    We first split on double newlines (paragraphs) and then group
    paragraphs until we reach the desired size. This keeps sections
    coherent while avoiding huge prompts.
    """
    text = text.strip()
    if not text:
        return []

    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return [text]

    total_chars = len(text)
    # Aim for N chunks but respect a minimum paragraph size.
    approx_chunk_size = max(min_chunk_chars, total_chars // max(target_chunks, 1))

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # If adding this paragraph would overshoot the target size
        # and we already have some content, start a new chunk.
        if current and current_len + len(para) > approx_chunk_size and len(chunks) < target_chunks - 1:
            chunks.append("\n\n".join(current).strip())
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)

    if current:
        chunks.append("\n\n".join(current).strip())

    # If we still ended up with more than target_chunks, merge extras
    # into the last chunk to keep API calls bounded.
    if len(chunks) > target_chunks:
        head = chunks[: target_chunks - 1]
        tail = "\n\n".join(chunks[target_chunks - 1 :])
        chunks = head + [tail]

    return chunks


def _summarize_chunk(client: OpenAI, model: str, chunk: str, index: int, total: int) -> str:
    """Call the chat model to summarize a single chunk of the report."""
    system = (
        "You are an expert cognitive health assistant. You are helping to "
        "summarize a patient's ReCOGnAIze cognitive performance report."
    )

    user = (
        f"You are summarizing section {index + 1} of {total} from a ReCOGnAIze cognitive performance report. "
        "Your goal is to shorten the wording so it fits into a small prompt, "
        "BUT you must preserve the key quantitative and categorical details.\n\n"
        "IMPORTANT INSTRUCTIONS (do all of these):\n"
        "- Do NOT drop or approximate any explicit NUMERIC SCORES that appear in this section "
        "  (for example: values like '22', '98', '14', '0 100', 'Your Score', 'Average Score').\n"
        "- Do NOT drop qualitative labels such as 'WEAK', 'STRONG', 'ADEQUATE', 'AVERAGE'. "
        "  Include them exactly as written.\n"
        "- If multiple scores are shown, list them all.\n"
        "- It is OK to compress repeated explanatory sentences as long as all scores and labels remain.\n\n"
        "Write a concise summary in this structure (plain text, no JSON):\n"
        "1) Domain & page context: which cognitive domain(s) this section is about, and if visible, the page number.\n"
        "2) Scores: list ALL scores and labels exactly as shown in the text.\n"
        "3) Meaning in plain language: 2-3 short sentences explaining what these scores mean.\n"
        "4) Key recommendations: 3-5 short bullet points of concrete lifestyle or training steps mentioned or clearly implied.\n\n"
        f"SECTION {index + 1}/{total}:\n" + chunk
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},  # type: ignore[arg-type]
            {"role": "user", "content": user},  # type: ignore[arg-type]
        ],
        temperature=0.3,
        max_tokens=300,
    )

    content = response.choices[0].message.content or ""
    return content.strip()


def _summarize_overall(client: OpenAI, model: str, chunk_summaries: List[str]) -> str:
    """Combine chunk-level summaries into a concise overall report summary."""
    joined = "\n\n".join(
        f"Section {i + 1} summary:\n{summary}" for i, summary in enumerate(chunk_summaries)
    )

    system = (
        "You are an expert cognitive health assistant. Based on summaries "
        "from a patient's ReCOGnAIze cognitive performance report, create an "
        "overall explanation that is clear, concise, and patient friendly."
    )

    user = (
        "Here are section summaries from the report. First, infer the patient's "
        "key cognitive strengths and weaknesses (processing speed, executive "
        "function, attention, working memory, overall risk). Then provide:\n"
        "1) A short paragraph explaining what these results mean in plain language,\n"
        "2) 4-6 specific, evidence-informed lifestyle and training recommendations "
        "tailored to these results (exercise, diet, sleep, cognitive training, vascular health),\n"
        "3) A brief note encouraging discussion with a healthcare provider.\n\n"
        "SECTION SUMMARIES:\n" + joined
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},  # type: ignore[arg-type]
            {"role": "user", "content": user},  # type: ignore[arg-type]
        ],
        temperature=0.4,
        max_tokens=600,
    )

    content = response.choices[0].message.content or ""
    return content.strip()


def summarize_report(text: str, target_chunks: int = 6) -> Dict[str, object]:
    """Summarize a full ReCOGnAIze report text in multiple steps.

    Returns a dict with:
    - chunk_summaries: list[str] of per-section summaries
    - overall_summary: str compact narrative used in chat context
    """
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4")

    chunks = _chunk_text(text, target_chunks=target_chunks)
    if not chunks:
        return {"chunk_summaries": [], "overall_summary": ""}

    chunk_summaries: List[str] = []
    total = len(chunks)

    for i, chunk in enumerate(chunks):
        try:
            summary = _summarize_chunk(client, model, chunk, i, total)
        except Exception:
            summary = "(Error summarizing this section.)"
        chunk_summaries.append(summary)

    # First, try to generate a short meta-summary across sections.
    meta_summary = ""
    try:
        meta_summary = _summarize_overall(client, model, chunk_summaries)
    except Exception:
        meta_summary = ""

    # Then build the overall summary that will actually be used in the
    # chat context. It contains both a brief high-level explanation and
    # a section-by-section view that keeps all scores and labels.
    header = "SECTION-BY-SECTION SUMMARY (scores and page details):"\
        if chunk_summaries else ""

    if meta_summary:
        overall = (
            meta_summary
            + ("\n\n" + header if header else "")
            + ("\n" if header else "")
            + ("\n\n".join(chunk_summaries) if chunk_summaries else "")
        )
    else:
        overall = (
            (header + "\n" if header else "")
            + ("\n\n".join(chunk_summaries) if chunk_summaries else "")
        )

    return {
        "chunk_summaries": chunk_summaries,
        "overall_summary": overall,
    }
