import json
import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    """FAISS-based vector store for multivitamin knowledge retrieval."""
    
    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        """
        Initialize the vector store.
        
        Args:
            knowledge_base_dir: Directory to store vector index and metadata
        """
        self.knowledge_base_dir = knowledge_base_dir
        self.index_path = os.path.join(knowledge_base_dir, "faiss_index.bin")
        self.metadata_path = os.path.join(knowledge_base_dir, "metadata.pkl")
        self.documents_path = os.path.join(knowledge_base_dir, "documents.pkl")
        
        # Set up HuggingFace authentication
        hf_token = os.getenv('HF_TOKEN')
        if hf_token:
            os.environ['HUGGINGFACE_HUB_TOKEN'] = hf_token
        
        # Initialize sentence transformer for embeddings
        try:
            # Try the correct model name first
            self.encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', use_auth_token=hf_token)
        except Exception as e:
            logger.warning(f"Failed to load sentence-transformers/all-MiniLM-L6-v2, trying alternative: {e}")
            try:
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2', use_auth_token=hf_token)
            except Exception as e2:
                logger.warning(f"Failed to load all-MiniLM-L6-v2, using fallback: {e2}")
                # Use a reliable fallback model
                self.encoder = SentenceTransformer('paraphrase-MiniLM-L6-v2', use_auth_token=hf_token)
                
        self.embedding_dim = 384  # Dimension for MiniLM models
        
        # Initialize FAISS index
        self.index = None
        self.documents = []
        self.metadata = []
        
        # Create knowledge base directory if it doesn't exist
        os.makedirs(knowledge_base_dir, exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def _create_documents_from_knowledge(self, knowledge_data: Dict) -> List[Dict]:
        """
        Convert multivitamin knowledge data into searchable documents.
        
        Args:
            knowledge_data: Loaded multivitamin knowledge JSON
            
        Returns:
            List of document dictionaries
        """
        documents = []
        
        # Process individual multivitamins
        for vitamin in knowledge_data.get('multivitamins', []):
            # Main vitamin document
            doc_text = f"""
            Vitamin: {vitamin['name']}
            Category: {vitamin['category']}
            Description: {vitamin['description']}
            Cognitive Benefits: {', '.join(vitamin['cognitive_benefits'])}
            Target Conditions: {', '.join(vitamin['target_conditions'])}
            Dosage: {vitamin['dosage']}
            Evidence Level: {vitamin['evidence_level']}
            Sources: {', '.join(vitamin['sources'])}
            """
            
            documents.append({
                'text': doc_text.strip(),
                'type': 'vitamin',
                'name': vitamin['name'],
                'category': vitamin['category'],
                'metadata': vitamin
            })
            
            # Create separate documents for each cognitive benefit
            for benefit in vitamin['cognitive_benefits']:
                benefit_doc = f"""
                {vitamin['name']} provides cognitive benefit: {benefit}
                Category: {vitamin['category']}
                Description: {vitamin['description']}
                Dosage: {vitamin['dosage']}
                Evidence: {vitamin['evidence_level']}
                """
                
                documents.append({
                    'text': benefit_doc.strip(),
                    'type': 'benefit',
                    'vitamin_name': vitamin['name'],
                    'benefit': benefit,
                    'metadata': vitamin
                })
            
            # Create documents for target conditions
            for condition in vitamin['target_conditions']:
                condition_doc = f"""
                For {condition.replace('_', ' ')}: {vitamin['name']} is recommended
                Benefits: {', '.join(vitamin['cognitive_benefits'])}
                Dosage: {vitamin['dosage']}
                Category: {vitamin['category']}
                Evidence Level: {vitamin['evidence_level']}
                """
                
                documents.append({
                    'text': condition_doc.strip(),
                    'type': 'condition',
                    'condition': condition,
                    'vitamin_name': vitamin['name'],
                    'metadata': vitamin
                })
        
        # Process combinations
        for combo in knowledge_data.get('combinations', []):
            combo_doc = f"""
            Combination: {combo['name']}
            Components: {', '.join(combo['components'])}
            Target: {combo['target']}
            Synergy: {combo['synergy']}
            """
            
            documents.append({
                'text': combo_doc.strip(),
                'type': 'combination',
                'name': combo['name'],
                'components': combo['components'],
                'metadata': combo
            })
        
        return documents
    
    def build_index(self, data_dir: str = "data"):
        """
        Build FAISS index from multivitamin knowledge data.
        
        Args:
            data_dir: Directory containing knowledge JSON files
        """
        logger.info("Building FAISS index from knowledge base...")
        
        # Load multivitamin knowledge
        knowledge_path = os.path.join(data_dir, "multivitamin_knowledge.json")
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)
        
        # Create documents
        documents = self._create_documents_from_knowledge(knowledge_data)
        
        # Extract texts for embedding
        texts = [doc['text'] for doc in documents]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.encoder.encode(texts, show_progress_bar=True)
        
        # Create FAISS index
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        self.index.add(embeddings.astype('float32'))
        
        # Store documents and metadata
        self.documents = documents
        self.metadata = [doc['metadata'] for doc in documents]
        
        # Save index and metadata
        self._save_index()
        
        logger.info(f"FAISS index built successfully with {len(documents)} documents")
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            logger.info("Index and metadata saved successfully")
    
    def _load_index(self):
        """Load FAISS index and metadata from disk."""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                
                with open(self.documents_path, 'rb') as f:
                    self.documents = pickle.load(f)
                
                logger.info(f"Loaded existing index with {len(self.documents)} documents")
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}")
                self.index = None
                self.documents = []
                self.metadata = []
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for relevant documents using semantic similarity.
        
        Args:
            query: Search query
            k: Number of top results to return
            
        Returns:
            List of relevant documents with similarity scores
        """
        if self.index is None or len(self.documents) == 0:
            logger.warning("Index not built. Please build index first.")
            return []
        
        # Encode query
        query_embedding = self.encoder.encode([query])
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Prepare results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                result = self.documents[idx].copy()
                result['similarity_score'] = float(score)
                results.append(result)
        
        return results
    
    def search_by_condition(self, condition: str, k: int = 3) -> List[Dict]:
        """
        Search for vitamins that target a specific condition.
        
        Args:
            condition: Target condition (e.g., "memory_loss", "attention_deficit")
            k: Number of results to return
            
        Returns:
            List of relevant vitamin recommendations
        """
        query = f"vitamins for {condition.replace('_', ' ')} cognitive impairment treatment"
        results = self.search(query, k)
        
        # Filter for vitamin and condition type documents
        filtered_results = [r for r in results if r['type'] in ['vitamin', 'condition']]
        
        return filtered_results[:k]
    
    def search_by_cognitive_domain(self, domain: str, k: int = 3) -> List[Dict]:
        """
        Search for vitamins that support a specific cognitive domain.
        
        Args:
            domain: Cognitive domain (e.g., "memory", "attention", "processing_speed")
            k: Number of results to return
            
        Returns:
            List of relevant vitamin recommendations
        """
        query = f"vitamins supplements for {domain.replace('_', ' ')} cognitive function improvement"
        results = self.search(query, k)
        
        return results[:k]
    
    def get_vitamin_details(self, vitamin_name: str) -> Optional[Dict]:
        """
        Get detailed information about a specific vitamin.
        
        Args:
            vitamin_name: Name of the vitamin
            
        Returns:
            Vitamin details dictionary or None if not found
        """
        for doc in self.documents:
            if doc['type'] == 'vitamin' and doc['name'].lower() == vitamin_name.lower():
                return doc['metadata']
        
        return None
    
    def get_combinations(self, vitamin_names: List[str]) -> List[Dict]:
        """
        Find relevant vitamin combinations based on individual vitamins.
        
        Args:
            vitamin_names: List of vitamin names
            
        Returns:
            List of relevant combination documents
        """
        combinations = []
        for doc in self.documents:
            if doc['type'] == 'combination':
                # Check if any of the requested vitamins are in this combination
                combo_components = [comp.lower() for comp in doc['components']]
                if any(vit.lower() in comp.lower() for vit in vitamin_names for comp in combo_components):
                    combinations.append(doc)
        
        return combinations
    
    def rebuild_index_if_needed(self):
        """Rebuild index if it doesn't exist."""
        if self.index is None or len(self.documents) == 0:
            logger.info("No existing index found. Building new index...")
            self.build_index()

if __name__ == "__main__":
    # Initialize and build vector store
    vector_store = VectorStore()
    
    # Build index if needed
    if vector_store.index is None:
        vector_store.build_index()
    
    # Test search functionality
    test_queries = [
        "vitamins for memory problems",
        "supplements for attention deficit",
        "cognitive enhancement nutrients",
        "brain fog treatment"
    ]
    
    print("Testing vector store search:")
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = vector_store.search(query, k=3)
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.get('vitamin_name', result.get('name', 'Unknown'))} "
                  f"(Score: {result['similarity_score']:.3f})")
            print(f"   Type: {result['type']}")