"""
RAG Workshop Corpus - Shared document collection for Days 1 and 2.

This corpus is designed to demonstrate progressive improvement across retrieval methods:
- Keyword/BM25 struggle with keyword-stuffed TRAP documents
- Vector search struggles with semantically similar NEAR-MISS documents  
- Hybrid (RRF) balances both but still includes some distractors
- Reranking filters out remaining distractors

Structure:
- 4 test queries with designated correct answer documents
- 8 documents per query (1 correct, 3 BM25 traps, 3 vector traps, 1 hybrid challenge)
- 28 filler documents for volume and noise
- Total: 66 documents
"""

# Document corpus - 66 documents total
documents = [
    # =================================================================
    # QUERY 1: "What is machine learning?" -> CORRECT DOC: 0
    # =================================================================
    # CORRECT - Direct definition but doesn't repeat "machine learning" excessively
    "Machine learning, a subset of artificial intelligence, enables systems to learn patterns from data without explicit programming.",
    # BM25 TRAP 1 - Keyword stuffed (mentions "machine learning" 8 times but meaningless)
    "Machine learning requires machine learning algorithms. Machine learning models need machine learning data. Without machine learning techniques, machine learning cannot work.",
    # BM25 TRAP 2 - About history, not definition
    "Machine learning began in the 1950s. Machine learning research started with perceptrons. Machine learning scientists published papers on machine learning theories in academic journals.",
    # VECTOR TRAP 1 - AI broadly (semantic similarity to query but wrong topic)
    "Artificial intelligence systems process information using neural networks. Deep learning models recognize complex patterns. AI algorithms improve through training on large datasets.",
    # VECTOR TRAP 2 - ML applications (related but doesn't define ML)
    "Companies use predictive models for recommendation systems. Image recognition software identifies objects. Natural language processing enables chatbots. Autonomous vehicles use computer vision.",
    # VECTOR TRAP 3 - Educational learning (semantic similarity to "learning")
    "Students learn through practice and feedback. Educational systems adapt to individual needs. Personalized learning improves outcomes. Cognitive science studies how humans acquire knowledge.",
    # HYBRID CHALLENGE - Partially correct but incomplete
    "Machine learning uses statistical methods. It involves training models on data. The process includes feature extraction and model selection.",
    # NOISE - Related field but irrelevant
    "Python libraries include NumPy, pandas, and matplotlib. Data scientists use Jupyter notebooks. Cloud computing provides scalable resources.",
    
    # =================================================================
    # QUERY 2: "How do cars work?" -> CORRECT DOC: 8
    # =================================================================
    # CORRECT - Uses "cars" not "automobiles", explains mechanism (synonym gap for keyword search)
    "Cars operate through internal combustion engines that transform fuel into mechanical power via controlled explosions within cylinders.",
    # BM25 TRAP 1 - "Car" repeated but about buying, not mechanics
    "Car buyers research car models online. Car dealers sell car brands. Car loans help purchase car vehicles. Car insurance protects car owners.",
    # BM25 TRAP 2 - "Automobile" repeated but about legal stuff
    "Automobile registration requires automobile documentation. Automobile licenses authorize automobile operation. Automobile laws regulate automobile traffic.",
    # VECTOR TRAP 1 - Transportation broadly (semantic similarity)
    "Buses transport passengers along fixed routes. Trains carry commuters on rail networks. Airplanes fly between airports. Ships navigate oceans carrying cargo.",
    # VECTOR TRAP 2 - Electric vehicles (close topic but different question)
    "Electric vehicles use battery packs and electric motors. EV charging stations provide power. Tesla produces electric cars. Range anxiety affects EV adoption.",
    # VECTOR TRAP 3 - Manufacturing (related to cars but wrong aspect)
    "Factory robots assemble vehicle components. Supply chains deliver parts to plants. Quality control inspectors check production lines. Lean manufacturing reduces waste.",
    # HYBRID CHALLENGE - Parts but no mechanism explanation
    "Vehicles contain transmissions, differentials, and exhaust systems. Mechanics repair brake pads and replace oil. Dashboards display speed and fuel levels.",
    # NOISE
    "Traffic lights control intersection flow. Highway systems connect cities. Parking meters charge for spaces. Road maintenance crews repair potholes.",
    
    # =================================================================
    # QUERY 3: "How to debug code?" -> CORRECT DOC: 16
    # =================================================================
    # CORRECT - Uses "debugging" not "fix code", no "errors" keyword (semantic gap for keyword search)
    "Debugging involves identifying software defects through systematic analysis, inserting breakpoints, examining variable states, and stepping through execution flow.",
    # BM25 TRAP 1 - "Fix" repeated but meaningless
    "Fix code errors to fix programs. Fix debugging by fixing lines. Fix syntax to fix runtime. Fix logic to fix output.",
    # BM25 TRAP 2 - About code quality/prevention, not debugging
    "Code reviews prevent code errors. Static analysis finds code mistakes. Linting checks code style. Code standards reduce code bugs in code bases.",
    # VECTOR TRAP 1 - Error types (descriptive, not prescriptive)
    "Syntax errors violate grammar rules. Runtime errors occur during execution. Logic errors produce wrong results. Exceptions halt program flow.",
    # VECTOR TRAP 2 - Testing (related but different activity)
    "Unit tests verify function behavior. Integration tests check module interactions. Test-driven development writes tests first. QA teams validate software quality.",
    # VECTOR TRAP 3 - Performance optimization (different topic)
    "Profiling identifies bottlenecks. Caching improves response times. Algorithm complexity affects scalability. Memory leaks consume resources over time.",
    # HYBRID CHALLENGE - Tools mentioned but not methodology
    "Developers use IDE features and logging statements. Stack traces show error locations. Print statements display values. Documentation explains APIs.",
    # NOISE
    "Version control tracks code changes. Git repositories store commit history. Pull requests facilitate code review. Continuous integration runs automated builds.",
    
    # =================================================================
    # QUERY 4: "What is RAG?" -> CORRECT DOC: 24
    # =================================================================
    # CORRECT - Full definition but doesn't contain "RAG" acronym
    "Retrieval-augmented generation combines document retrieval systems with language models to produce responses grounded in external knowledge sources.",
    # BM25 TRAP 1 - "RAG" everywhere but wrong context (fashion industry)
    "RAG designers create RAG collections. RAG fashion shows display RAG clothing. RAG industry produces RAG garments. RAG trends influence RAG styles.",
    # BM25 TRAP 2 - "RAG" in technical context but wrong meaning (memory errors)
    "Buffer overflow causes RAG faults. Memory RAG errors crash systems. RAG allocation fails when RAM exhausted. RAG segmentation faults indicate pointer issues.",
    # VECTOR TRAP 1 - LLMs broadly (semantic similarity)
    "Large language models generate text using transformers. GPT processes tokens autoregressively. LLMs are trained on internet text. Prompt engineering guides outputs.",
    # VECTOR TRAP 2 - Search engines (retrieval but not augmented generation)
    "Google indexes web pages. Search algorithms rank results. Elasticsearch queries document stores. Information retrieval finds relevant content.",
    # VECTOR TRAP 3 - Knowledge systems (knowledge but not retrieval-augmented)
    "Expert systems encode domain rules. Knowledge graphs connect entities. Ontologies define relationships. Symbolic AI uses formal logic.",
    # HYBRID CHALLENGE - Components mentioned separately
    "Vector databases store embeddings. Similarity search finds nearest neighbors. Language models generate sequences. Context windows have token limits.",
    # NOISE
    "Transformers use attention mechanisms. BERT introduced bidirectional encoding. Fine-tuning adapts pre-trained models. HuggingFace hosts model repositories.",
    
    # =================================================================
    # FILLER DOCUMENTS - Add volume and realistic noise
    # =================================================================
    # Database (8 docs)
    "SQL databases store structured data in tables. Relational models use primary keys. JOIN operations combine tables. ACID properties ensure consistency.",
    "NoSQL databases handle unstructured data. MongoDB stores JSON documents. Cassandra provides wide-column storage. Redis offers in-memory caching.",
    "Database indexes speed up queries. Query planners optimize execution. Normalization reduces redundancy. Sharding distributes data across servers.",
    "Transactions maintain data integrity. Deadlocks occur when processes block each other. Replication creates backup copies. Backups protect against data loss.",
    "Graph databases model relationships. Neo4j uses nodes and edges. Cypher queries traverse connections. Social networks analyze friend graphs.",
    "Full-text search indexes documents. Elasticsearch scales horizontally. Inverted indexes map terms to docs. Relevance scoring ranks results.",
    "Object-relational mappers abstract SQL. Hibernate maps Java classes. Django ORM provides Python interface. Migrations evolve database schemas.",
    "Database connection pools reuse connections. Prepared statements prevent injection attacks. ORM queries may produce N+1 problems. Caching reduces database load.",
    
    # Web dev (7 docs)
    "HTTP protocol enables web communication. GET requests retrieve resources. POST requests submit data. Status codes indicate results.",
    "REST APIs use standard methods. JSON formats API responses. Authentication verifies identity. Authorization controls access permissions.",
    "Frontend frameworks build user interfaces. React uses virtual DOM. Vue provides reactive bindings. Angular offers full MVC framework.",
    "JavaScript runs in browsers. Async await handles promises. Event listeners respond to clicks. DOM manipulation updates page content.",
    "Web servers handle HTTP requests. Nginx serves static files. Load balancers distribute traffic. CDNs cache content globally.",
    "Microservices split monoliths. Containers package applications. Kubernetes orchestrates deployments. Docker images provide environment consistency.",
    "API gateways route requests. Rate limiting prevents abuse. GraphQL allows flexible queries. Webhooks push event notifications.",
    
    # Cloud/DevOps (7 docs)
    "Cloud providers offer infrastructure. AWS provides EC2 instances. Azure hosts virtual machines. GCP offers compute engine.",
    "Infrastructure as code defines resources. Terraform manages cloud state. CloudFormation templates create stacks. Pulumi uses programming languages.",
    "CI/CD pipelines automate deployment. Jenkins runs build jobs. GitHub Actions triggers workflows. CircleCI provides cloud-based testing.",
    "Monitoring tracks system health. Prometheus collects metrics. Grafana creates dashboards. Alertmanager sends notifications.",
    "Logging aggregates application events. ELK stack indexes logs. Splunk analyzes machine data. Structured logging aids debugging.",
    "Containers isolate processes. Docker images include dependencies. Dockerfile defines build steps. Multi-stage builds reduce image size.",
    "Serverless computing runs functions. Lambda executes event handlers. API Gateway triggers Lambdas. Cold starts affect latency.",
    
    # Security (6 docs)
    "Encryption protects data confidentiality. AES provides symmetric encryption. RSA uses public-private keys. TLS secures network connections.",
    "Hashing verifies data integrity. SHA-256 generates fixed-length digests. Salting prevents rainbow table attacks. bcrypt hashes passwords slowly.",
    "Firewalls filter network traffic. WAFs protect web applications. IDS detects intrusions. IPS blocks malicious activity.",
    "Vulnerabilities expose attack surfaces. SQL injection manipulates queries. XSS executes malicious scripts. CSRF forges cross-site requests.",
    "Penetration testing finds weaknesses. Bug bounties reward researchers. CVEs track known vulnerabilities. Patches fix security holes.",
    "Zero trust verifies every request. MFA requires multiple factors. Biometrics use physical characteristics. Hardware keys provide strong authentication.",
    
    # Data Science (6 docs)
    "Pandas manipulates tabular data. DataFrames organize information. Groupby aggregates statistics. Merge combines datasets.",
    "NumPy performs array operations. Broadcasting applies functions element-wise. Vectorization speeds calculations. Linear algebra solves equations.",
    "Visualization reveals patterns. Matplotlib creates static plots. Seaborn adds statistical styling. Plotly builds interactive charts.",
    "Statistical analysis infers populations. Hypothesis testing calculates p-values. Confidence intervals estimate ranges. Correlation measures relationships.",
    "Feature engineering improves models. One-hot encoding categorizes variables. Scaling normalizes ranges. PCA reduces dimensionality.",
    "Neural networks learn representations. Backpropagation calculates gradients. Activation functions introduce non-linearity. Dropout prevents overfitting.",
]

# Mapping of test questions to correct document IDs
# This allows consistent evaluation across all days
test_questions = [
    # Acronym problem: "ML" won't match "machine learning"
    {"question": "What is ML?", "expected": "Machine learning, a subset of AI, enables systems to learn from data", "correct_doc_id": 0},
    # Synonym problem: "automobiles" won't match "cars"
    {"question": "How do automobiles work?", "expected": "Cars use internal combustion engines to convert fuel into mechanical energy", "correct_doc_id": 8},
    # Semantic gap: "fix errors" won't match "debugging" and "resolving defects"
    {"question": "How to fix code errors?", "expected": "Debugging involves identifying and resolving software defects", "correct_doc_id": 16},
    # Acronym problem: "RAG" won't match "Retrieval-Augmented Generation"
    {"question": "What is RAG?", "expected": "Retrieval-Augmented Generation combines retrieval with language models", "correct_doc_id": 24},
]

# Document categories for analysis
doc_categories = {
    0: "CORRECT (ML definition)",
    1: "BM25_TRAP (keyword stuffed)",
    2: "BM25_TRAP (history)",
    3: "VECTOR_TRAP (AI broadly)",
    4: "VECTOR_TRAP (applications)",
    5: "VECTOR_TRAP (education)",
    6: "HYBRID_CHALLENGE (partial)",
    7: "NOISE",
    8: "CORRECT (car mechanism)",
    9: "BM25_TRAP (buying)",
    10: "BM25_TRAP (legal)",
    11: "VECTOR_TRAP (transportation)",
    12: "VECTOR_TRAP (electric vehicles)",
    13: "VECTOR_TRAP (manufacturing)",
    14: "HYBRID_CHALLENGE (parts)",
    15: "NOISE",
    16: "CORRECT (debugging)",
    17: "BM25_TRAP (nonsense keywords)",
    18: "BM25_TRAP (prevention)",
    19: "VECTOR_TRAP (error types)",
    20: "VECTOR_TRAP (testing)",
    21: "VECTOR_TRAP (performance)",
    22: "HYBRID_CHALLENGE (tools)",
    23: "NOISE",
    24: "CORRECT (RAG definition)",
    25: "BM25_TRAP (fashion)",
    26: "BM25_TRAP (memory errors)",
    27: "VECTOR_TRAP (LLMs broadly)",
    28: "VECTOR_TRAP (search engines)",
    29: "VECTOR_TRAP (knowledge systems)",
    30: "HYBRID_CHALLENGE (components)",
    31: "NOISE",
}

def get_doc_category(doc_id: int) -> str:
    """Get the category label for a document ID."""
    return doc_categories.get(doc_id, "FILLER")

def is_correct_doc(doc_id: int, query_idx: int) -> bool:
    """Check if document is the correct answer for a given query."""
    correct_ids = [0, 8, 16, 24]
    return doc_id == correct_ids[query_idx]

# Corpus metadata
CORPUS_SIZE = len(documents)
NUM_TEST_QUERIES = len(test_questions)
NUM_FILLER_DOCS = CORPUS_SIZE - (NUM_TEST_QUERIES * 8)  # 8 docs per query section

if __name__ == "__main__":
    print(f"RAG Workshop Corpus")
    print(f"==================")
    print(f"Total documents: {CORPUS_SIZE}")
    print(f"Test queries: {NUM_TEST_QUERIES}")
    print(f"Filler documents: {NUM_FILLER_DOCS}")
    print()
    print("Test questions and correct doc IDs:")
    for i, q in enumerate(test_questions):
        print(f"  {i+1}. '{q['question']}' -> Doc #{q['correct_doc_id']}")
