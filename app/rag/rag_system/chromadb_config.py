"""
ChromaDB Configuration Module
==============================

Production-grade configuration and orchestration layer for ChromaDB,
serving as the single source of truth for vector database configuration,
collection lifecycle management, embedding model consistency, and
document routing metadata.

This module ensures that all ingestion and retrieval pipelines use the
same embedding model, storage directory, and collection configuration,
which is critical for semantic search correctness.

Primary Responsibilities
------------------------
1. Persistent Client Initialization
   Creates and manages ChromaDB persistent client instances that survive
   process restarts and ensure long-term storage durability.

2. Collection Lifecycle Management
   Handles creation, retrieval, and resetting of collections while
   enforcing consistent embedding configuration.

3. Embedding Model Configuration
   Provides a centralized embedding function using a module-level
   singleton — loaded once per process, reused everywhere. This
   eliminates the 5–15s cold-start penalty on every run.

4. Document Routing via DOCUMENT_REGISTRY
   Defines metadata that controls how documents are categorized,
   routed, filtered, and retrieved by downstream agents.

5. Multi-Agent Support
   Enables agent-specific retrieval for:
      - Dispatcher Agent (Complaint routing)
      - Sentinel Agent (Fraud detection and risk analysis)
      - Trajectory Agent (Product recommendation logic)
      - Customer Agent (Customer-facing FAQ retrieval)

Architecture Flow
-----------------

    Document Generator / Source Files
               ↓
    DOCUMENT_REGISTRY (routing metadata)
               ↓
    DocumentIngester (chunking + tagging)
               ↓
    ChromaDBConfig (embedding + collections)
               ↓
    ChromaDB Collections (vector storage)
               ↓
    RetrievalEngine (semantic search)
               ↓
    RAGQueryEngine (context assembly)
               ↓
    AI Agents (Dispatcher, Sentinel, Trajectory, Customer)

Embedding Model
---------------
Model: all-mpnet-base-v2

Chosen because:
- High semantic accuracy
- 768-dimensional vectors
- Strong performance on compliance, policy, and fraud datasets
- Industry standard for enterprise-grade RAG pipelines

IMPORTANT: This model name is the single source of truth for the entire
pipeline. retrieval.py imports EMBEDDING_MODEL from this module to
guarantee ingestion and retrieval always use the same model. If they
differ, ChromaDB will embed queries in a different vector space than
documents, silently destroying similarity scores.

Fixes in this version (v2):
  1. Singleton embedding function — module-level, not instance-level.
       The previous implementation cached on self._embedding_fn, but
       initialize_chromadb() creates a new ChromaDBConfig() each call,
       so the cache was never reused. The model loaded fresh every run.
       Fixed with a module-level _embedding_fn_instance + threading.Lock
       (double-checked locking, same pattern as retrieval.py).
  2. EMBEDDING_MODEL exported at module level.
       retrieval.py now imports EMBEDDING_MODEL from here instead of
       defining its own string. One name, one place — no drift possible.
  3. Model name mismatch corrected.
       chromadb_config.py used "all-mpnet-base-v2" while retrieval.py
       had "all-MiniLM-L6-v2". This caused ingestion and retrieval to
       use different vector spaces, silently corrupting similarity scores.
       Both now use "all-mpnet-base-v2" (this file is the authority).
  4. initialize_chromadb() made into a cached singleton.
       Previously returned a fresh ChromaDBConfig + client on every call.
       Now returns the same (client, config) pair for the process lifetime,
       eliminating repeated collection loading and connection setup.
  5. logger.info for collection get/create demoted to logger.debug.
       These fire on every RetrievalEngine.__init__ call — i.e. every
       test run. Demoted so production console stays clean.
  6. Startup INFO logs (model loaded, persistence dir) retained as-is.

Author: AI Engineer 2
Date: February 2026
"""

# =============================================================================
# Imports
# =============================================================================

import chromadb
import logging
import os
import threading
from chromadb.api import ClientAPI
from chromadb.utils import embedding_functions
from chromadb.config import Settings
from pathlib import Path
from typing import Optional, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# Embedding Model — Single Source of Truth
# =============================================================================
# This is the ONLY place the embedding model name is defined.
# retrieval.py imports this constant instead of defining its own string.
# If ingestion and retrieval use different models, ChromaDB embeds queries
# in a different vector space than documents — similarity scores become
# meaningless and routing silently breaks.
#
# To change the model for the whole pipeline, change it HERE only.

EMBEDDING_MODEL = "all-mpnet-base-v2"

# =============================================================================
# Embedding Function Singleton
# =============================================================================
# The HuggingFace model takes 5–15s to load. The previous implementation
# cached on self._embedding_fn (instance-level), but initialize_chromadb()
# creates a new ChromaDBConfig() on each call, so the cache was never
# reused — the model loaded fresh on every run, every test, every query.
#
# The fix: module-level singleton with double-checked locking.
# First call loads the model once. All subsequent calls return instantly.
# Thread-safe: two threads racing to call get_embedding_function() will
# not both load the model — only one will, the other waits and reuses.

_embedding_fn_instance = None
_embedding_fn_lock     = threading.Lock()

# Models directory — cached locally to avoid repeated HuggingFace downloads
_MODELS_DIR = Path(__file__).parent.parent.parent / "models"


def get_embedding_function():
    """
    Return the shared embedding function, loading it on first call only.

    This is the single accessor used by both ChromaDBConfig (ingestion)
    and RetrievalEngine (retrieval) — guaranteeing model consistency.

    Thread-safe via double-checked locking. Lazy: importing this module
    does not trigger a model download.

    Returns:
        SentenceTransformerEmbeddingFunction (module-level singleton)
    """
    global _embedding_fn_instance

    # Fast path — already loaded, return immediately without locking
    if _embedding_fn_instance is not None:
        return _embedding_fn_instance

    # Slow path — acquire lock and load
    with _embedding_fn_lock:
        # Re-check inside the lock: another thread may have loaded while
        # we were waiting
        if _embedding_fn_instance is not None:
            return _embedding_fn_instance

        logger.info(
            f"Loading embedding model '{EMBEDDING_MODEL}' — "
            f"one-time startup cost. All subsequent calls return instantly."
        )
        _models_dir = Path(__file__).parent.parent.parent / "models"
        _models_dir.mkdir(parents=True, exist_ok=True)

        # Suppress HuggingFace version-check HTTP noise and telemetry logs.
        # sentence-transformers hits HuggingFace on every load to check for
        # model updates even when the model is fully cached locally. This
        # adds ~30s of HEAD requests with no benefit in production.
        #
        # HF_HUB_OFFLINE=1       — skip all HF network calls, use local cache
        # TRANSFORMERS_OFFLINE=1  — same for transformers library
        # TOKENIZERS_PARALLELISM=false — suppress fork warning from tokenizers
        #
        # These are process-scoped env vars set before the library loads.
        # They are not written to disk. Set them in your .env file to make
        # them permanent:
        #
        #   HF_HUB_OFFLINE=1
        #   TRANSFORMERS_OFFLINE=1
        #   TOKENIZERS_PARALLELISM=false
        #   HF_TOKEN=your_token_here   ← also silences the rate-limit warning
        import os as _os
        _os.environ.setdefault("HF_HUB_OFFLINE",          "1")
        _os.environ.setdefault("TRANSFORMERS_OFFLINE",     "1")
        _os.environ.setdefault("TOKENIZERS_PARALLELISM",   "false")

        # Disable tqdm progress bars from sentence-transformers.
        # The "Batches: 100%|████" bar appears on every query embedding call.
        # TOKENIZERS_PARALLELISM also suppresses the tokenizer fork warning.
        _os.environ.setdefault("TOKENIZERS_PARALLELISM",   "false")
        _os.environ.setdefault("TQDM_DISABLE",             "1")
        # httpx logs every HEAD request to HuggingFace (20+ lines per load).
        # posthog logs telemetry notices. sentence_transformers logs model path.
        # These are demoted to WARNING for the duration of the load only.
        import logging as _logging
        _noisy = [
            "httpx",
            "sentence_transformers",
            "chromadb.telemetry.product.posthog",
            "huggingface_hub",
            "huggingface_hub.utils._http",
        ]
        _saved_levels = {n: _logging.getLogger(n).level for n in _noisy}
        for n in _noisy:
            _logging.getLogger(n).setLevel(_logging.WARNING)

        try:
            _embedding_fn_instance = (
                embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=EMBEDDING_MODEL,
                    cache_folder=str(_models_dir),
                )
            )
        finally:
            # Always restore log levels — even if load fails
            for n, lvl in _saved_levels.items():
                _logging.getLogger(n).setLevel(lvl if lvl != 0 else _logging.NOTSET)

        logger.info(f"Embedding model '{EMBEDDING_MODEL}' loaded and cached.")

    return _embedding_fn_instance


# =============================================================================
# DOCUMENT REGISTRY
# =============================================================================
# Authoritative routing table for all documents in the vector database.
# Maps each document ID to metadata that controls collection routing,
# agent targeting, retrieval filtering, and version tracking.
#
# Keys MUST match:
#   1. document_id generated by BankingPolicyGenerator._package_for_rag()
#   2. Corresponding .txt filenames in knowledge_base/
#
# doc_type_flag controls collection routing:
#   policy         → bank_policies collection
#   knowledge_base → customer_faqs collection
#   Both also go into: all_documents collection

DOCUMENT_REGISTRY: Dict[str, Dict] = {

    "POL-CCH-001": {
        "title":        "Customer Complaint Handling Policy",
        "category":     "policy",
        "version":      "2.1",
        "agent_target": "Dispatcher",
        "doc_type_flag":"policy",
        "description":  "Complaint routing rules, escalation matrix, SLA timelines",
    },

    "FRM-001": {
        "title":        "Fraud Detection and Prevention Guidelines",
        "category":     "security",
        "version":      "4.0",
        "agent_target": "Sentinel",
        "doc_type_flag":"policy",
        "description":  "Fraud detection rules, risk scoring 0–100, fraud escalation",
    },

    "TSU-POL-002": {
        "title":        "Transaction Processing Policies",
        "category":     "operations",
        "version":      "4.0",
        "agent_target": "All",
        "doc_type_flag":"policy",
        "description":  "Transaction processing rules, reversals, and processing SLA",
    },

    "FAQ-001": {
        "title":        "Customer Frequently Asked Questions",
        "category":     "knowledge_base",
        "version":      "2.0",
        "agent_target": "Customer",
        "doc_type_flag":"knowledge_base",
        "description":  "Customer-facing FAQs and help content",
    },

    "FRM-002": {
        "title":        "Merchant Risk Profiles",
        "category":     "security",
        "version":      "1.0",
        "agent_target": "Sentinel",
        "doc_type_flag":"policy",
        "description":  "Merchant risk categories and fraud risk weights",
    },

    "PRS-001": {
        "title":        "Product Recommendation Policy",
        "category":     "policy",
        "version":      "1.0",
        "agent_target": "Trajectory",
        "doc_type_flag":"policy",
        "description":  "Product eligibility rules and recommendation logic",
    },
}


# =============================================================================
# ChromaDB Configuration Class
# =============================================================================

class ChromaDBConfig:
    """
    Central configuration controller for ChromaDB.

    Ensures consistent embedding model, storage directory, and metadata
    across all ingestion and retrieval workflows.

    The embedding function is obtained via the module-level singleton
    get_embedding_function() — never instantiated inside this class.
    This is the key fix: instance-level caching (self._embedding_fn)
    was ineffective because a new ChromaDBConfig is created each run.
    """

    COLLECTION_POLICIES = "bank_policies"
    COLLECTION_FAQS     = "customer_faqs"
    COLLECTION_ALL      = "all_documents"
    EMBEDDING_MODEL     = EMBEDDING_MODEL   # reference module constant
    DISTANCE_METRIC     = "cosine"

    def __init__(self, persist_directory: Optional[Path] = None) -> None:
        """
        Initialise ChromaDB configuration object.

        Args:
            persist_directory: Optional custom storage path.
                               Default: project_root/chroma_db/
        """
        if persist_directory is None:
            persist_directory = Path(__file__).parent.parent / "chroma_db"

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"ChromaDB persistence directory: {self.persist_directory}")

    def get_embedding_function(self):
        """
        Return the shared module-level embedding function singleton.

        Delegates entirely to the module-level get_embedding_function().
        The model is loaded at most once per process regardless of how
        many ChromaDBConfig instances are created.
        """
        return get_embedding_function()

    def create_client(self) -> ClientAPI:
        """
        Create and return a ChromaDB client.

        Checks for Chroma Cloud credentials in environment variables
        first. Falls back to local PersistentClient if not configured.

        Returns:
            ChromaDB ClientAPI instance
        """
        api_key  = os.getenv("CHROMA_API_KEY",  "")
        tenant   = os.getenv("CHROMA_TENANT",   "")
        database = os.getenv("CHROMA_DATABASE", "")

        if api_key and tenant and database:
            logger.info("Connecting to Chroma Cloud...")
            # Suppress httpx and posthog telemetry INFO during connection.
            # The ~5 GET requests for auth/identity/tenant/database are
            # routine handshakes — not useful to see on every startup.
            import logging as _logging
            _conn_noisy = [
                "httpx",
                "chromadb.telemetry.product.posthog",
            ]
            _conn_saved = {n: _logging.getLogger(n).level for n in _conn_noisy}
            for n in _conn_noisy:
                _logging.getLogger(n).setLevel(_logging.WARNING)
            try:
                client = chromadb.HttpClient(
                    ssl=True,
                    host="api.trychroma.com",
                    tenant=tenant,
                    database=database,
                    headers={"x-chroma-token": api_key},
                )
            finally:
                for n, lvl in _conn_saved.items():
                    _logging.getLogger(n).setLevel(lvl if lvl != 0 else _logging.NOTSET)
            return client
        else:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using local ChromaDB at {self.persist_directory}")
            return chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True,
                ),
            )

    def get_or_create_collection(
        self,
        client:          ClientAPI,
        collection_name: str,
        metadata:        Optional[Dict] = None,
    ):
        """
        Retrieve an existing collection or create it if missing.

        Always uses the singleton embedding function so ingestion and
        retrieval are guaranteed to share the same model.

        Args:
            client:          ChromaDB client instance
            collection_name: Name of the collection
            metadata:        Optional collection-level metadata dict

        Returns:
            ChromaDB collection instance
        """
        embedding_function = self.get_embedding_function()

        if metadata is None:
            metadata = {
                "description":          f"Banking collection: {collection_name}",
                "embedding_model":      self.EMBEDDING_MODEL,
                "distance_metric":      self.DISTANCE_METRIC,
                "document_registry_size": str(len(DOCUMENT_REGISTRY)),
            }

        try:
            collection = client.get_collection(
                name=collection_name,
                embedding_function=embedding_function,
            )
            # DEBUG — fires on every RetrievalEngine.__init__, not just startup
            logger.debug(f"Retrieved existing collection: {collection_name}")

        except Exception:
            collection = client.create_collection(
                name=collection_name,
                embedding_function=embedding_function,
                metadata=metadata,
            )
            # INFO retained — collection creation is a meaningful event
            logger.info(f"Created new collection: {collection_name}")

        return collection

    def reset_collection(self, client: ClientAPI, collection_name: str) -> None:
        """
        Delete and recreate a collection.

        Used to prevent duplicate chunks during re-ingestion.

        Args:
            client:          ChromaDB client
            collection_name: Collection to reset
        """
        try:
            client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception:
            logger.warning(f"Collection did not exist: {collection_name}")

        self.get_or_create_collection(client, collection_name)
        logger.info(f"Reset complete: {collection_name}")

    def reset_all_collections(self, client: ClientAPI) -> None:
        """
        Reset all three collections for a clean re-ingestion.

        Args:
            client: ChromaDB client instance
        """
        for name in [
            self.COLLECTION_POLICIES,
            self.COLLECTION_FAQS,
            self.COLLECTION_ALL,
        ]:
            self.reset_collection(client, name)

        logger.info("All collections reset and ready for fresh ingestion.")


# =============================================================================
# Initialization Helper — Singleton
# =============================================================================
# The previous implementation returned a fresh (ChromaDBConfig, client)
# pair on every call. Since RetrievalEngine.__init__ calls initialize_chromadb(),
# every new engine instance triggered collection loading and a fresh client
# connection. Wrapping with a module-level cache returns the same pair
# for the entire process lifetime.

_chromadb_instance: Optional[Tuple[ClientAPI, ChromaDBConfig]] = None
_chromadb_lock = threading.Lock()


def initialize_chromadb() -> Tuple[ClientAPI, ChromaDBConfig]:
    """
    Return the shared (client, config) pair, initialising on first call.

    Thread-safe singleton — creates client and config exactly once per
    process. All subsequent calls return the cached pair immediately,
    avoiding repeated collection loading and connection setup overhead.

    Returns:
        Tuple of (ChromaDB ClientAPI, ChromaDBConfig)

    Used by:
        RetrievalEngine, RAGQueryEngine, DocumentIngester, agent systems
    """
    global _chromadb_instance

    if _chromadb_instance is not None:
        return _chromadb_instance

    with _chromadb_lock:
        if _chromadb_instance is not None:
            return _chromadb_instance

        logger.info("Initializing ChromaDB client (one-time setup)...")
        config = ChromaDBConfig()
        client = config.create_client()
        _chromadb_instance = (client, config)
        logger.info("ChromaDB client ready.")

    return _chromadb_instance


# =============================================================================
# Collection Statistics Helper
# =============================================================================

def get_collection_stats(collection) -> Dict:
    """
    Retrieve operational statistics from a collection.

    Useful for monitoring ingestion success, debugging retrieval,
    and system observability.

    Returns:
        Dict with collection_name, document_count, metadata, sample_metadata
    """
    try:
        count = collection.count()

        sample_metadata = {}
        if count > 0:
            sample          = collection.peek(limit=1)
            sample_metadata = sample["metadatas"][0] if sample["metadatas"] else {}

        return {
            "collection_name": collection.name,
            "document_count":  count,
            "metadata":        collection.metadata,
            "sample_metadata": sample_metadata,
        }

    except Exception as e:
        logger.error(f"Error retrieving collection stats: {e}")
        return {"error": str(e)}


# =============================================================================
# Standalone Test Runner
# =============================================================================

if __name__ == "__main__":
    print("\nInitializing ChromaDB configuration test...\n")

    client, config = initialize_chromadb()

    print(f"  Persistence    : {config.persist_directory}")
    print(f"  Embedding model: {config.EMBEDDING_MODEL}")
    print(f"  Document registry: {len(DOCUMENT_REGISTRY)} documents\n")

    print("Document Registry:")
    for doc_id, meta in DOCUMENT_REGISTRY.items():
        print(
            f"  {doc_id:<14}  category={meta['category']:<14}  "
            f"agent={meta['agent_target']:<12}  v{meta['version']}"
        )
    print()

    # Second call — should return instantly (singleton)
    client2, config2 = initialize_chromadb()
    assert client2 is client, "Singleton broken — returned a different client"
    print("  Singleton check : PASS (initialize_chromadb returned same instance)\n")

    collection = config.get_or_create_collection(client, config.COLLECTION_ALL)
    stats      = get_collection_stats(collection)

    print("Collection Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nChromaDB configuration is fully operational.\n")