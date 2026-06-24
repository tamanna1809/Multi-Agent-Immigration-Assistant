import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.tools import tool

_vectorstore = None


def _load_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    rules_path = os.path.join(os.path.dirname(__file__), "..", "data", "immigration_rules.txt")
    with open(rules_path, "r") as f:
        content = f.read()

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    chunks = splitter.create_documents([content])

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    _vectorstore = FAISS.from_documents(chunks, embeddings)
    return _vectorstore


@tool
def search_immigration_rules(query: str) -> str:
    """Search immigration rules, visa requirements, eligibility criteria, and document checklists from the knowledge base."""
    vs = _load_vectorstore()
    docs = vs.similarity_search(query, k=4)
    return "\n\n---\n\n".join([d.page_content for d in docs])
