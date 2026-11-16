# RAG & Grounding -- Deep Reference

> Cross-references: `prompt-engineering.md`, `evaluation-and-testing.md`, `orchestration-patterns.md`, `security-and-hardening.md`, `model-selection.md`

---

## The Grounding Principle

Grounding anchors AI outputs in reliable, factual data rather than relying on the LLM's training knowledge. It reduces hallucinations, enables proprietary data access, provides up-to-date information, and makes outputs verifiable through source citation.

**Why Grounding Matters:**
- LLMs have knowledge cutoff dates -- grounding provides current information
- LLMs hallucinate confidently -- grounding provides verifiable facts
- Enterprise data is proprietary -- grounding enables domain-specific answers
- Compliance requires auditability -- grounding enables source attribution

---

## RAG Three-Step Process

### Step 1: Retrieve
1. Convert user query to a vector embedding (same model used for document ingestion)
2. Search vector database for semantically similar document chunks
3. Return top-K most relevant chunks (typically K=3-10)

**Similarity Metrics:**
- **Cosine Similarity**: Directional similarity (angle between vectors). Most common for text. Range: -1 to 1. Invariant to vector magnitude.
- **L2 Distance (Euclidean)**: Straight-line distance between vectors. Lower = more similar. Good for clustering and nearest-neighbor.

### Step 2: Augment
Inject retrieved chunks into the prompt alongside the user query. Structure the augmentation clearly:
- Separate retrieved context from user query using delimiters
- Explicitly instruct the LLM to base answers ONLY on provided context
- Require source citations (document ID, section, or chunk reference)
- Define fallback: "If context is insufficient, say 'I don't have enough information to answer this question.'"

### Step 3: Generate
LLM produces a response grounded in the retrieved context. Quality depends on retrieval relevance, augmentation prompt quality, and grounding constraint strength.

---

## Advanced Retrieval Techniques

### Query Rewriting
The user's raw query is often suboptimal for retrieval. Transform it before searching:

| Technique | Description | When to Use |
|-----------|-------------|-------------|
| **Query expansion** | Add synonyms and related terms to broaden recall | User queries are terse or ambiguous |
| **Query decomposition** | Break complex query into sub-queries, retrieve for each | Multi-part questions ("compare X and Y") |
| **HyDE** (Hypothetical Document Embedding) | Generate a hypothetical answer, embed THAT, search for similar real documents | Queries where the answer's language differs from the question's language |
| **Step-back prompting** | Rephrase to a more general question first, retrieve broader context | Highly specific queries that miss relevant general context |

### Re-ranking
After initial vector retrieval, apply a second-stage ranker for higher precision:
- **Cross-encoder re-ranking**: Pass (query, document) pairs through a cross-encoder model. More accurate than bi-encoder similarity but more expensive. Apply to top 20-50 candidates, return top K.
- **LLM re-ranking**: Ask the LLM to score relevance of each retrieved chunk. Most expensive but handles nuance well.
- **Reciprocal Rank Fusion (RRF)**: Combine rankings from multiple retrieval methods (vector + keyword) into a single ranked list.

### Hybrid Search
Combine vector similarity with keyword/BM25 search:
- Vector search captures semantic meaning ("car" matches "automobile")
- Keyword search captures exact matches (product codes, names, acronyms)
- Fusion: run both, merge results using RRF or weighted scoring
- Particularly valuable for technical domains with specific terminology

### Multi-hop Retrieval
For questions requiring information from multiple documents:
1. Retrieve initial context based on the query
2. Generate an intermediate reasoning step
3. Formulate a follow-up query based on what's still missing
4. Retrieve additional context
5. Synthesize final answer from all retrieved information

Use when: answers span multiple documents, require connecting facts, or involve comparison/aggregation.

### Agentic RAG
The LLM decides when and how to retrieve, rather than retrieving on every query:
- Agent evaluates whether retrieval is needed (some questions don't need it)
- Agent formulates optimized search queries
- Agent evaluates retrieval quality and re-retrieves if insufficient
- Agent decides how many retrieval rounds are needed

Best for: conversational systems where not every turn needs retrieval, and for complex research tasks.

---

## Document Processing Pipeline

### Ingestion Steps
1. **Collect** documents (PDFs, web pages, databases, wikis, knowledge bases)
2. **Preprocess**: extract text, clean formatting, normalize encoding, handle tables/images
3. **Chunk**: split into segments (see strategies below)
4. **Enrich**: add metadata (source, date, author, category, section hierarchy)
5. **Embed**: convert each chunk to a vector via embedding model
6. **Store**: save vectors with metadata in vector database
7. **Index**: build retrieval indices for efficient search

### Chunking Strategies

| Strategy | Description | Best For | Tradeoff |
|----------|-------------|----------|----------|
| **Fixed-size** | Split every N tokens | Homogeneous documents, simple implementation | May cut mid-sentence |
| **Semantic** | Split at natural boundaries (paragraphs, sections, headings) | Structured documents (reports, manuals, articles) | Uneven chunk sizes |
| **Overlapping** | Fixed chunks with N-token overlap between consecutive chunks | Preventing information loss at boundaries | More storage, some redundancy |
| **Hierarchical** | Multi-level (document -> section -> paragraph) | Large collections with diverse query granularity | More complex indexing |
| **Sentence-window** | Embed single sentences, retrieve with surrounding window | Precision-critical retrieval | More embeddings to store |

**Sizing Guidance:**
- Start with 200-500 tokens per chunk, 10-20% overlap
- Too small = insufficient context per chunk, LLM lacks enough to reason
- Too large = noise dilutes relevance, wastes context window space
- Empirically test 3-4 chunk sizes on your data with your queries

### Metadata
Store alongside each chunk: source document ID, section heading, timestamp, author, category, page number, confidence score. Enables:
- Filtered retrieval ("only search HR docs from 2024+")
- Source attribution in responses
- Access control (user can only retrieve from authorized collections)
- Freshness ranking (prefer recent documents)

---

## Embedding Models

Convert text to numerical vectors capturing semantic meaning. "Car" and "automobile" produce nearby vectors despite sharing no characters.

**Selection Criteria:**

| Criterion | Consideration |
|-----------|--------------|
| Dimensionality | 768-1536 common. Higher = more expressive, more storage/compute |
| Domain fit | General-purpose vs. domain-specific (legal, medical, code) |
| Multilingual support | Essential for international deployments |
| Max input length | Must accommodate your chunk sizes |
| Inference speed | Matters for real-time ingestion and query-time embedding |

**Critical Rule:** Use the SAME embedding model for ingestion and query time. Mixing models produces incompatible vector spaces.

---

## Vector Search Tuning

- **Top-K**: Start with 5, adjust based on answer quality. Too few = missed context. Too many = noise dilutes relevance.
- **Relevance threshold**: Minimum similarity score cutoff. Prevents low-quality matches from polluting context.
- **Metadata filtering**: Filter by source, date, category BEFORE vector search -- reduces search space and improves precision.
- **Re-ranking**: After initial retrieval, use a cross-encoder or LLM to re-rank for improved precision (see Advanced Retrieval).
- **Hybrid search**: Combine vector similarity with keyword/BM25 for both semantic breadth and exact-match precision.

---

## RAG Evaluation Metrics

| Metric | What It Measures | How to Compute |
|--------|-----------------|----------------|
| **Context Relevance** | Are retrieved chunks relevant to the query? | LLM-as-judge or human annotation on retrieved chunks |
| **Context Recall** | Does retrieved context contain the information needed to answer? | Compare retrieved context against ground-truth answer |
| **Faithfulness** | Is the generated answer supported by retrieved context? | Claim extraction + entailment check against context |
| **Answer Relevance** | Does the answer actually address the query? | Semantic similarity between query and answer |
| **Answer Correctness** | Is the answer factually correct? | Compare against ground-truth answers |
| **Retrieval Precision@K** | Of K retrieved chunks, how many are relevant? | Human annotation or relevance model |
| **Retrieval Recall** | Of all relevant chunks in the corpus, how many were retrieved? | Requires annotated relevant set |

**Evaluation Approach:**
1. Build a test set of 50-100 questions with ground-truth answers and relevant source documents
2. Run RAG pipeline, collect retrieved chunks and generated answers
3. Score each metric above
4. Identify weakest link: is the problem retrieval (wrong chunks) or generation (wrong answer despite good chunks)?
5. Target improvements at the weakest link

See `evaluation-and-testing.md` for general evaluation frameworks.

---

## When to Use RAG

**Use RAG when:**
- Proprietary or frequently updated data needed
- Factual accuracy is critical (compliance, legal, medical, financial)
- Citations and source attribution required
- Fine-tuning is too expensive or inflexible
- Knowledge base changes regularly

**Skip RAG when:**
- Task uses only general knowledge
- Latency prohibits retrieval step
- Knowledge base is small enough to fit in the prompt (< 100K tokens)
- Task is purely creative or generative

**RAG vs. Alternatives:**

| Approach | Best For | Tradeoff |
|----------|----------|----------|
| **RAG** | Dynamic data, transparent sourcing, no model modification | Added latency, retrieval quality dependency |
| **Fine-tuning** | Style/behavior change, domain vocabulary, consistent patterns | Expensive, static knowledge, less transparent |
| **Long context** | Small stable document sets, single-document analysis | Limited by context window, no dynamic updates |
| **RAG + Fine-tuning** | Domain-adapted model with dynamic knowledge access | Most complex, highest quality ceiling |

---

## Common Failure Modes

| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Irrelevant retrieval | Answers miss the point despite context | Improve chunking, add re-ranking, tune threshold, try query rewriting |
| Missing information | "I don't know" when answer exists in corpus | Increase K, fix chunking (answer split across chunks), try query decomposition |
| Hallucination despite context | Answer contradicts retrieved sources | Strengthen grounding instructions, add faithfulness validation, output checking |
| Stale data | Outdated answers | Increase update frequency, add freshness signals to ranking, timestamp filtering |
| Context overflow | Too many chunks exceed context window | Reduce K, summarize chunks before injection, use hierarchical retrieval |
| Citation fabrication | LLM cites sources that don't support the claim | Add citation verification in post-processing, cross-check claims against context |
| Query-document mismatch | User language differs from document language | Apply query rewriting, HyDE, or query expansion |
| Low recall on specific queries | Domain jargon or acronyms not matched semantically | Add hybrid search (vector + keyword), expand abbreviations |
