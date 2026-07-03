import os
import requests
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document

# ========================
# EMBEDDING MODEL
# ========================
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

CHROMA_PATH = "./chroma_db"

def get_vectorstore():
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

def load_stations_to_vectordb():
    try:
        response = requests.get(
            "http://127.0.0.1:8000/api/stations/list/",
            timeout=5
        )
        if response.status_code != 200:
            print("Could not fetch stations")
            return False

        data = response.json()
        stations = data.get("results", data)

        documents = []
        for station in stations:
            content = f"""
Station Name: {station.get('station_name', '')}
City: {station.get('city', '')}
Address: {station.get('address', '')}
Status: {station.get('status', '')}
Opening Time: {station.get('opening_time', '')}
Closing Time: {station.get('closing_time', '')}
            """.strip()

            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "station_id": station.get("id"),
                        "station_name": station.get("station_name"),
                        "city": station.get("city"),
                    }
                )
            )

        if not documents:
            print("No stations found")
            return False

        splitter = CharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        split_docs = splitter.split_documents(documents)

        vectorstore = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings,
            persist_directory=CHROMA_PATH
        )

        print(f"✅ Loaded {len(documents)} stations into ChromaDB")
        return True

    except Exception as e:
        print(f"Error loading stations: {e}")
        return False


def search_relevant_stations(query: str, k: int = 3) -> str:
    try:
        vectorstore = get_vectorstore()
        results = vectorstore.similarity_search(query, k=k)

        if not results:
            return ""

        context = "Relevant VoltStream Charging Stations:\n\n"
        for doc in results:
            context += doc.page_content + "\n\n"

        return context

    except Exception as e:
        print(f"Search error: {e}")
        return ""