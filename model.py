import dotenv
from langchain.chat_models import init_chat_model
import os


dotenv.load_dotenv()

llm = init_chat_model(
    model=os.getenv("OPENAI_API_NAME"),
    model_provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
    temperature=0.0,
    model_kwargs={
        "extra_body": {"thinking": {"type": "enabled"}}
    }
)
