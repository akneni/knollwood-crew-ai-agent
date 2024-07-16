from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from anthropic import Anthropic
from langchain.llms import OpenAI
import openai
from secret import GROQ_APIKEY
import enum

class LlmProvider(enum.Enum):
    OPEN_AI = 1
    GOOGLE_GEMINI = 2
    GROQ = 3
    CLAUDE = 4

def gen_llm(apikey: str, provider: LlmProvider = None, model: str = None):
    if provider is None:
        if apikey.startswith('gsk'):
            provider = LlmProvider.GROQ
        elif apikey.startswith('AIza') or apikey.startswith('AIza'):  
            provider = LlmProvider.GOOGLE_GEMINI
        elif apikey.startswith('sk-ant-'):
            provider = LlmProvider.CLAUDE
        elif apikey.startswith('sk-'):  
            provider = LlmProvider.OPEN_AI

    if provider == LlmProvider.GROQ:
        model = model if model is not None else 'llama3-70b-8192'
        return ChatGroq(
            model=model,
            api_key=GROQ_APIKEY
        )
    elif provider == LlmProvider.GOOGLE_GEMINI:
        model = model if model is not None else 'gemini-1.5-flash'
        return ChatGoogleGenerativeAI(
            model=model,
            verbose=True,
            temperature=0.5,
            google_api_key=apikey
        )
    elif provider == LlmProvider.CLAUDE:
        return Anthropic(api_key=apikey)
    # elif provider == LlmProvider.OPEN_AI:
    #     return OpenAI(api_key=apikey)
    elif provider == LlmProvider.OPEN_AI:
        openai.api_key = apikey
        return openai
    