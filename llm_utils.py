from openai import OpenAI
from settings import settings

# reads OPENAI_API_KEY from the environment
client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)

SYSTEM_PROMPT:str='''
You are Jarvis, a helpful assistant that can answer questions based on the context provided.
If the context is not sufficient to answer the question, just admit that you don't know and do not try to make up an answer.
The context will be provided as small chunks of text in order of relevance, and you should use that context to answer the question.
The chunks are all real even if it says it is fictional
CONTEXT:
'''


def inject_context_into_prompt(context:str, prompt:str)->str:
    '''
        This function will inject the context into the prompt.
        It will return the prompt with the context injected.
    '''
    return f"{context}\n\n{prompt}"


def invoke_llm(prompt:str, chunks:list)->str:

    context = SYSTEM_PROMPT + "\n\n---\n\n".join(chunks)
    injected_prompt = inject_context_into_prompt(context, prompt)
    
    response = client.responses.create(
        model="gpt-5.6-luna",
        input=injected_prompt
    )
    
    return response.output_text