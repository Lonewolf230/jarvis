'''
    The guardrail layer. check_input runs before the agent is invoked, so a blocked message never reaches the LLM or any tool.
    Tool-call and output guardrails come later, once approvals and the API exist.
'''
import math
import re
import uuid
from collections import Counter

from jarvis.llm_utils import client
from jarvis.logger import setup_logger

logger = setup_logger('guardrails')

MAX_INPUT_CHARS = 4000

# a random marker placed in the system prompt; a reply that holds it is a prompt leak. New per process.
CANARY = f"canary-{uuid.uuid4().hex[:12]}"

KNOWN_KEYS = re.compile(r"sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36,}|xox[abp]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}|eyJ[\w-]+\.[\w-]+\.[\w-]+")
LABELLED_SECRET = re.compile(r"(?i)\b(?:api[_-]?key|secret|token|passw(?:or)?d|bearer|authorization)\b[\s:=\"']+([^\s\"']{8,})")
# no "/" or "-": they split note paths and slugs into short words; dashed provider keys are caught by KNOWN_KEYS
TOKEN_LIKE = re.compile(r"[A-Za-z0-9+_=]{24,}")


def _entropy(s: str) -> float:
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in Counter(s).values())


REDACTED = "[REDACTED]"


def redact(text: str) -> str:
    '''
        Replaces anything that looks like a credential with [REDACTED]: a known key format, the value after a
        secret-like label, or a long random-looking token. The rest of the text is kept.
    '''
    text = KNOWN_KEYS.sub(REDACTED, text)
    text = LABELLED_SECRET.sub(lambda m: m.group(0).replace(m.group(1), REDACTED), text)
    # shortcut: 4.0 bits/char is a guess that flags random keys, not words; tune on your own false positives
    # a digit is required: note paths like study/rag/chunking-strategies are long and varied but hold no digits
    return TOKEN_LIKE.sub(lambda m: REDACTED if re.search(r"\d", m.group(0)) and _entropy(m.group(0)) > 4.0 else m.group(0), text)


def has_secret(text: str) -> bool:
    '''
        True if the text looks like it holds a credential. See redact for what counts.
    '''
    return redact(text) != text


def check_input(text: str) -> str | None:
    '''
        Returns why the message is blocked, or None when it may go to the agent.
        Rules first (empty, too long, secrets), then OpenAI's moderation endpoint (free) for harmful content.
    '''
    if not text.strip():
        return "Empty message."
    if len(text) > MAX_INPUT_CHARS:
        return f"Message too long ({len(text)} chars, limit {MAX_INPUT_CHARS})."
    if has_secret(text):
        return "Message looks like it contains a secret or API key. Remove it and try again."
    try:
        result = client.moderations.create(model="omni-moderation-latest", input=text).results[0]
    except Exception as e:
        # fails closed: if the check cannot run, nothing goes to the agent
        logger.error(f"Moderation call failed: {e}")
        return "Could not check the message, try again."
    if result.flagged:
        flagged = [name for name, hit in result.categories.model_dump().items() if hit]
        logger.info(f"Blocked input, categories: {flagged}")
        return f"Message blocked by content policy ({', '.join(flagged)})."
    return None


def check_output(text: str, system_prompt: str) -> str | None:
    '''
        Returns why a reply must not be shown, or None. Catches the canary, a verbatim line of the system prompt,
        and anything that looks like a secret. Paraphrased or translated prompt text gets through.
    '''
    if CANARY in text or any(len(line.strip()) >= 40 and line.strip() in text for line in system_prompt.splitlines()):
        logger.warning("Blocked reply: system prompt leak")
        return "system prompt leak"
    if has_secret(text):
        logger.warning("Blocked reply: looks like a secret")
        return "possible secret"
    return None
