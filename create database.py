from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.vectorstores.chroma import Chroma
import os
import shutil
import json
from langchain.embeddings import VoyageEmbeddings
from dotenv import load_dotenv

#Set paths
CHROMA_ADVICE_PATH = "chroma\\advice"
ADVICE_DATA_PATHS = ["data\\aratohu"]
LINKS_FILE_PATH = "data\source_links.json"

CHROMA_TRIBUNAL_PATH = "chroma\\tribunal"
TRIBUNAL_DATA_PATHS = ["data\\tribunal"]

load_dotenv()

def load_documents(DATA_PATHS):
    documents = []

    for path in DATA_PATHS:
        loader = DirectoryLoader(path, glob="*.md")
        temp_documents = loader.load()
        documents = documents + temp_documents

    return documents

def split_text(documents: list[Document]):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )

    chunks = text_splitter.split_documents(documents)

    with open(LINKS_FILE_PATH , 'r') as file:
        data_dict = json.load(file)

    for chunk in chunks:
        file_name_with_extension = os.path.basename(chunk.metadata['source'])
        file_name_without_extension, extension = os.path.splitext(file_name_with_extension)

        link = data_dict[file_name_without_extension]

        chunk.metadata['link'] = link
        
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    return chunks

def save_to_chroma(chunks: list[Document], CHROMA_PATH):
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    #embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    embedding_function = VoyageEmbeddings()

    # Create a new DB from the documents.
    db = Chroma.from_documents(
        chunks, embedding_function, persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")

def generate_data_store(DATA_PATHS, CHROMA_PATH):
    documents = load_documents(DATA_PATHS)
    chunks = split_text(documents)
    save_to_chroma(chunks, CHROMA_PATH)

generate_data_store(ADVICE_DATA_PATHS, CHROMA_ADVICE_PATH)
#generate_data_store(TRIBUNAL_DATA_PATHS, CHROMA_TRIBUNAL_PATH)