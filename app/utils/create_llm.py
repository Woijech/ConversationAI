from app.settings import settings
from langchain_openai import ChatOpenAI
llm=ChatOpenAI(model='gpt-4o-mini',api_key=settings.get_llm_key())
