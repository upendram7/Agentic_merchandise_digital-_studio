from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

def chat_model(temperature: float = 0):
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for LLM-backed workflow execution")
    return ChatOpenAI(model=settings.openai_model, temperature=temperature, api_key=settings.openai_api_key)

def embeddings():
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for embedding generation")
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), retry=retry_if_exception_type(Exception), reraise=True)
def invoke_structured(model, prompt):
    return model.invoke(prompt)
