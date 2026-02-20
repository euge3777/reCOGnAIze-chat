import os
import sys
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env so OPENAI_API_KEY is available
load_dotenv()

# Ensure we can import from src/
BASE_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from domain_chatbot import initialize_chatbot  # type: ignore
from file_processor import FileProcessor  # type: ignore
from report_summarizer import summarize_report  # type: ignore


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    file_context: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str


app = FastAPI(title="ReCOGnAIze Backend API")

# CORS: allow both local dev and deployed frontends (Vercel, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can tighten this later by listing specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazily initialize chatbot so startup failures don't crash import
_chatbot = None


def get_chatbot():
    global _chatbot
    if _chatbot is None:
        _chatbot = initialize_chatbot()
    return _chatbot


def _format_report_reply(text: str) -> str:
    """Post-process LLM reply for report questions to improve readability.

    - Puts section labels and bullet lines on their own lines
    - Ensures there are line breaks before bullet points
    """
    if not text:
        return text

    formatted = text

    # Ensure key section headers start on their own line
    for header in ["Your Results by Game:", "What This Means:", "Next Steps:"]:
        formatted = formatted.replace(header, f"{header}\n")

    # Put bullets on separate lines when they're inline after text
    formatted = formatted.replace(" • ", "\n• ")

    # Also handle cases like "Next Steps:\n•" where bullets run together
    formatted = formatted.replace("Next Steps:\n•", "Next Steps:\n\n•")

    return formatted.strip()


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """Main chat endpoint for the React frontend.

    - `message`: user question
    - `conversation_history`: optional list of past messages
    - `file_context`: optional pre-processed / summarized report text
    """
    chatbot = get_chatbot()

    lower_q = (payload.message or "").lower()

    # If we have a summarized report, handle this request with a
    # dedicated prompt that focuses on reading and interpreting the
    # report, rather than going through the generic DomainChatbot
    # flow which was treating the question as if no details existed.
    #
    # BUT: if the user is asking a general concept question (e.g. "what is MCI"),
    # we should use the domain chatbot instead so they get a clean
    # explanation rather than another personalized plan.
    if payload.file_context:
        # Detect generic concept questions that should bypass the
        # report-specific pipeline.
        is_concept_question = any(
            phrase in lower_q
            for phrase in [
                "what is mci",
                "what is mild cognitive impairment",
                "explain mci",
                "explain mild cognitive impairment",
                "what is dementia",
                "what is cognitive impairment",
            ]
        )

        if is_concept_question:
            history = payload.conversation_history or []
            reply = chatbot.generate_response(payload.message, conversation_history=history)
            return ChatResponse(reply=reply)

        history = payload.conversation_history or []

        # Simple intent routing for report-based questions so answers can
        # be more dynamic and not always the full 4-section plan.
        is_personalization_intent = any(
            phrase in lower_q
            for phrase in [
                "personalize my plan",
                "personalise my plan",
                "personalized plan",
                "personalised plan",
                "ask me questions",
            ]
        )

        is_full_plan_intent = any(
            phrase in lower_q
            for phrase in [
                "action plan",
                "create a plan",
                "create an action plan",
                "personalized cognitive health plan",
                "personalised cognitive health plan",
                "give me personalized advice based on my report",
                "give me personalised advice based on my report",
                "overall plan",
                "next steps",
                "next action",
                "next actions",
                "what are my next actions",
                "what are my next steps",
                "what should i do next",
                "what should i do now",
            ]
        )

        # Optionally still use the knowledge base for extra context
        kb_context = chatbot.get_context(payload.message, k=5)

        system_prompt = (
            "You are an expert cognitive health assistant helping a user understand their "
            "ReCOGnAIze cognitive performance report. You must use the report text that is "
            "provided to you and explain it in clear, supportive language suitable for older adults. "
            "Always answer concisely, using short paragraphs and clean bullet lines that start with '• '. "
            "Do NOT use markdown headings like '#', '##', or '###'. "
            "If the conversation history already includes an explanation of the user's scores, "
            "avoid repeating the same detailed description of each domain. Instead, give a very brief "
            "reminder of the overall pattern (for example: which areas are strong or lower) and then "
            "focus on new, practical next steps or clarifications that move the conversation forward."
        )

        # Build conversation-style messages
        messages: list[dict[str, str]] = []

        if history:
            for msg in history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    messages.append({"role": role, "content": content})

        # If the user is explicitly asking for exact scores, return a very focused
        # scores-only format to improve UX.
        wants_scores_only = "score" in lower_q and (
            "each game" in lower_q or "exact score" in lower_q or "scores" in lower_q
        )

        if wants_scores_only:
            # Scores-only format for questions explicitly asking for exact scores
            user_content_parts = [
                "You have been given a summarized cognitive performance report for this user.",
                "The user is specifically asking for their exact score for each game / domain.",
                "\nCRITICAL INSTRUCTIONS (FOLLOW EXACTLY):",
                "- You DO have access to the user's results in the REPORT TEXT below. Never say that you ",
                "  do not have their specific results or that you are missing details.",
                "- ONLY list the scores and labels for each game or cognitive domain.",
                "- Do NOT include lifestyle advice, explanations, or extra commentary unless the user ",
                "  explicitly asks for it.",
                "- Format the answer exactly like this, with no extra text before or after:",
                "  Your Results by Game:",
                "  • Processing Speed (Symbol Matching): 28 – HIGH (average: 29)",
                "  • Executive Function (Trail Making): 12 – MEDIUM (average: 18)",
                "  (Use the real numbers and domains from the report.)",
                "- Use the bullet character '•' at the start of each line, not '-'.",
                "- Keep the answer under 6 bullets if possible.",
            ]
        elif is_personalization_intent:
            # User is explicitly asking for more personalization; focus on
            # a brief reflection plus targeted clarifying questions.
            user_content_parts = [
                "You have been given a summarized cognitive performance report for this user.",
                "The user is asking you to personalize recommendations further by asking them specific questions.",
                "\nCRITICAL INSTRUCTIONS (FOLLOW EXACTLY):",
                "- You DO have access to the user's results in the REPORT TEXT below. Never say that you ",
                "  do not have their specific results or that you are missing details.",
                "- Start with one short, empathetic sentence acknowledging that wanting a more personalized plan is understandable.",
                "- Then, in 1–2 short sentences, briefly reflect what the report suggests (for example: which domains look strong, which look lower).",
                "- Next, ask 3–5 clear, concrete questions to personalize the plan further. Focus on their exercise habits, diet, sleep, mood/stress, vascular risk factors, and daily functioning.",
                "- Format each question as a separate bullet line starting with '• '.",
                "- Do NOT provide a full plan yet—only set up the next step by gathering the right details.",
                "- Use simple, supportive language suitable for older adults and avoid medical jargon.",
            ]
        elif is_full_plan_intent:
            # Full structured advice format inspired by the slide deck for
            # users who explicitly ask for a comprehensive plan.
            user_content_parts = [
                "You have been given a summarized cognitive performance report for this user.",
                "FIRST, carefully read the REPORT TEXT below. THEN answer the user's question.",
                "\nCRITICAL INSTRUCTIONS (FOLLOW EXACTLY):",
                "- You DO have access to the user's results in the REPORT TEXT below. Never say that you ",
                "  do not have their specific results or that you are missing details.",
                "- Always base your explanation on the information in the report, including the actual scores and ",
                "  game / domain names when helpful.",
                "- Focus on being concise and easy to read.",
                "- Use short paragraphs (2–3 sentences) and bullet lines starting with '• '.",
                "- Do NOT use markdown headings (#, ##, ###) or HTML tags.",
                "",
                "FORMAT YOUR ANSWER USING THESE FOUR SECTIONS IN ORDER (unless the user explicitly asks for something different):",
                "1) A heading line for UNDERSTANDING RESULTS:",
                "   '📊 Understanding Your Results' on its own line.",
                "   Then 1 short paragraph (2–3 short sentences) that explains the overall pattern of scores ",
                "   in simple, reassuring language.",
                "",
                "2) A heading line for ACTION PLAN:",
                "   '🎯 Your Personalized Action Plan' on its own line.",
                "   Then 3–6 bullet lines (each starting with '• ') that describe concrete lifestyle and cognitive ",
                "   strategies tailored to this user's pattern of results (for example: physical activity, diet, ",
                "   sleep, cognitive exercises, managing vascular risk factors).",
                "",
                "3) A heading line for MONITORING / RETEST:",
                "   '📅 Monitoring Your Progress' on its own line.",
                "   Then 2–4 bullet lines that describe when to check in on progress and when to repeat the ",
                "   ReCOGnAIze assessment (for example: 3 months for lifestyle check-in, 12 months for retest).",
                "",
                "4) A heading line for WHEN TO SEE A DOCTOR:",
                "   '⚕️ When to See Your Doctor' on its own line.",
                "   Then 3–6 bullet lines describing red-flag symptoms or changes that should prompt the user ",
                "   to talk to their healthcare provider for further assessment.",
                "",
                "END with one short, reassuring sentence reminding the user that this is educational information ",
                "and does not replace medical advice, and that early discussion with their healthcare provider can help.",
                "Then add a final line starting with 'To personalize this further, please tell me:' followed by 2–3",
                "short questions (in a single sentence or separated by semicolons) about their lifestyle or health, ",
                "so that future advice can be more tailored.",
            ]
        else:
            # Focused Q&A format for other report-based questions (for example,
            # "what does my processing speed score mean", "how often should I retake",
            # "how do my scores compare to others my age").
            user_content_parts = [
                "You have been given a summarized cognitive performance report for this user.",
                "FIRST, carefully read the REPORT TEXT below. THEN answer the user's specific question.",
                "\nCRITICAL INSTRUCTIONS (FOLLOW EXACTLY):",
                "- You DO have access to the user's results in the REPORT TEXT below. Never say that you ",
                "  do not have their specific results or that you are missing details.",
                "- Directly address the user's question (for example: understanding a single domain score, comparing scores to age norms, retesting frequency, lifestyle impact).",
                "- Where relevant, briefly reference what the report shows (for example: which domains are strong or lower) in everyday language.",
                "- Use a warm, empathetic tone (for example: 'I understand this can be concerning...').",
                "- Use short paragraphs and, when helpful, 2–4 bullet lines starting with '• ' to list concrete suggestions.",
                "- End with one short section that begins with 'Here is what you can do today:' and give 2–3 simple, practical next steps.",
                "- Include a brief reminder that this is educational guidance and that medical decisions should be made with a healthcare provider.",
                "- Do NOT force the full four-section slide layout in this mode; only use headings if they come naturally from the answer.",
            ]

        if kb_context:
            user_content_parts.append(
                "\nOPTIONAL KNOWLEDGE BASE CONTEXT (for additional background, not for scores):\n"
                + kb_context
            )

        user_content_parts.append("\n\nREPORT TEXT (from uploaded file):\n" + payload.file_context)
        user_content_parts.append("\n\nUSER QUESTION: " + payload.message)

        messages.append({"role": "user", "content": "\n".join(user_content_parts)})

        response = chatbot.client.chat.completions.create(
            model=chatbot.model,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.7,
            max_tokens=800,
        )

        raw_content = response.choices[0].message.content or ""
        content = _format_report_reply(raw_content)
        return ChatResponse(reply=content)

    # Fallback: no report context, use the existing domain chatbot flow
    history = payload.conversation_history or []
    reply = chatbot.generate_response(payload.message, conversation_history=history)
    return ChatResponse(reply=reply)


@app.options("/chat")
async def chat_options() -> Response:
    """Handle CORS preflight requests for the /chat endpoint.

    Some hosting environments may not let CORSMiddleware short-circuit
    OPTIONS requests correctly, which can cause the browser preflight
    to get a 400 response. Returning an empty 200 response here ensures
    the frontend can successfully POST to /chat.
    """
    return Response(status_code=200)


@app.post("/upload")
async def upload_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Handle file upload from React.

    - Processes file with FileProcessor
    - If PDF, runs the multi-step report summarizer
    - Returns metadata plus the summarized content to be used as context
    """
    # Pass the UploadFile wrapper; FileProcessor can handle it
    file_data = FileProcessor.process_uploaded_file(file)
    if not file_data:
        return {"error": "Unable to process file"}

    # If this is a PDF, keep the extracted text as-is so the
    # assistant sees the raw report (scores, labels, etc.). The
    # text is already length-limited inside FileProcessor.

    # Log a summary of what was parsed so you can verify in the backend terminal.
    content = file_data.get("content") or ""
    snippet = content[:400].replace("\n", " ") + ("..." if len(content) > 400 else "")
    print(
        "[UPLOAD] Parsed report",
        {
            "filename": file.filename,
            "file_type": file_data.get("file_type"),
            "size_bytes": file_data.get("size_bytes"),
            "content_length": len(content),
            "snippet": snippet,
        },
        flush=True,
    )

    return {
        "filename": file.filename,
        "file_type": file_data.get("file_type"),
        "size_bytes": file_data.get("size_bytes"),
        "content": content,  # summarized or raw text for context
    }


@app.get("/health")
async def healthcheck() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}
