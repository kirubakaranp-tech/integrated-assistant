import os

from dotenv import load_dotenv

# read settings like OPENAI_API_KEY from the .env file
load_dotenv()

# Folder where Chroma saves its data. The tests change this to a temp folder.
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma")
COLLECTION_NAME = "documents"

# Chunk size in characters. 800 characters stays under the 256 token limit
# of the embedding model, so no text gets cut off when it is embedded.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

MAX_FILE_SIZE_MB = 20

# Chat
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TOP_K = 4  # how many chunks we give to the model
# Chunks further away than this are not relevant to the question.
# (Chroma's default distance: 0 = same meaning, 2 = nothing in common.)
MAX_DISTANCE = 1.4
MEMORY_SIZE = 5  # messages kept per session
