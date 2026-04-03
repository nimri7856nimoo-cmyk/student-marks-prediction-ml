import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools import tool

FAISS_PATH = "faiss_index"
DOCS_PATH = "documents"

def load_documents():
    print(" Loading all documents...")
    loader = DirectoryLoader(
        DOCS_PATH,
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    documents = loader.load()
    print(f" Loaded {len(documents)} documents!")
    return documents

def create_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

def setup_vectorstore():
    embeddings = create_embeddings()

    if os.path.exists(FAISS_PATH):
        print(" Loading existing embeddings from disk...")
        vectorstore = FAISS.load_local(
            FAISS_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        print(" Embeddings loaded!")
    else:
        documents = load_documents()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = splitter.split_documents(documents)
        print(f" Created {len(chunks)} chunks!")
        print(" Creating embeddings...")
        vectorstore = FAISS.from_documents(chunks, embeddings)
        vectorstore.save_local(FAISS_PATH)
        print(f" Embeddings saved to {FAISS_PATH}!")

    return vectorstore.as_retriever(search_kwargs={"k": 3})

def create_rag_tool(retriever):
    @tool
    def search_knowledge_base(query: str) -> str:
        """Search company documents for HR policies, products, company info."""
        docs = retriever.invoke(query)
        if docs:
            results = []
            for doc in docs:
                source = doc.metadata.get("source", "Unknown")
                results.append(f"Source: {source}\n{doc.page_content}")
            return "\n\n---\n\n".join(results)
        return "No relevant information found."
    return search_knowledge_base