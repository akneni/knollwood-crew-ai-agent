from langchain.llms.base import LLM
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from anthropic import Anthropic
import openai
from secret import GROQ_APIKEY
import enum
from typing import Any, List, Optional
import shelve
from docx import Document
import os
import shutil

class LlmProvider(enum.Enum):
    OPEN_AI = 1
    GOOGLE_GEMINI = 2
    GROQ = 3
    CLAUDE = 4

def gen_llm(apikey: str, provider: Optional[LlmProvider] = None, model: str = None):
    if provider is None:
        if apikey.startswith('gsk'):
            provider = LlmProvider.GROQ
        elif apikey.startswith('AIza'):  
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
    elif provider == LlmProvider.OPEN_AI:
        openai.api_key = apikey
        return openai

def build_word_doc(output_dir):
    screening_mem_out = os.path.join(output_dir, 'screening-memo.docx')
    with shelve.open(os.path.join(output_dir, "shelve-db/db")) as db:
        shutil.copyfile('./templates/TEMPLATE FUND Screening Memo.docx', screening_mem_out)

        d = {k:format_section(v.split('<[SEP]>')) for k,v in db.items()}
        find_replace_in_document(
            "./templates/TEMPLATE FUND Screening Memo.docx",
            d,
            "./outputs/output.docx",
        )

def format_section(text: list[str]) -> str:
    return '\n'.join(text)

def find_replace_in_document(doc_path, replacements, output_path):
    doc = Document(doc_path)
    
    for paragraph in doc.paragraphs:
        for old_text, new_text in replacements.items():
            if old_text in paragraph.text:
                paragraph.text = paragraph.text.replace(old_text, new_text)
        
    doc.save(output_path)