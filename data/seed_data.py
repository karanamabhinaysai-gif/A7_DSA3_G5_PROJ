#!/usr/bin/env python3
"""
Seed script — populates the SQLite database with sample research papers,
citations, users, and reading history for development and testing.

Usage:
    python data/seed_data.py
"""

import hashlib
import os
import sqlite3
import sys

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "database", "papers.db")
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "database", "schema.sql")


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ── Sample Papers ──────────────────────────────────────────────────────────
PAPERS = [
    # Machine Learning (1-5)
    (1, "A Survey of Machine Learning Approaches for Classification",
     "This survey reviews modern machine learning algorithms for classification tasks including SVMs, random forests, and gradient boosting. We compare their performance across standard benchmarks.",
     "J. Smith, A. Johnson", 2019, "machine learning, classification, SVM, random forest", "ICML", "10.1000/ml001"),
    (2, "Gradient Boosting Machines: A Tutorial",
     "We provide a comprehensive tutorial on gradient boosting methods covering XGBoost, LightGBM, and CatBoost. Practical guidelines for hyperparameter tuning are presented.",
     "R. Chen, M. Williams", 2020, "gradient boosting, XGBoost, ensemble learning", "NeurIPS", "10.1000/ml002"),
    (3, "Transfer Learning in Practice",
     "This paper demonstrates effective transfer learning strategies for scenarios with limited labeled data. Domain adaptation and fine-tuning techniques are evaluated across multiple tasks.",
     "L. Zhang, K. Patel", 2021, "transfer learning, domain adaptation, fine-tuning", "ICML", "10.1000/ml003"),
    (4, "Federated Learning: Challenges and Solutions",
     "We address privacy-preserving machine learning through federated learning. Communication efficiency and model aggregation strategies are analyzed.",
     "P. Brown, S. Lee", 2022, "federated learning, privacy, distributed ML", "NeurIPS", "10.1000/ml004"),
    (5, "AutoML: Automated Machine Learning Pipeline Design",
     "AutoML systems that automate feature engineering, model selection, and hyperparameter optimization are surveyed. We benchmark several open-source AutoML frameworks.",
     "T. Garcia, N. Kumar", 2023, "AutoML, hyperparameter optimization, neural architecture search", "ICML", "10.1000/ml005"),

    # Deep Learning (6-10)
    (6, "Deep Residual Learning for Image Recognition",
     "We present residual learning framework to ease training of very deep networks. Identity shortcut connections enable training of networks with 100+ layers.",
     "K. He, X. Zhang, S. Ren", 2018, "deep learning, residual networks, image recognition, ResNet", "CVPR", "10.1000/dl001"),
    (7, "Attention Is All You Need: The Transformer Architecture",
     "We propose the Transformer, a novel architecture based entirely on attention mechanisms. It achieves state-of-the-art results in machine translation without recurrence.",
     "A. Vaswani, N. Shazeer, N. Parmar", 2019, "transformer, attention mechanism, sequence modeling", "NeurIPS", "10.1000/dl002"),
    (8, "Generative Adversarial Networks: A Comprehensive Review",
     "This review covers GAN architectures, training techniques, and applications in image synthesis, super-resolution, and data augmentation.",
     "I. Goodfellow, J. Pouget-Abadie", 2020, "GAN, generative models, image synthesis, deep learning", "ICLR", "10.1000/dl003"),
    (9, "Self-Supervised Learning: Methods and Applications",
     "Self-supervised approaches that learn representations from unlabeled data are surveyed. Contrastive learning and masked prediction methods are compared.",
     "Y. LeCun, M. Chen", 2022, "self-supervised learning, contrastive learning, representation learning", "ICML", "10.1000/dl004"),
    (10, "Neural Architecture Search with Reinforcement Learning",
     "We use reinforcement learning to discover optimal neural network architectures. The method finds architectures competitive with hand-designed networks.",
     "B. Zoph, Q. Le", 2021, "neural architecture search, reinforcement learning, deep learning", "ICLR", "10.1000/dl005"),

    # NLP (11-15)
    (11, "BERT: Pre-training of Deep Bidirectional Transformers",
     "BERT introduces bidirectional pre-training for language representations. Fine-tuning BERT achieves state-of-the-art on eleven NLP tasks.",
     "J. Devlin, M. Chang, K. Lee", 2019, "BERT, NLP, pre-training, language model", "NAACL", "10.1000/nlp001"),
    (12, "Sentiment Analysis Using Deep Learning Techniques",
     "We compare CNN, LSTM, and Transformer-based approaches for sentiment analysis. Attention-based models show superior performance on review datasets.",
     "D. Kim, Y. Park", 2020, "sentiment analysis, deep learning, NLP, text classification", "ACL", "10.1000/nlp002"),
    (13, "Named Entity Recognition with Conditional Random Fields",
     "This work combines BiLSTM networks with CRF layers for named entity recognition. Character-level embeddings improve recognition of rare entities.",
     "G. Lample, M. Ballesteros", 2019, "NER, CRF, sequence labeling, NLP", "EMNLP", "10.1000/nlp003"),
    (14, "Text Summarization: Extractive and Abstractive Approaches",
     "We compare extractive and abstractive summarization methods. Transformer-based abstractive models generate more coherent summaries than traditional methods.",
     "A. See, P. Liu, C. Manning", 2021, "text summarization, NLP, abstractive, extractive", "ACL", "10.1000/nlp004"),
    (15, "Question Answering Systems: A Survey",
     "This survey covers reading comprehension and open-domain question answering. We analyze retrieval-augmented and generative approaches.",
     "D. Chen, A. Fisch, J. Weston", 2022, "question answering, NLP, reading comprehension", "EMNLP", "10.1000/nlp005"),

    # Computer Vision (16-20)
    (16, "Object Detection with YOLO: Real-Time Performance",
     "YOLO frames detection as regression, enabling real-time object detection. We evaluate speed-accuracy tradeoffs across YOLO versions.",
     "J. Redmon, S. Divvala, R. Girshick", 2018, "object detection, YOLO, real-time, computer vision", "CVPR", "10.1000/cv001"),
    (17, "Semantic Segmentation Using Fully Convolutional Networks",
     "Fully convolutional networks adapt classification CNNs for dense pixel-wise prediction. Skip connections combine deep coarse features with shallow fine features.",
     "E. Shelhamer, J. Long, T. Darrell", 2019, "semantic segmentation, FCN, computer vision", "CVPR", "10.1000/cv002"),
    (18, "Image Super-Resolution with Deep Neural Networks",
     "We present deep learning methods for single-image super-resolution. Residual and adversarial training produce photorealistic high-resolution outputs.",
     "C. Dong, C. Loy, K. He", 2020, "super-resolution, deep learning, image enhancement", "ECCV", "10.1000/cv003"),
    (19, "3D Object Recognition from Point Clouds",
     "PointNet directly processes point cloud data for 3D classification and segmentation. The architecture is invariant to input permutations.",
     "C. Qi, H. Su, K. Mo", 2021, "3D recognition, point clouds, PointNet, computer vision", "CVPR", "10.1000/cv004"),
    (20, "Vision Transformers for Image Classification",
     "We apply Transformer architectures directly to sequences of image patches. Vision Transformers achieve competitive results with significantly less inductive bias.",
     "A. Dosovitskiy, L. Beyer, A. Kolesnikov", 2022, "vision transformer, ViT, image classification, attention", "ICLR", "10.1000/cv005"),

    # Distributed Systems (21-25)
    (21, "MapReduce: Simplified Data Processing on Large Clusters",
     "MapReduce provides a programming model for processing large datasets in parallel. Automatic partitioning, scheduling, and fault tolerance are handled by the runtime.",
     "J. Dean, S. Ghemawat", 2018, "MapReduce, distributed computing, parallel processing", "OSDI", "10.1000/ds001"),
    (22, "Consensus Algorithms in Distributed Systems",
     "We survey Paxos, Raft, and Byzantine fault-tolerant consensus protocols. Performance comparisons under various network conditions are presented.",
     "D. Ongaro, J. Ousterhout", 2019, "consensus, Raft, Paxos, distributed systems", "USENIX ATC", "10.1000/ds002"),
    (23, "Microservices Architecture: Patterns and Best Practices",
     "This paper analyzes design patterns for microservices including service discovery, circuit breakers, and API gateways. Migration strategies from monoliths are discussed.",
     "S. Newman, M. Fowler", 2021, "microservices, architecture, distributed systems", "ICSE", "10.1000/ds003"),
    (24, "Stream Processing Systems: A Comparative Study",
     "We compare Apache Kafka, Flink, and Spark Streaming for real-time data processing. Latency, throughput, and fault tolerance tradeoffs are evaluated.",
     "T. Akidau, R. Bradshaw", 2022, "stream processing, Kafka, Flink, real-time", "VLDB", "10.1000/ds004"),
    (25, "Container Orchestration with Kubernetes",
     "Kubernetes architecture for container orchestration is examined. Auto-scaling, service mesh, and deployment strategies are benchmarked.",
     "B. Burns, J. Beda, K. Hightower", 2023, "Kubernetes, containers, orchestration, cloud", "SoCC", "10.1000/ds005"),

    # Database Systems (26-30)
    (26, "NewSQL Databases: Combining NoSQL Scalability with SQL",
     "NewSQL databases provide ACID transactions at NoSQL-like scale. We compare CockroachDB, TiDB, and Google Spanner architectures.",
     "A. Pavlo, M. Aslett", 2019, "NewSQL, database, distributed transactions, scalability", "SIGMOD", "10.1000/db001"),
    (27, "Graph Databases: Modeling and Querying Complex Networks",
     "We survey graph database models including property graphs and RDF. Query languages like Cypher and SPARQL are compared.",
     "R. Angles, C. Gutierrez", 2020, "graph database, Neo4j, SPARQL, network analysis", "VLDB", "10.1000/db002"),
    (28, "Query Optimization in Modern Database Systems",
     "Advanced query optimization techniques including adaptive query processing and learned optimizers are reviewed. Cost model improvements are benchmarked.",
     "V. Leis, A. Gubichev, A. Kemper", 2021, "query optimization, database, cost estimation", "SIGMOD", "10.1000/db003"),
    (29, "Time-Series Databases for IoT Applications",
     "Time-series databases optimized for IoT workloads are analyzed. Compression, retention policies, and downsampling strategies are evaluated.",
     "E. Lindstrom, P. Boncz", 2022, "time-series, IoT, database, InfluxDB", "VLDB", "10.1000/db004"),
    (30, "Learned Index Structures",
     "We propose replacing traditional B-tree indexes with neural network models. Learned indexes reduce storage and can improve lookup time.",
     "T. Kraska, A. Beutel, E. Chi", 2020, "learned indexes, machine learning, database, B-tree", "SIGMOD", "10.1000/db005"),

    # Computer Networks (31-35)
    (31, "Software-Defined Networking: A Comprehensive Survey",
     "SDN separates the control plane from the data plane enabling programmable networks. OpenFlow protocol and controller architectures are discussed.",
     "D. Kreutz, F. Ramos, P. Verissimo", 2018, "SDN, OpenFlow, network architecture", "IEEE Comm. Surveys", "10.1000/net001"),
    (32, "Network Function Virtualization: State of the Art",
     "NFV replaces dedicated network hardware with software functions on commodity servers. Performance, reliability, and deployment challenges are analyzed.",
     "R. Mijumbi, J. Serrat, J. Gorricho", 2019, "NFV, virtualization, network functions", "IEEE Comm. Surveys", "10.1000/net002"),
    (33, "Deep Learning for Network Traffic Classification",
     "Deep learning models classify encrypted network traffic without payload inspection. CNN and RNN architectures outperform traditional DPI methods.",
     "M. Lopez-Martin, B. Carro", 2021, "traffic classification, deep learning, network security", "IEEE TNSM", "10.1000/net003"),
    (34, "Edge Computing: Vision and Challenges",
     "Edge computing brings computation closer to data sources reducing latency. We survey architectures, offloading strategies, and IoT integration.",
     "W. Shi, J. Cao, Q. Zhang", 2022, "edge computing, IoT, latency, cloud", "IEEE IoT Journal", "10.1000/net004"),
    (35, "5G Network Slicing: Architecture and Management",
     "Network slicing in 5G creates virtual networks optimized for specific use cases. Resource allocation and slice lifecycle management are addressed.",
     "X. Foukas, G. Patounas, A. Elmokashfi", 2023, "5G, network slicing, virtualization", "IEEE Comm. Magazine", "10.1000/net005"),

    # Software Engineering (36-40)
    (36, "Technical Debt: A Software Engineering Perspective",
     "We define and categorize technical debt in software projects. Measurement frameworks and remediation strategies are proposed.",
     "P. Avgeriou, P. Kruchten, I. Ozkaya", 2019, "technical debt, software quality, maintenance", "IEEE Software", "10.1000/se001"),
    (37, "Continuous Integration and Continuous Deployment Practices",
     "CI/CD pipeline best practices are surveyed across open-source and industrial projects. Build optimization and test selection strategies are evaluated.",
     "M. Hilton, T. Tunnell, K. Huang", 2020, "CI/CD, DevOps, continuous integration, testing", "ICSE", "10.1000/se002"),
    (38, "Code Review Best Practices in Open Source Projects",
     "We analyze code review practices in large open-source projects. Reviewer assignment, review quality metrics, and tooling are studied.",
     "A. Bacchelli, C. Bird", 2021, "code review, software engineering, open source", "ICSE", "10.1000/se003"),
    (39, "Automated Bug Detection Using Static Analysis",
     "Static analysis tools for bug detection are compared. We evaluate precision, recall, and developer adoption across multiple languages.",
     "C. Sadowski, E. Aftandilian, A. Eagle", 2022, "static analysis, bug detection, program analysis", "ESEC/FSE", "10.1000/se004"),
    (40, "Machine Learning for Software Engineering Tasks",
     "We survey ML applications in code completion, bug prediction, and test generation. Large language models for code are benchmarked.",
     "D. Lo, X. Xia, L. Bao", 2023, "ML for SE, code generation, software engineering", "TSE", "10.1000/se005"),

    # Information Retrieval (41-45)
    (41, "Learning to Rank for Information Retrieval",
     "Learning to rank methods including pointwise, pairwise, and listwise approaches are surveyed. Neural ranking models outperform traditional IR methods.",
     "T. Liu, H. Li", 2019, "learning to rank, information retrieval, ranking", "SIGIR", "10.1000/ir001"),
    (42, "Dense Passage Retrieval for Open-Domain Question Answering",
     "Dense retrieval using dual-encoder architectures outperforms sparse BM25 retrieval. We pre-train encoders on natural question-answer pairs.",
     "V. Karpukhin, B. Oguz, S. Min", 2020, "dense retrieval, question answering, information retrieval", "EMNLP", "10.1000/ir002"),
    (43, "Knowledge Graphs for Enhanced Information Retrieval",
     "Knowledge graphs augment retrieval by capturing entity relationships. Entity linking and graph embeddings improve search relevance.",
     "L. Dietz, A. Kotov, E. Meij", 2021, "knowledge graphs, information retrieval, entity linking", "SIGIR", "10.1000/ir003"),
    (44, "Conversational Search: A Survey",
     "Conversational search systems that handle multi-turn queries are reviewed. Context modeling and clarification question generation are key challenges.",
     "H. Zamani, S. Dumais, N. Craswell", 2022, "conversational search, dialogue, information retrieval", "CHIIR", "10.1000/ir004"),
    (45, "Recommender Systems for Academic Literature",
     "Academic paper recommender systems using content, citation, and collaborative signals are surveyed. Hybrid approaches achieve best user satisfaction.",
     "B. Beel, B. Gipp, S. Langer", 2019, "recommender systems, academic literature, information retrieval", "JCDL", "10.1000/ir005"),

    # Data Mining (46-50)
    (46, "Deep Clustering: A Comprehensive Survey",
     "Deep learning-based clustering methods are reviewed. Autoencoder and GAN-based approaches learn cluster-friendly representations.",
     "E. Aljalbout, V. Golkov, Y. Siddiqui", 2020, "deep clustering, unsupervised learning, data mining", "KDD", "10.1000/dm001"),
    (47, "Anomaly Detection in Time Series Data",
     "We survey anomaly detection methods for temporal data. Statistical, ML, and deep learning approaches are compared on benchmark datasets.",
     "A. Blázquez-García, A. Conde, U. Mori", 2021, "anomaly detection, time series, data mining", "KDD", "10.1000/dm002"),
    (48, "Frequent Pattern Mining: Algorithms and Applications",
     "Classical and modern frequent pattern mining algorithms are reviewed. Scalable methods for large transaction databases are benchmarked.",
     "R. Agrawal, R. Srikant, J. Han", 2019, "frequent patterns, association rules, data mining", "ICDM", "10.1000/dm003"),
    (49, "Explainable AI: Methods for Understanding ML Models",
     "Interpretability methods including SHAP, LIME, and attention visualization are compared. We discuss tradeoffs between accuracy and explainability.",
     "C. Molnar, G. Casalicchio, B. Bischl", 2022, "explainable AI, interpretability, SHAP, LIME", "KDD", "10.1000/dm004"),
    (50, "Graph Mining: Patterns and Community Detection",
     "Graph mining methods for community detection, motif discovery, and influence analysis are surveyed. Scalable algorithms for billion-edge graphs are presented.",
     "J. Leskovec, A. Rajaraman, J. Ullman", 2021, "graph mining, community detection, social networks", "WWW", "10.1000/dm005"),
]

# ── Citation Relationships ─────────────────────────────────────────────────
# (citing_paper_id, cited_paper_id) — newer papers cite older/related ones
CITATIONS = [
    # ML papers citing each other
    (2, 1), (3, 1), (3, 2), (4, 1), (5, 1), (5, 2), (5, 3),
    # DL papers citing ML and each other
    (7, 6), (8, 6), (8, 7), (9, 7), (9, 6), (10, 6), (10, 7),
    # DL citing ML
    (6, 1), (7, 1), (9, 3),
    # NLP papers citing DL and each other
    (11, 7), (12, 7), (12, 11), (13, 11), (14, 7), (14, 11), (14, 12),
    (15, 11), (15, 14),
    # CV papers citing DL and each other
    (16, 6), (17, 6), (17, 16), (18, 6), (18, 8), (19, 6), (19, 17),
    (20, 7), (20, 6), (20, 16),
    # Distributed systems
    (22, 21), (23, 21), (23, 22), (24, 21), (25, 23), (25, 24),
    # Database systems
    (26, 21), (27, 26), (28, 26), (28, 27), (29, 26), (30, 1), (30, 28),
    # Networks
    (32, 31), (33, 31), (33, 1), (34, 31), (34, 32), (35, 31), (35, 34),
    # Software engineering
    (37, 36), (38, 36), (38, 37), (39, 36), (39, 37), (40, 1), (40, 5),
    (40, 39),
    # Information retrieval
    (41, 1), (42, 11), (42, 41), (43, 27), (43, 41), (44, 15), (44, 42),
    (45, 41), (45, 1),
    # Data mining
    (46, 6), (46, 9), (47, 1), (47, 46), (48, 1), (49, 1), (49, 5),
    (50, 27), (50, 48),
    # Cross-domain
    (33, 12), (40, 11), (42, 15), (30, 5), (49, 40),
]

# ── Sample Users ───────────────────────────────────────────────────────────
USERS = [
    ("alice",   "alice123",   "machine learning, deep learning, neural networks"),
    ("bob",     "bob123",     "natural language processing, information retrieval, text mining"),
    ("charlie", "charlie123", "computer vision, image recognition, deep learning"),
]

# ── Sample History ─────────────────────────────────────────────────────────
USER_HISTORY = [
    # alice viewed ML/DL papers
    (1, 1, "viewed"), (1, 2, "viewed"), (1, 3, "saved"),
    (1, 6, "viewed"), (1, 7, "saved"), (1, 9, "viewed"),
    # bob viewed NLP/IR papers
    (2, 11, "viewed"), (2, 12, "saved"), (2, 14, "viewed"),
    (2, 41, "viewed"), (2, 42, "saved"), (2, 45, "viewed"),
    # charlie viewed CV papers
    (3, 16, "viewed"), (3, 17, "saved"), (3, 18, "viewed"),
    (3, 19, "viewed"), (3, 20, "saved"), (3, 6, "viewed"),
]


def seed_database():
    """Create and populate the database with sample data."""
    # Ensure database directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Remove existing DB to start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Run schema
    with open(SCHEMA_PATH, "r") as f:
        cursor.executescript(f.read())
    print("Schema created successfully.")

    # Insert papers
    cursor.executemany(
        "INSERT INTO papers (id, title, abstract, authors, year, keywords, venue, doi) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        PAPERS,
    )
    print(f"Inserted {len(PAPERS)} papers.")

    # Insert citations
    cursor.executemany(
        "INSERT INTO citations (citing_paper_id, cited_paper_id) VALUES (?, ?)",
        CITATIONS,
    )
    print(f"Inserted {len(CITATIONS)} citation relationships.")

    # Insert users
    for username, password, interests in USERS:
        cursor.execute(
            "INSERT INTO users (username, password_hash, interests) VALUES (?, ?, ?)",
            (username, _hash_password(password), interests),
        )
    print(f"Inserted {len(USERS)} users.")

    # Insert history
    cursor.executemany(
        "INSERT INTO user_history (user_id, paper_id, action) VALUES (?, ?, ?)",
        USER_HISTORY,
    )
    print(f"Inserted {len(USER_HISTORY)} history entries.")

    conn.commit()
    conn.close()

    print(f"\nDatabase seeded successfully at: {DB_PATH}")
    print(f"  Papers:    {len(PAPERS)}")
    print(f"  Citations: {len(CITATIONS)}")
    print(f"  Users:     {len(USERS)}")
    print(f"  History:   {len(USER_HISTORY)}")


if __name__ == "__main__":
    seed_database()
