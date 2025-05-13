import os
import argparse
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
from openai import OpenAI
import logging
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ToolRAG:
    """A class to perform document retrieval from Qdrant based on a query."""

    DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
    # DEFAULT_GENERATION_MODEL = "gpt-3.5-turbo" # No longer needed for generation
    DEFAULT_PAYLOAD_TEXT_FIELD = "description" # Field containing the tool description
    DEFAULT_PAYLOAD_NAME_FIELD = "name" # ASSUMPTION: Field containing the tool name
    DEFAULT_SEARCH_LIMIT = 5
    DEFAULT_VECTOR_SIZE = 1536 # For text-embedding-3-small

    def __init__(
        self,
        openai_api_key: str,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        qdrant_collection_name: str = "mcp_servers",
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        payload_text_field: str = DEFAULT_PAYLOAD_TEXT_FIELD,
        payload_name_field: str = DEFAULT_PAYLOAD_NAME_FIELD, # Added name field
        search_limit: int = DEFAULT_SEARCH_LIMIT,
        vector_size: int = DEFAULT_VECTOR_SIZE
    ):
        """Initializes the ToolRAG class.

        Args:
            openai_api_key: The API key for OpenAI services.
            qdrant_host: Hostname or IP address of the Qdrant server.
            qdrant_port: Port number for the Qdrant server.
            qdrant_collection_name: Name of the Qdrant collection to use.
            embedding_model: The OpenAI model to use for generating embeddings.
            payload_text_field: The field name in the Qdrant payload containing the description text.
            payload_name_field: The field name in the Qdrant payload containing the tool's name.
            search_limit: The maximum number of documents to retrieve from Qdrant.
            vector_size: The expected dimension of the embeddings (used by the collection).
        """
        if not openai_api_key:
            raise ValueError("OpenAI API key must be provided.")

        self.openai_api_key = openai_api_key
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.qdrant_collection_name = qdrant_collection_name
        self.embedding_model = embedding_model
        # self.generation_model = generation_model # No longer needed
        self.payload_text_field = payload_text_field
        self.payload_name_field = payload_name_field
        self.search_limit = search_limit
        self.vector_size = vector_size

        self.openai_client = self._initialize_openai_client()
        self.qdrant_client = self._initialize_qdrant_client()

    def _initialize_openai_client(self) -> OpenAI:
        """Initializes and returns an OpenAI client."""
        logger.info("Initializing OpenAI client.")
        try:
            client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized successfully.")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def _initialize_qdrant_client(self) -> QdrantClient:
        """Initializes and returns a Qdrant client."""
        logger.info(f"Connecting to Qdrant at {self.qdrant_host}:{self.qdrant_port}")
        try:
            client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port, timeout=10.0)
            client.get_collection(collection_name=self.qdrant_collection_name)
            logger.info(f"Successfully connected to Qdrant and found collection '{self.qdrant_collection_name}'.")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant or find collection '{self.qdrant_collection_name}': {e}")
            raise

    def _get_embedding(self, text: str) -> list[float]:
        """Generates an embedding for the given text using the instance's OpenAI client."""
        logger.debug(f"Generating embedding for text: '{text[:50]}...'")
        try:
            response = self.openai_client.embeddings.create(input=[text], model=self.embedding_model)
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)}.")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    # Removed _generate_response method as it's no longer used for LLM call

    def retrieve(self, query: str) -> list[PointStruct]:
        """Performs query embedding and searches Qdrant for relevant documents.

        Args:
            query: The user query string.

        Returns:
            A list of Qdrant PointStruct objects representing the search results,
            ordered by relevance.
        """
        logger.info(f"Starting retrieval for query: '{query}'")
        try:
            # 1. Generate query embedding
            query_embedding = self._get_embedding(query)

            # 2. Search Qdrant
            logger.info(f"Searching collection '{self.qdrant_collection_name}' in Qdrant.")
            search_result = self.qdrant_client.search(
                collection_name=self.qdrant_collection_name,
                query_vector=query_embedding,
                limit=self.search_limit,
                with_payload=True,
                score_threshold=0.01 # Optional: Add a score threshold if desired
            )
            logger.info(f"Found {len(search_result)} results in Qdrant.")

            logger.info(f"Retrieval finished successfully for query: '{query}'")
            return search_result
        except Exception as e:
            logger.error(f"An error occurred during the retrieval process: {e}")
            raise

    def ask(self, query: str) -> str:
        """Retrieves relevant tools and explains their relevance in natural language.

        Args:
            query: The user query string.

        Returns:
            A natural language string explaining the relevance of retrieved tools.
        """
        search_results = self.retrieve(query)

        if not search_results:
            return f"I couldn't find any tools relevant to your query: '{query}'"

        explanation_parts = [f"Based on your query '{query}', here are the most relevant tools I found:"]

        for i, result in enumerate(search_results):
            payload = result.payload
            if not payload:
                logger.warning(f"Result {i+1} has no payload.")
                continue

            tool_name = payload.get(self.payload_name_field, f"Tool {result.id}") # Fallback to ID if name field missing
            tool_desc = payload.get(self.payload_text_field, "No description available.")
            score = result.score # Qdrant score indicates similarity

            explanation_parts.append(
                f"{i+1}. {tool_name} (Score: {score:.4f}): Seems relevant because its description mentions: \"{tool_desc[:150]}...\""
            )

        if len(explanation_parts) == 1: # Only the initial message means no valid tools found
             return f"I found some potential matches for '{query}', but couldn't extract tool details."

        return "\n".join(explanation_parts)


# --- Main Execution (Example Usage) ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve relevant tools from Qdrant based on a query and explain relevance.")
    parser.add_argument("query", type=str, help="The search query.")
    parser.add_argument("--openai-key", type=str, default=os.environ.get("OPENAI_API_KEY"), help="OpenAI API Key")
    parser.add_argument("--qdrant-host", type=str, default=os.environ.get("QDRANT_HOST", "localhost"), help="Qdrant host")
    parser.add_argument("--qdrant-port", type=int, default=int(os.environ.get("QDRANT_PORT", 6333)), help="Qdrant port")
    parser.add_argument("--collection", type=str, default=os.environ.get("QDRANT_COLLECTION_NAME", "mcp_servers"), help="Qdrant collection name")
    parser.add_argument("--name-field", type=str, default=ToolRAG.DEFAULT_PAYLOAD_NAME_FIELD, help="Payload field containing tool name")
    parser.add_argument("--desc-field", type=str, default=ToolRAG.DEFAULT_PAYLOAD_TEXT_FIELD, help="Payload field containing tool description")

    args = parser.parse_args()

    if not args.openai_key:
        print("Error: OpenAI API Key is required. Set --openai-key or OPENAI_API_KEY environment variable.")
        exit(1)

    query = args.query
    logger.info(f"Executing ToolRAG script for query: '{query}'")

    try:
        # Initialize the RAG tool
        rag_tool = ToolRAG(
            openai_api_key=args.openai_key,
            qdrant_host=args.qdrant_host,
            qdrant_port=args.qdrant_port,
            qdrant_collection_name=args.collection,
            payload_name_field=args.name_field,
            payload_text_field=args.desc_field
        )

        # Perform ask
        explanation = rag_tool.ask(query)

        # Print explanation
        print("\n--- Tool Relevance Explanation ---")
        print(explanation)
        print("--------------------------------")

    except Exception as e:
        logger.error(f"An error occurred during the script execution: {e}")
        print(f"\nError: Could not complete the search. Reason: {e}")
    finally:
        logger.info("ToolRAG script execution finished.")
