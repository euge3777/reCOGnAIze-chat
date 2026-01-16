#!/usr/bin/env python3
"""
Multivitamin Recommendation Chatbot
Main application entry point

Usage:
    python app.py                    # Run Streamlit app
    python app.py --test             # Run system tests
    python app.py --build-index     # Rebuild vector index
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_streamlit_app():
    """Launch the Streamlit chatbot interface."""
    print("🌟 Starting Multivitamin Recommendation Chatbot...")
    print("📱 The app will open in your browser shortly...")
    
    # Path to the chatbot module
    chatbot_path = os.path.join(os.path.dirname(__file__), 'src', 'chatbot.py')
    
    # Run streamlit
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', chatbot_path,
            '--theme.primaryColor=#667eea',
            '--theme.backgroundColor=#ffffff',
            '--theme.secondaryBackgroundColor=#f0f2f6',
            '--theme.textColor=#262730'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit app: {e}")
        print("💡 Make sure Streamlit is installed: pip install streamlit")
    except KeyboardInterrupt:
        print("\n👋 Shutting down the application...")

def run_tests():
    """Run system tests."""
    print("🧪 Running system tests...")
    
    try:
        from src.vector_store import VectorStore
        from src.rag_system import RAGRecommendationSystem
        from src.cognitive_analyzer import CognitiveTestAnalyzer
        
        # Test vector store
        print("Testing vector store...")
        vector_store = VectorStore()
        if vector_store.index is None:
            print("Building vector index...")
            vector_store.build_index()
        
        search_results = vector_store.search("memory problems", k=3)
        assert len(search_results) > 0, "Vector store search failed"
        print("✅ Vector store working correctly")
        
        # Test cognitive analyzer
        print("Testing cognitive analyzer...")
        analyzer = CognitiveTestAnalyzer()
        
        test_data = {
            "scores": {"memory": 65, "attention": 70, "processing_speed": 80, "executive_function": 75},
            "age": 35,
            "gender": "female"
        }
        
        analysis = analyzer.analyze_test_results(test_data)
        assert 'overall_assessment' in analysis, "Cognitive analysis failed"
        print("✅ Cognitive analyzer working correctly")
        
        # Test RAG system
        print("Testing RAG recommendation system...")
        rag_system = RAGRecommendationSystem()
        
        recommendations = rag_system.generate_recommendations(test_data)
        assert 'recommendations' in recommendations, "RAG system failed"
        print("✅ RAG system working correctly")
        
        print("🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def build_index():
    """Rebuild the vector index."""
    print("🔄 Rebuilding vector index...")
    
    try:
        from src.vector_store import VectorStore
        
        vector_store = VectorStore()
        vector_store.build_index()
        
        print("✅ Vector index rebuilt successfully!")
        
    except Exception as e:
        print(f"❌ Failed to rebuild index: {e}")

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("📋 Checking dependencies...")
    
    # Map package names to their import names
    package_imports = {
        'streamlit': 'streamlit',
        'faiss-cpu': 'faiss',
        'sentence-transformers': 'sentence_transformers',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'scikit-learn': 'sklearn'
    }
    
    missing_packages = []
    
    for package, import_name in package_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print(f"💡 Install them with: pip install {' '.join(missing_packages)}")
        return False
    else:
        print("✅ All dependencies are installed!")
        return True

def download_mistral_model():
    """Download Mistral model if not present."""
    print("🤖 Downloading Mistral-7B-Instruct-v0.3 model...")
    print("⚠️ This is a large download (several GB) and may take time.")
    
    try:
        from src.mistral_llm import download_mistral_model
        return download_mistral_model()
    except Exception as e:
        print(f"❌ Failed to download Mistral model: {e}")
        return False

def setup_project():
    """Set up the project for first run."""
    print("🚀 Setting up Multivitamin Recommendation Chatbot...")
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Please install missing dependencies first.")
        return False
    
    # Check data files
    data_dir = Path("data")
    required_files = ["multivitamin_knowledge.json", "cognitive_mapping.json"]
    
    for file_name in required_files:
        file_path = data_dir / file_name
        if not file_path.exists():
            print(f"❌ Missing data file: {file_path}")
            return False
    
    print("✅ Data files found")
    
    # Build vector index if needed
    try:
        from src.vector_store import VectorStore
        vector_store = VectorStore()
        if vector_store.index is None:
            print("📦 Building vector index for first time...")
            vector_store.build_index()
            print("✅ Vector index built successfully")
        else:
            print("✅ Vector index already exists")
    except Exception as e:
        print(f"❌ Error setting up vector index: {e}")
        return False
    
    print("🎉 Project setup complete!")
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Multivitamin Recommendation Chatbot")
    parser.add_argument("--test", action="store_true", help="Run system tests")
    parser.add_argument("--build-index", action="store_true", help="Rebuild vector index")
    parser.add_argument("--setup", action="store_true", help="Set up project")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")
    parser.add_argument("--download-mistral", action="store_true", help="Download Mistral model")
    
    args = parser.parse_args()
    
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    elif args.build_index:
        build_index()
    elif args.setup:
        success = setup_project()
        sys.exit(0 if success else 1)
    elif args.check_deps:
        success = check_dependencies()
        sys.exit(0 if success else 1)
    elif args.download_mistral:
        success = download_mistral_model()
        sys.exit(0 if success else 1)
    else:
        # Default: run the Streamlit app
        if setup_project():
            run_streamlit_app()
        else:
            print("❌ Setup failed. Please resolve issues before running the app.")
            sys.exit(1)

if __name__ == "__main__":
    main()