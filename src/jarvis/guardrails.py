'''
    The guardrail layer. check_input runs before the agent is invoked, so a blocked message never reaches the LLM or any tool.
    Tool-call and output guardrails come later, once approvals and the API exist.
'''
from jarvis.llm_utils import client
from jarvis.logger import setup_logger

logger = setup_logger('guardrails')

MAX_INPUT_CHARS = 4000


def check_input(text: str) -> str | None:
    '''
        Returns why the message is blocked, or None when it may go to the agent.
        Rules first (empty, too long), then OpenAI's moderation endpoint (free) for harmful content.
    '''
    if not text.strip():
        return "Empty message."
    if len(text) > MAX_INPUT_CHARS:
        return f"Message too long ({len(text)} chars, limit {MAX_INPUT_CHARS})."
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
