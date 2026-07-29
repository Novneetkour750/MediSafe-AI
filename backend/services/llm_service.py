import json

from google import genai

from utils.exceptions import LLMGenerationError
from utils.logger import get_logger

log = get_logger("services.llm")


class LLMService:
    def __init__(self, api_key: str, model_name: str):
        if not api_key:
            log.warning("GEMINI_API_KEY is not set — LLM calls will fail")
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def generate(self, contents) -> str:
        """Low-level call. `contents` is a prompt string or a list like
        [image, prompt]. Every other method in this class goes through
        this one call site."""
        try:
            response = self._client.models.generate_content(
                model=self._model_name, contents=contents
            )
            return (response.text or "").strip()
        except Exception as exc:  # network/auth/quota errors from the SDK
            log.exception("Gemini call failed")
            raise LLMGenerationError(str(exc)) from exc

    def generate_regulation_answer(self, query: str, destination_country: str, context: str) -> dict:
        """Structured, single-medicine answer grounded in `context`
        (pre-formatted regulation rows). Returns parsed JSON."""
        prompt = f"""You are MediSafe AI, a travel medicine regulation assistant.

The traveler is asking about the medicine: "{query}"
Destination country: "{destination_country}"

Answer ONLY using the provided context below. Do not hallucinate or
assume anything that is not explicitly stated in the context. Pick
the single entry in the context whose Country matches the destination
and whose Medicine/Brand/Generic best matches the query.

If no entry in the context matches both the medicine and the
destination country, return this JSON exactly:

{{
    "found": false,
    "message": "Medicine not found in database for {destination_country}."
}}

Otherwise return ONLY valid JSON, no markdown formatting, in this
exact shape:

{{
    "found": true,
    "medicine": "",
    "country": "",
    "approval_status": "",
    "restriction": "",
    "reason": "",
    "recommendation": "",
    "approved_alternative": "",
    "source": ""
}}

Rules:
- Never invent a status, source, or alternative that isn't in the
  matching context entry.
- Keep "reason" and "recommendation" short and jargon-free.

Context:
{context}

Question:
Is "{query}" allowed in "{destination_country}", and if not, why, and
what is a safe alternative?"""

        return self._parse_json(self.generate(prompt))

    def generate_chat_answer(self, question: str, context: str) -> str:
        prompt = f"""You are MediSafe AI, a friendly travel medicine regulation assistant.
This is one turn in an ongoing chat — the user has already been
greeted and knows who you are. Do NOT introduce or re-introduce
yourself, do NOT say things like "Hi, I'm MediSafe AI" or any other
greeting, and do NOT restate your role. Respond only with the
answer itself, starting directly with the relevant information.

Answer the traveler's question using ONLY the context below. If the
context doesn't contain enough information to answer confidently, say
so plainly and suggest checking with a local pharmacist or embassy.
Keep the answer short, clear, and free of medical or legal jargon.

Context:
{context}

Question:
{question}"""
        return self.generate(prompt)

    def generate_followup_answer(self, medicine_context: dict, question: str) -> str:
        prompt = f"""You are MediSafe AI's "Know More" assistant.
This is one turn in an ongoing chat — the user has already been
greeted and knows who you are. Do NOT introduce or re-introduce
yourself, do NOT say things like "Hi, I'm MediSafe AI" or any other
greeting, and do NOT restate your role. Respond only with the
answer itself, starting directly with the relevant information.

Here is what we already know about this medicine, from our database:
{json.dumps(medicine_context, indent=2)}

The traveler is now asking a follow-up question:
"{question}"

Answer simply and clearly, in 2-4 short sentences, using only the
information above. Avoid medical or legal jargon.

If the answer isn't contained in the information above, say you
don't have that detail and suggest they check with a local
pharmacist or embassy.

Respond with plain text only, not JSON."""
        return self.generate(prompt)

    @staticmethod
    def _parse_json(text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            log.warning("Gemini returned non-JSON output: %.200s", cleaned)
            return {"found": False, "message": "The AI response could not be parsed."}
