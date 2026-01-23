"""
Qdrant-based vector store for cognitive health knowledge base
Supports both in-memory and server modes
"""

import os
import json
from pathlib import Path
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI


class VectorStore:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        
        # Qdrant configuration
        qdrant_url = os.getenv('QDRANT_URL', '').strip()
        qdrant_api_key = os.getenv('QDRANT_API_KEY', '').strip()
        self.collection_name = os.getenv('QDRANT_COLLECTION', 'cognitive_health')
        
        # Initialize Qdrant client (in-memory if no URL provided)
        if qdrant_url:
            self.qdrant_client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key if qdrant_api_key else None
            )
            print(f"Connected to Qdrant at {qdrant_url}")
        else:
            self.qdrant_client = QdrantClient(":memory:")
            print("Using in-memory Qdrant")
        
        # Initialize collection
        self._initialize_collection()
        
        # Load knowledge base
        self._load_knowledge_base()
    
    def _initialize_collection(self):
        """Create or get Qdrant collection"""
        try:
            # Try to get existing collection
            self.qdrant_client.get_collection(self.collection_name)
            print(f"Using existing Qdrant collection: {self.collection_name}")
        except Exception:
            # Create new collection if it doesn't exist
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            print(f"Created new Qdrant collection: {self.collection_name}")
    
    def _load_knowledge_base(self):
        """Load knowledge from JSON files and index them"""
        data_dir = 'data'
        
        knowledge_files = [
            'vascular_health_rules.json',
            'lifestyle_rules.json',
            'sleep_rules.json'
        ]
        
        documents = []
        points = []
        point_id = 1
        
        for filename in knowledge_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    domain = filename.replace('_rules.json', '')
                    
                    # Process based on file type
                    if isinstance(data, dict):
                        for key, content in data.items():
                            if isinstance(content, dict):
                                text = self._format_content(content, key)
                            else:
                                text = str(content)
                            
                            documents.append({
                                'text': text,
                                'domain': domain,
                                'source': filename,
                                'key': key
                            })
                    
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                text = self._format_content(item, '')
                            else:
                                text = str(item)
                            
                            documents.append({
                                'text': text,
                                'domain': domain,
                                'source': filename
                            })
                
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        # Embed and index all documents
        if documents:
            print(f"Indexing {len(documents)} documents...")
            self._embed_and_index_documents(documents)
    
    def _format_content(self, content: dict, key: str) -> str:
        """Format dictionary content into readable text"""
        lines = []
        if key:
            lines.append(f"{key}:")
        
        for k, v in content.items():
            if isinstance(v, dict):
                lines.append(f"  {k}:")
                for sub_k, sub_v in v.items():
                    lines.append(f"    {sub_k}: {sub_v}")
            elif isinstance(v, list):
                lines.append(f"  {k}: {', '.join(map(str, v))}")
            else:
                lines.append(f"  {k}: {v}")
        
        return '\n'.join(lines)
    
    def _embed_and_index_documents(self, documents: List[Dict]):
        """Embed documents and index them in Qdrant"""
        try:
            # Extract texts for embedding
            texts = [doc['text'] for doc in documents]
            
            # Get embeddings from OpenAI
            embeddings = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            ).data
            
            # Prepare points for Qdrant
            points = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                point_id = i + 1
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding.embedding,
                        payload={
                            'text': doc['text'],
                            'domain': doc['domain'],
                            'source': doc['source'],
                            'key': doc.get('key', '')
                        }
                    )
                )
            
            # Upload to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            print(f"Indexed {len(points)} documents in Qdrant")
        
        except Exception as e:
            print(f"Error embedding and indexing documents: {e}")
    
    def search(self, query: str, k: int = 5, threshold: float = 0.3) -> List[Dict]:
        """
        Search for similar documents using Qdrant
        
        Args:
            query: Search query
            k: Number of results to return
            threshold: Minimum similarity threshold
        
        Returns:
            List of similar documents with metadata
        """
        try:
            # Get query embedding
            query_embedding = self.client.embeddings.create(
                model=self.embedding_model,
                input=[query]
            ).data[0].embedding
            
            # Search Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                score_threshold=threshold
            )
            
            results = []
            for hit in search_results:
                results.append({
                    'content': hit.payload.get('text', ''),
                    'similarity': hit.score,
                    'metadata': {
                        'domain': hit.payload.get('domain', ''),
                        'source': hit.payload.get('source', ''),
                        'key': hit.payload.get('key', '')
                    }
                })
            
            # If no results above threshold, lower it and try again
            if len(results) == 0:
                search_results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=k,
                    score_threshold=0.1
                )
                
                for hit in search_results:
                    results.append({
                        'content': hit.payload.get('text', ''),
                        'similarity': hit.score,
                        'metadata': {
                            'domain': hit.payload.get('domain', ''),
                            'source': hit.payload.get('source', ''),
                            'key': hit.payload.get('key', '')
                        }
                    })
            
            return results[:k]
        
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def search_by_domain(self, domain: str, k: int = 5) -> List[Dict]:
        """Search documents by domain"""
        try:
            # Scroll through collection with domain filter
            points, _ = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                query_filter={
                    "must": [
                        {
                            "key": "domain",
                            "match": {
                                "value": domain
                            }
                        }
                    ]
                },
                limit=k
            )
            
            results = []
            for point in points:
                results.append({
                    'content': point.payload.get('text', ''),
                    'metadata': {
                        'domain': point.payload.get('domain', ''),
                        'source': point.payload.get('source', ''),
                        'key': point.payload.get('key', '')
                    }
                })
            
            return results
        
        except Exception as e:
            print(f"Error searching by domain: {e}")
            return []
    
    def get_recommendations(self, user_profile: Dict) -> List[Dict]:
        """
        Get personalized recommendations based on user profile
        
        Args:
            user_profile: Dictionary with user health information
        
        Returns:
            List of relevant recommendations
        """
        recommendations = []
        
        # Build search queries based on profile
        queries = []
        
        if user_profile.get('processing_speed_low'):
            queries.append("processing speed cognitive decline brain health")
        
        if user_profile.get('hypertension'):
            queries.append("hypertension blood pressure SPRINT MIND cognitive")
        
        if user_profile.get('high_cholesterol'):
            queries.append("cholesterol lipid management cardiovascular cognitive")
        
        if user_profile.get('diabetes'):
            queries.append("diabetes glucose control cognitive health")
        
        if user_profile.get('sedentary'):
            queries.append("physical activity exercise aerobic cognitive benefit")
        
        if user_profile.get('poor_sleep'):
            queries.append("sleep quality sleep optimization cognitive function")
        
        # Search for each query and collect results
        seen_content = set()
        for query in queries:
            results = self.search(query, k=3)
            for result in results:
                content_hash = hash(result['content'])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    recommendations.append(result)
        
        return recommendations


def initialize_vector_store() -> VectorStore:
    """Initialize and return vector store"""
    return VectorStore()
