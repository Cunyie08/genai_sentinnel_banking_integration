"""
Hybrid Document Ingestion Pipeline
====================================

Production-grade pipeline combining:
  - Smart chunking (section-based with paragraph fallback)
  - Rich metadata enrichment (agent_target, doc_type_flag, contains_sla, etc.)
  - In-memory generation mode (no disk roundtrip needed)
  - Disk-based mode with auto-generation fallback
  - Registry-driven collection routing
  - Batch insertion into ChromaDB



Author: AI Engineer 2
Date: February 2026
"""

import re
import hashlib
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import logging
import sys

from .chromadb_config import (
    initialize_chromadb,
    ChromaDBConfig,
    DOCUMENT_REGISTRY,
    get_collection_stats,
)
from ..knowledge_base.generate_policies import (
    BankingPolicyGenerator,
    DATASET_DIR,
    EXPECTED_SLA,
    DEPT_NAMES,
    MERCHANT_RISK,
    FLAG_WEIGHTS,
)

# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# Document Chunker
# =============================================================================

class DocumentChunker:
    """
    Production-grade chunker for Sentinel Bank policy documents.

    Strategy:
      1. Split on major section dividers (=== and --- lines ≥ 70 chars)
      2. Keep each section as one chunk unless > 2000 chars
      3. For large sections: split on double newlines with 1-paragraph overlap
      4. Never split mid-sentence inside a paragraph

    Produces chunks of 300–2000 chars optimal for all-mpnet-base-v2 (512 token limit).
    """

    MAX_CHUNK_SIZE  = 2000   # chars → ~500 tokens, safe for all-mpnet-base-v2
    MIN_SECTION_LEN = 100    # skip trivially short fragments
    OVERLAP_PARAS   = 1      # paragraphs of overlap between sub-chunks

    # Dividers used in generated policy documents
    MAJOR_DIVIDERS = (
        "=========================================================================",
        "─────────────────────────────────────────────────────────────────────────",
    )

    @staticmethod
    def chunk_document(text: str, document_id: str) -> List[Dict]:
        """
        Split a policy document into retrieval-optimised chunks.

        Args:
            text: Full document text
            document_id: Document ID for chunk ID generation

        Returns:
            List of chunk dicts: chunk_id, content, section_title,
            chunk_index, char_count
        """
        chunks      = []
        # Normalise line endings
        text        = text.replace("\r\n", "\n")
        lines       = text.split("\n")

        # --- Find divider positions ---
        divider_positions = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if any(stripped.startswith(div[:10]) and len(stripped) >= 50
                   for div in DocumentChunker.MAJOR_DIVIDERS):
                divider_positions.append(i)

        # Build section spans
        if not divider_positions:
            # No dividers — treat whole document as one section
            spans = [(0, len(lines))]
        else:
            spans = []
            for idx, pos in enumerate(divider_positions):
                start = pos
                end   = (divider_positions[idx + 1]
                         if idx + 1 < len(divider_positions)
                         else len(lines))
                spans.append((start, end))
            # Content before first divider (preamble)
            if divider_positions[0] > 0:
                spans.insert(0, (0, divider_positions[0]))

        # --- Convert spans to text sections ---
        for span_idx, (start, end) in enumerate(spans):
            section_lines = lines[start:end]
            section_text  = "\n".join(section_lines).strip()

            if len(section_text) < DocumentChunker.MIN_SECTION_LEN:
                continue

            # Extract section title — first non-empty, non-divider line
            section_title = f"Section {span_idx}"
            for line in section_lines:
                stripped = line.strip()
                if stripped and not any(
                    stripped.startswith(d[:10]) for d in DocumentChunker.MAJOR_DIVIDERS
                ):
                    section_title = stripped[:120]
                    break

            if len(section_text) <= DocumentChunker.MAX_CHUNK_SIZE:
                chunks.append({
                    "chunk_id":      f"{document_id}_chunk{span_idx}",
                    "content":       section_text,
                    "section_title": section_title,
                    "chunk_index":   len(chunks),
                    "char_count":    len(section_text),
                })
            else:
                # Section too large — split on double newlines with overlap
                sub_chunks = DocumentChunker._split_large_section(
                    section_text, section_title, document_id, span_idx, len(chunks)
                )
                chunks.extend(sub_chunks)

        logger.info(f"  → {document_id}: {len(chunks)} chunks created")
        if chunks:
            avg = sum(c["char_count"] for c in chunks) / len(chunks)
            logger.info(f"  → Average chunk size: {avg:.0f} chars")

        return chunks

    @staticmethod
    def _split_large_section(
        section_text:  str,
        section_title: str,
        document_id:   str,
        span_idx:      int,
        base_index:    int,
    ) -> List[Dict]:
        """Split an oversized section into sub-chunks with 1-paragraph overlap."""
        paragraphs   = section_text.split("\n\n")
        sub_chunks   = []
        current_paras: List[str] = []
        current_len  = 0
        sub_idx      = 0

        for para in paragraphs:
            if (current_len + len(para) > DocumentChunker.MAX_CHUNK_SIZE
                    and current_paras):
                chunk_text = "\n\n".join(current_paras)
                sub_chunks.append({
                    "chunk_id":      f"{document_id}_chunk{span_idx}_sub{sub_idx}",
                    "content":       chunk_text,
                    "section_title": section_title,
                    "chunk_index":   base_index + len(sub_chunks),
                    "char_count":    len(chunk_text),
                })
                # Overlap: carry last paragraph into next chunk
                overlap      = current_paras[-DocumentChunker.OVERLAP_PARAS:]
                current_paras = overlap + [para]
                current_len  = sum(len(p) for p in current_paras)
                sub_idx     += 1
            else:
                current_paras.append(para)
                current_len += len(para)

        if current_paras:
            chunk_text = "\n\n".join(current_paras)
            sub_chunks.append({
                "chunk_id":      f"{document_id}_chunk{span_idx}_sub{sub_idx}",
                "content":       chunk_text,
                "section_title": section_title,
                "chunk_index":   base_index + len(sub_chunks),
                "char_count":    len(chunk_text),
            })

        return sub_chunks

    @staticmethod
    def extract_key_terms(text: str, top_n: int = 5) -> str:
        """
        Extract top-N key terms from text.

        Returns a comma-separated string (ChromaDB metadata requires str values).

        Args:
            text:  Input text
            top_n: Number of key terms to return

        Returns:
            Comma-separated string of key terms, e.g. "fraud,risk,card,transaction,sla"
        """
        STOPWORDS = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "are", "was", "were",
            "be", "been", "this", "that", "these", "those", "will", "shall",
            "should", "must", "have", "has", "had", "not", "its", "it",
            "their", "they", "which", "when", "where", "all", "any",
        }
        words     = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        freq: Dict[str, int] = {}
        for w in words:
            if w not in STOPWORDS:
                freq[w] = freq.get(w, 0) + 1
        top = sorted(freq, key=freq.get, reverse=True)[:top_n]  # type: ignore[arg-type]
        return ", ".join(top)


# =============================================================================
# Document Ingester
# =============================================================================

class DocumentIngester:
    """
    Production ingestion pipeline that loads documents into ChromaDB.

    Workflow:
      1. Load documents (disk or in-memory)
      2. Chunk with DocumentChunker
      3. Enrich every chunk with full metadata
      4. Route to correct collection(s)
      5. Batch-insert into ChromaDB

    Two modes:
      ingest_from_generator() — no disk I/O, generates docs in memory
      ingest_knowledge_base() — reads .txt files from directory
    """

    def __init__(self, client, config: ChromaDBConfig):
        """
        Args:
            client: ChromaDB client
            config: ChromaDBConfig instance
        """
        self.client  = client
        self.config  = config
        self.chunker = DocumentChunker()

    # =========================================================================
    # Shared Chunk Enrichment Helper
    # =========================================================================

    def _make_enriched_chunks(
        self,
        content:       str,
        document_id:   str,
        title:         str,
        category:      str,
        version:       str,
        agent_target:  str,
        doc_type_flag: str,
        source_meta:   Dict,
    ) -> List[Dict]:
        """
        Chunk a document and attach production-grade metadata to every chunk.

        Metadata fields written to each ChromaDB chunk:
          source_document     : document ID (e.g. "FRM-002")
          document_title      : human-readable title
          document_type       : category (policy|security|operations|knowledge_base)
          doc_type_flag       : "policy" | "knowledge_base" — drives collection routing
          version             : document version string
          agent_target        : primary agent consumer (Dispatcher|Sentinel|Trajectory|All|Customer)
          section_title       : section heading for this chunk
          chunk_index         : ordinal position within document
          char_count          : character count of cleaned chunk content
          content_hash        : MD5 for deduplication
          key_terms           : comma-separated top-5 terms
          contains_sla        : bool — True if chunk mentions SLA/resolution timeframes
          ingestion_timestamp : ISO datetime of this ingest run
          dataset_dir         : DATASET_DIR path for audit trail
          project             : pass-through from _package_for_rag metadata
          organization        : pass-through from _package_for_rag metadata
          jurisdiction        : pass-through from _package_for_rag metadata

        Args:
            content:       Raw document text
            document_id:   Document ID
            title:         Human-readable document title
            category:      Category string
            version:       Version string
            agent_target:  Target agent
            doc_type_flag: "policy" or "knowledge_base"
            source_meta:   Metadata dict from _package_for_rag (project, org, etc.)

        Returns:
            List of enriched chunk dicts ready for ChromaDB.add()
        """
        raw_chunks  = self.chunker.chunk_document(content, document_id)
        enriched    = []
        ingest_ts   = datetime.now().isoformat()

        # SLA-related keywords for contains_sla flag
        SLA_TERMS = {
            "sla", "resolution", "working days", "timeframe",
            "deadline", "hours", "within", "turnaround",
        }

        for chunk in raw_chunks:
            # Normalize whitespace for embedding quality
            clean = re.sub(r"\s+", " ", chunk["content"]).strip()

            content_hash  = hashlib.md5(clean.encode()).hexdigest()
            key_terms     = self.chunker.extract_key_terms(clean)
            contains_sla  = any(t in clean.lower() for t in SLA_TERMS)

            enriched.append({
                "id":       chunk["chunk_id"],
                "document": clean,
                "metadata": {
                    # Core identification
                    "source_document":     document_id,
                    "document_title":      title,
                    "document_type":       category,
                    "doc_type_flag":       doc_type_flag,
                    "version":             version,
                    "agent_target":        agent_target,
                    # Chunk position
                    "section_title":       chunk["section_title"],
                    "chunk_index":         chunk["chunk_index"],
                    "char_count":          len(clean),
                    # Content fingerprint
                    "content_hash":        content_hash,
                    "key_terms":           key_terms,
                    "contains_sla":        contains_sla,
                    # Pipeline audit
                    "ingestion_timestamp": ingest_ts,
                    "dataset_dir":         str(DATASET_DIR),
                    # Provenance pass-through
                    "project":             source_meta.get("project",      ""),
                    "organization":        source_meta.get("organization", ""),
                    "jurisdiction":        source_meta.get("jurisdiction", "Nigeria"),
                },
            })

        return enriched

    # =========================================================================
    # In-Memory Ingestion (preferred mode)
    # =========================================================================

    def ingest_from_generator(
        self,
        bank_name:   str  = "Sentinel Bank Nigeria",
        reset_first: bool = True,
    ) -> Dict:
        """
        Generate all 6 policy documents in memory and ingest directly.

        No prior save_all_policies() call needed. Preferred in CI/CD pipelines
        or when starting from scratch.

        Args:
            bank_name:   Passed to BankingPolicyGenerator
            reset_first: Wipe all collections first (prevents duplicate chunks)

        Returns:
            Dict with: total_docs, total_chunks, policy_chunks, faq_chunks,
                       documents_ingested, timestamp
        """
        print("\n" + "=" * 70)
        print(" " * 12 + "IN-MEMORY KNOWLEDGE BASE INGESTION")
        print("=" * 70 + "\n")

        if reset_first:
            print("Step 0: Resetting collections...")
            self.config.reset_all_collections(self.client)
            print("  ✓ All collections cleared\n")

        print("Step 1: Generating documents via BankingPolicyGenerator...")
        generator = BankingPolicyGenerator(bank_name=bank_name)
        documents = generator.generate_all_documents()
        print(f"  ✓ {len(documents)} documents generated\n")

        print("Step 2: Chunking and enriching metadata...")
        all_chunks: List[Dict]    = []
        policy_chunks: List[Dict] = []
        faq_chunks: List[Dict]    = []

        for doc in documents:
            doc_id        = doc["document_id"]
            registry      = DOCUMENT_REGISTRY.get(doc_id, {})
            doc_type_flag = registry.get("doc_type_flag", "policy")

            # Override from doc's own category if available
            if doc.get("category") == "knowledge_base":
                doc_type_flag = "knowledge_base"

            chunks = self._make_enriched_chunks(
                content       = doc["content"],
                document_id   = doc_id,
                title         = doc.get("title",    registry.get("title",    doc_id)),
                category      = doc.get("category", registry.get("category", "policy")),
                version       = doc.get("version",  registry.get("version",  "1.0")),
                agent_target  = registry.get("agent_target", "All"),
                doc_type_flag = doc_type_flag,
                source_meta   = doc.get("metadata", {}),
            )

            all_chunks.extend(chunks)
            if doc_type_flag == "knowledge_base":
                faq_chunks.extend(chunks)
            else:
                policy_chunks.extend(chunks)

            print(f"  ✓ {doc_id:<14}  {len(chunks):>3} chunks  "
                  f"agent={registry.get('agent_target', 'All'):<12}  "
                  f"type={doc_type_flag}")

        print(f"\n  Total: {len(all_chunks)} chunks  "
              f"({len(policy_chunks)} policy + {len(faq_chunks)} FAQ)\n")

        print("Step 3: Ingesting into ChromaDB...")

        if policy_chunks:
            print(f"\n  → {self.config.COLLECTION_POLICIES}  ({len(policy_chunks)} chunks)")
            self.ingest_to_collection(policy_chunks, self.config.COLLECTION_POLICIES)

        if faq_chunks:
            print(f"\n  → {self.config.COLLECTION_FAQS}  ({len(faq_chunks)} chunks)")
            self.ingest_to_collection(faq_chunks, self.config.COLLECTION_FAQS)

        print(f"\n  → {self.config.COLLECTION_ALL}  ({len(all_chunks)} chunks)")
        self.ingest_to_collection(all_chunks, self.config.COLLECTION_ALL)

        self._print_completion_block()

        return {
            "total_docs":         len(documents),
            "total_chunks":       len(all_chunks),
            "policy_chunks":      len(policy_chunks),
            "faq_chunks":         len(faq_chunks),
            "documents_ingested": [d["document_id"] for d in documents],
            "timestamp":          datetime.now().isoformat(),
        }

    # =========================================================================
    # Disk-Based Ingestion
    # =========================================================================

    def load_documents_from_directory(self, directory: Path) -> List[Dict]:
        """
        Load all .txt documents from a directory.

        Uses DOCUMENT_REGISTRY for category/agent metadata instead of
        fragile path-part string checks.

        Args:
            directory: Root directory containing .txt policy files

        Returns:
            List of document dicts
        """
        documents = []
        directory = Path(directory)

        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return documents

        for txt_file in sorted(directory.glob("**/*.txt")):
            try:
                content  = txt_file.read_text(encoding="utf-8")
                doc_id   = txt_file.stem
                registry = DOCUMENT_REGISTRY.get(doc_id, {})

                documents.append({
                    "document_id":   doc_id,
                    "filepath":      str(txt_file),
                    "content":       content,
                    "category":      registry.get("category",      "policy"),
                    "doc_type_flag": registry.get("doc_type_flag", "policy"),
                    "version":       registry.get("version",       "1.0"),
                    "title":         registry.get("title",         doc_id),
                    "agent_target":  registry.get("agent_target",  "All"),
                    "filename":      txt_file.name,
                })
                logger.info(
                    f"Loaded {txt_file.name}  "
                    f"category={registry.get('category', 'policy')}  "
                    f"agent={registry.get('agent_target', 'All')}"
                )
            except Exception as e:
                logger.error(f"Error loading {txt_file}: {e}")

        logger.info(f"Loaded {len(documents)} documents from {directory}")
        return documents

    @staticmethod
    def preprocess_document(document: Dict) -> Dict:
        """
        Clean and validate document text before chunking.

        Args:
            document: Raw document dict

        Returns:
            Preprocessed document dict (mutated in place)
        """
        content = document["content"]
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = re.sub(r" {2,}", " ", content)
        content = content.replace("\r\n", "\n")
        document["content"]    = content.strip()
        document["char_count"] = len(content)
        document["word_count"] = len(content.split())
        return document

    def ingest_knowledge_base(
        self,
        knowledge_base_dir: Path,
        reset_first: bool = True,
    ):
        """
        Complete disk-based ingestion pipeline.

        Auto-generates policy documents if directory is missing.

        Args:
            knowledge_base_dir: Directory containing .txt policy files
            reset_first: Wipe collections before ingesting (default True)
        """
        print("\n" + "=" * 70)
        print(" " * 15 + "KNOWLEDGE BASE INGESTION (DISK MODE)")
        print("=" * 70 + "\n")

        knowledge_base_dir = Path(knowledge_base_dir)

        if not knowledge_base_dir.exists():
            print(f"⚠️  Not found: {knowledge_base_dir}")
            print("    Auto-generating policy documents...\n")
            BankingPolicyGenerator().save_all_policies(knowledge_base_dir)
            print()

        if reset_first:
            print("Step 0: Resetting collections...")
            self.config.reset_all_collections(self.client)
            print("  ✓ All collections cleared\n")

        print("Step 1: Loading documents...")
        documents = self.load_documents_from_directory(knowledge_base_dir)
        print(f"  ✓ {len(documents)} documents loaded\n")

        print("Step 2: Preprocessing...")
        for doc in documents:
            self.preprocess_document(doc)
        print(f"  ✓ {len(documents)} documents preprocessed\n")

        print("Step 3: Chunking...")
        all_chunks: List[Dict] = []
        for doc in documents:
            chunks = self._make_enriched_chunks(
                content       = doc["content"],
                document_id   = doc["document_id"],
                title         = doc["title"],
                category      = doc["category"],
                version       = doc["version"],
                agent_target  = doc["agent_target"],
                doc_type_flag = doc["doc_type_flag"],
                source_meta   = {},
            )
            all_chunks.extend(chunks)
            print(f"  ✓ {doc['document_id']:<14}  {len(chunks):>3} chunks  "
                  f"agent={doc.get('agent_target', 'All')}")

        print(f"\n  Total: {len(all_chunks)} chunks\n")

        policy_chunks = [c for c in all_chunks
                         if c["metadata"]["doc_type_flag"] != "knowledge_base"]
        faq_chunks    = [c for c in all_chunks
                         if c["metadata"]["doc_type_flag"] == "knowledge_base"]

        print("Step 4: Ingesting into ChromaDB...")

        if policy_chunks:
            print(f"\n  → {self.config.COLLECTION_POLICIES}  ({len(policy_chunks)} chunks)")
            self.ingest_to_collection(policy_chunks, self.config.COLLECTION_POLICIES)

        if faq_chunks:
            print(f"\n  → {self.config.COLLECTION_FAQS}  ({len(faq_chunks)} chunks)")
            self.ingest_to_collection(faq_chunks, self.config.COLLECTION_FAQS)

        print(f"\n  → {self.config.COLLECTION_ALL}  ({len(all_chunks)} chunks)")
        self.ingest_to_collection(all_chunks, self.config.COLLECTION_ALL)

        self._print_completion_block()

    # =========================================================================
    # Batch Insert into ChromaDB
    # =========================================================================

    def ingest_to_collection(
        self,
        chunks:          List[Dict],
        collection_name: str,
        batch_size:      int = 100,
    ):
        """
        Insert enriched chunks into ChromaDB in batches.

        Args:
            chunks:          Enriched chunk list from _make_enriched_chunks()
            collection_name: Target collection name
            batch_size:      Chunks per batch (default 100)
        """
        collection = self.config.get_or_create_collection(
            self.client, collection_name
        )
        logger.info(f"Ingesting {len(chunks)} chunks → {collection_name}")

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            collection.add(
                ids       = [c["id"]       for c in batch],
                documents = [c["document"] for c in batch],
                metadatas = [c["metadata"] for c in batch],
            )
            logger.info(
                f"  Batch {i // batch_size + 1}: "
                f"{len(batch)} chunks inserted"
            )

        logger.info(f"  ✓ All chunks ingested to {collection_name}")

    # =========================================================================
    # Completion Block
    # =========================================================================

    def _print_completion_block(self):
        """Print post-ingestion stats and shared-constants audit."""
        print("\n" + "=" * 70)
        print(" " * 20 + "INGESTION COMPLETE!")
        print("=" * 70 + "\n")

        print("Collection Statistics:")
        for name in [self.config.COLLECTION_POLICIES,
                     self.config.COLLECTION_FAQS,
                     self.config.COLLECTION_ALL]:
            try:
                col   = self.client.get_collection(name)
                count = col.count()
                print(f"  {name:<25}: {count:>4} chunks")
            except Exception:
                print(f"  {name:<25}: (not yet created)")

        print()
        print("Shared constants baked into chunk metadata:")
        print(f"  EXPECTED_SLA  : {dict(EXPECTED_SLA)}")
        print(f"  MERCHANT_RISK : {len(MERCHANT_RISK)} categories  "
              f"max={max(MERCHANT_RISK.values())} pts")
        print(f"  FLAG_WEIGHTS  : {dict(FLAG_WEIGHTS)}")
        print(f"  DEPT_NAMES    : {list(DEPT_NAMES.keys())}")
        print(f"  Dataset dir   : {DATASET_DIR}")

        print("\n" + "=" * 70)
        print("Knowledge base is ready for RAG queries!")
        print("Run: python rag_query.py")
        print("=" * 70 + "\n")


# =============================================================================
# Module-Level Entry Point
# =============================================================================

def ingest_banking_policies(mode: str = "memory", reset_first: bool = True):
    """
    Ingest all 6 Sentinel Bank policy documents into ChromaDB.

    Args:
        mode:        "memory" (default) — generate docs in memory, no disk needed
                     "disk"             — load from knowledge_base/ directory
        reset_first: Wipe collections before ingesting (default True)

    Usage:
        python ingest_documents.py             # in-memory mode
        python ingest_documents.py --disk      # disk mode
        python ingest_documents.py --no-reset  # keep existing chunks
    """
    client, config = initialize_chromadb()
    ingester       = DocumentIngester(client, config)

    if mode == "memory":
        result = ingester.ingest_from_generator(
            bank_name   = "Sentinel Bank Nigeria",
            reset_first = reset_first,
        )
        print(f"\nIngested {result['total_chunks']} chunks from "
              f"{result['total_docs']} documents.")
        print(f"Documents: {', '.join(result['documents_ingested'])}")

    else:
        kb_dir = Path(__file__).parent.parent / "knowledge_base"
        ingester.ingest_knowledge_base(
            knowledge_base_dir = kb_dir,
            reset_first        = reset_first,
        )


if __name__ == "__main__":
    mode        = "memory"
    reset_first = True

    for arg in sys.argv[1:]:
        if arg == "--disk":
            mode = "disk"
        elif arg == "--no-reset":
            reset_first = False

    ingest_banking_policies(mode=mode, reset_first=reset_first)