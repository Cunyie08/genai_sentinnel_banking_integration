"""
Embedding Module
================

Enterprise-grade embedding engine for semantic vector generation.

This module converts natural language text into dense numerical vectors
(embeddings) that capture semantic meaning rather than just keyword overlap.

Core Responsibility
-------------------
Transform text into 768-dimensional vectors using a pre-trained
SentenceTransformer model.

Example Transformation
----------------------

    "Card was declined"
        ↓
    [0.23, -0.41, 0.87, ..., 0.15]   (768 floating-point numbers)

These vectors allow similarity comparison using cosine distance.

Operational Usage
-----------------

1. During ingestion:
   - Policy and FAQ chunks are embedded before being stored in ChromaDB.

2. During retrieval:
   - User queries are embedded and compared against stored vectors.

CRITICAL REQUIREMENT
--------------------
This module MUST use the same model as:

    ChromaDBConfig.EMBEDDING_MODEL

Currently:
    all-mpnet-base-v2

If ingestion and retrieval use different models,
semantic similarity will fail.

Model Selection Rationale
--------------------------
all-mpnet-base-v2 was chosen because:

• 768 dimensions (higher semantic resolution than 384-d MiniLM)
• Strong performance on enterprise and compliance datasets
• Better distinction of subtle policy nuance
• Stable cosine similarity performance on banking-domain text

This module is optimized for production RAG systems in financial domains.
"""

from typing import List  # Provides type hinting for vector outputs
import logging  # Standard Python logging for observability
from sentence_transformers import SentenceTransformer  
from pathlib import Path
from functools import lru_cache
# Pretrained transformer-based sentence embedding models


# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(level=logging.INFO)
# Sets default logging level to INFO for operational visibility

logger = logging.getLogger(__name__)
# Module-specific logger for precise debugging and tracing

_ENGINE_INSTANCE = None
# =============================================================================
# Embedding Engine
# =============================================================================

class EmbeddingEngine:
    """
    Semantic vector generation engine for RAG systems.

    High-Level Explanation
    ----------------------
    Converts human-readable text into a numerical vector representation
    that captures semantic meaning.

    Think of it as generating a "meaning fingerprint."

    Similar meaning → Similar vector

    Example:

        "My card was declined"
        "Payment was rejected"

        Even though wording differs, semantic meaning overlaps.
        Cosine similarity between vectors will be high.

    Technical Specifications
    ------------------------
    Model:        all-mpnet-base-v2
    Dimensions:   768
    Model Size:   ~420MB
    CPU Speed:    ~500 texts/second
    Similarity:   Cosine similarity

    Production Constraint
    ----------------------
    MUST remain synchronized with ChromaDBConfig.EMBEDDING_MODEL.
    """

    MODEL_NAME = "all-mpnet-base-v2"
    # Centralized embedding model identifier

    EMBEDDING_DIMENSION = 768
    # Expected vector size for this model


    def __init__(self):
        """
        Initialize embedding engine.

        Loads pretrained transformer model into memory.

        First load:
            ~3 seconds
            ~420MB RAM

        After loading:
            Fast inference on CPU.

        Raises:
            Exception if model fails to load.
        """
        global _ENGINE_INSTANCE
        if _ENGINE_INSTANCE is not None:
            # Reuse already-loaded model
            self.model = _ENGINE_INSTANCE.model
            logger.info("Reusing cached embedding model")
            return

        logger.info(f"Loading embedding model: {self.MODEL_NAME}")
        try:
            cache_dir = str(Path(__file__).parent.parent.parent / "models")
            self.model = SentenceTransformer(self.MODEL_NAME, cache_folder=cache_dir)
            _ENGINE_INSTANCE = self
            logger.info(f"  Embedding model loaded: {self.MODEL_NAME}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise


    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string into a semantic vector.

        Args:
            text:
                Raw natural language string.

                Example:
                    "My card was declined at the ATM"

        Returns:
            List[float]
                768-dimensional semantic vector.

        Behavior:
            - Uses model.encode()
            - Converts NumPy output to Python list
            - Raises exception if embedding fails
        """

        try:
            # Convert text into NumPy embedding
            embedding = self.model.encode(
                text,
                convert_to_numpy=True
            )

            # Convert NumPy array to Python list for JSON/storage compatibility
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise


    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts simultaneously (vectorized inference).

        This is significantly faster than embedding one-by-one.

        Args:
            texts:
                List of input strings.

        Returns:
            List of vectors:
                [[768 floats], [768 floats], ...]

        Performance Comparison:
            100 texts individually: ~200ms
            100 texts batch:        ~35ms

        show_progress_bar:
            Enabled only for large batches (>100)
            Prevents console noise for small inputs.
        """

        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100,
            )

            # Convert NumPy 2D array to nested Python list
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            raise


    def get_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.

        Cosine Similarity Formula:
            (A · B) / (||A|| * ||B||)

        Output Range:
            1.0 → Identical meaning
            ~0.8 → Strong similarity
            ~0.5 → Partial overlap
            ~0.1 → Unrelated

        Args:
            text1: First text
            text2: Second text

        Returns:
            Float similarity score
        """

        from numpy import dot
        # Dot product operation

        from numpy.linalg import norm
        # Vector magnitude calculation

        # Generate embeddings for both texts
        vec1 = self.embed_text(text1)
        vec2 = self.embed_text(text2)

        # Compute cosine similarity
        return float(dot(vec1, vec2) / (norm(vec1) * norm(vec2)))


    def get_model_info(self) -> dict:
        """
        Retrieve metadata about loaded embedding model.

        Returns:
            Dictionary containing:
                - model_name
                - embedding dimension
                - max sequence length
                - description

        Useful for:
            - System introspection
            - Debug logging
            - Admin dashboards
        """

        return {
            "model_name": self.MODEL_NAME,
            "dimensions": self.EMBEDDING_DIMENSION,
            "max_sequence_length": self.model.max_seq_length,
            "description": "High-accuracy sentence embeddings for banking RAG",
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_embedding_engine() -> EmbeddingEngine:
    """
    Factory helper for creating embedding engine instance.

    Recommended for:
        Application startup initialization.

    Returns:
        Ready-to-use EmbeddingEngine instance.
    """
    return EmbeddingEngine()


def embed_single(text: str) -> List[float]:
    """
    Quick utility for embedding a single text.

    WARNING:
        Loads model every call (slow).
        Intended only for testing or CLI usage.

    For production:
        Create one EmbeddingEngine and reuse it.
    """
    return EmbeddingEngine().embed_text(text)


# =============================================================================
# Demo / Manual Test Runner
# =============================================================================

def demo():
    """
    Demonstration of embedding engine functionality.

    Shows:
        - Model metadata
        - Single embedding example
        - Semantic similarity examples
        - Batch embedding performance

    Designed for CLI testing.
    """

    print("\n" + "=" * 70)
    print(" " * 20 + "EMBEDDING ENGINE DEMO")
    print("=" * 70 + "\n")

    engine = create_embedding_engine()

    print("Model Information:")
    for key, value in engine.get_model_info().items():
        print(f"  {key}: {value}")
    print()

    text = "My card was declined at Shoprite"
    vector = engine.embed_text(text)

    print(f"Single Embedding:")
    print(f"  Text:            '{text}'")
    print(f"  Vector length:   {len(vector)}")
    print(f"  First 5 values:  {[round(v, 4) for v in vector[:5]]}")
    print()

    print("Similarity Tests:")

    pairs = [
        ("Card was declined", "Payment was rejected"),
        ("Card was declined", "Weather is sunny"),
        ("Transfer failed", "Transaction not completed"),
        ("Fraud unauthorized", "Suspicious transaction I did not make"),
        ("Loan application", "Credit request for car purchase"),
    ]

    for t1, t2 in pairs:
        sim = engine.get_similarity(t1, t2)
        bar = "█" * int(sim * 20)
        print(f"  [{bar:<20}] {sim:.3f}  '{t1}' ↔ '{t2}'")
    print()

    import time

    texts = [f"Banking policy text example number {i}" for i in range(50)]

    start = time.time()

    vecs = engine.embed_batch(texts)

    elapsed = (time.time() - start) * 1000

    print(f"Batch Performance:")
    print(f"  {len(texts)} texts embedded in {elapsed:.1f}ms")
    print(f"  Output: {len(vecs)} vectors × {len(vecs[0])} dimensions")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    demo()