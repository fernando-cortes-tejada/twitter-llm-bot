import os
from langchain.indexes import VectorstoreIndexCreator
from langchain.chat_models import ChatOpenAI

from langchain.document_loaders import WebBaseLoader
from src.langchain.entities import QUERY

from dotenv import load_dotenv

# in order to load the OPENAI_API_KEY
load_dotenv()


# use the langchaing doc answering system
def docs_answering(url: str, query: str = QUERY) -> str:
    query = query.replace("{url}", url)

    # read the url and gather the article information
    loader = WebBaseLoader(url)
    # create the index
    index = VectorstoreIndexCreator().from_loaders([loader])

    # create the chat model
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    # query the index
    result = index.query(question=query, llm=llm)

    return result
