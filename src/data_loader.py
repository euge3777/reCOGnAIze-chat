"""
Data loader utility for the multivitamin recommendation system.
Handles loading and preprocessing of knowledge base data.
"""

import json
import os
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """Utility class for loading and managing knowledge base data."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize data loader.
        
        Args:
            data_dir: Directory containing data files
        """
        self.data_dir = data_dir
        self._validate_data_directory()
    
    def _validate_data_directory(self):
        """Validate that the data directory exists and contains required files."""
        if not os.path.exists(self.data_dir):
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        
        required_files = ["multivitamin_knowledge.json", "cognitive_mapping.json"]
        missing_files = []
        
        for file_name in required_files:
            file_path = os.path.join(self.data_dir, file_name)
            if not os.path.exists(file_path):
                missing_files.append(file_name)
        
        if missing_files:
            raise FileNotFoundError(f"Missing required data files: {missing_files}")
    
    def load_multivitamin_knowledge(self) -> Dict:
        """Load multivitamin knowledge base."""
        file_path = os.path.join(self.data_dir, "multivitamin_knowledge.json")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data.get('multivitamins', []))} vitamins and "
                       f"{len(data.get('combinations', []))} combinations")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load multivitamin knowledge: {e}")
            raise
    
    def load_cognitive_mapping(self) -> Dict:
        """Load cognitive domain mapping data."""
        file_path = os.path.join(self.data_dir, "cognitive_mapping.json")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            domains = len(data.get('cognitive_domains', {}))
            logger.info(f"Loaded cognitive mapping for {domains} domains")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load cognitive mapping: {e}")
            raise
    
    def get_vitamin_by_name(self, name: str) -> Optional[Dict]:
        """Get specific vitamin information by name."""
        knowledge = self.load_multivitamin_knowledge()
        
        for vitamin in knowledge.get('multivitamins', []):
            if vitamin['name'].lower() == name.lower():
                return vitamin
        
        return None
    
    def get_vitamins_by_category(self, category: str) -> List[Dict]:
        """Get all vitamins in a specific category."""
        knowledge = self.load_multivitamin_knowledge()
        
        return [
            vitamin for vitamin in knowledge.get('multivitamins', [])
            if vitamin['category'].lower() == category.lower()
        ]
    
    def get_vitamins_for_condition(self, condition: str) -> List[Dict]:
        """Get vitamins that target a specific condition."""
        knowledge = self.load_multivitamin_knowledge()
        
        matching_vitamins = []
        for vitamin in knowledge.get('multivitamins', []):
            target_conditions = [cond.lower() for cond in vitamin.get('target_conditions', [])]
            if condition.lower() in target_conditions:
                matching_vitamins.append(vitamin)
        
        return matching_vitamins
    
    def validate_data_integrity(self) -> Dict[str, List[str]]:
        """Validate the integrity of loaded data."""
        issues = {"warnings": [], "errors": []}
        
        try:
            # Validate multivitamin knowledge
            knowledge = self.load_multivitamin_knowledge()
            
            required_vitamin_fields = ['name', 'category', 'cognitive_benefits', 'target_conditions', 'dosage']
            
            for i, vitamin in enumerate(knowledge.get('multivitamins', [])):
                for field in required_vitamin_fields:
                    if field not in vitamin:
                        issues["errors"].append(f"Vitamin {i}: Missing required field '{field}'")
                    elif not vitamin[field]:
                        issues["warnings"].append(f"Vitamin {vitamin.get('name', i)}: Empty field '{field}'")
            
            # Validate cognitive mapping
            mapping = self.load_cognitive_mapping()
            
            required_domain_fields = ['description', 'recommended_vitamins']
            domains = mapping.get('cognitive_domains', {})
            
            for domain_name, domain_data in domains.items():
                for field in required_domain_fields:
                    if field not in domain_data:
                        issues["errors"].append(f"Domain {domain_name}: Missing required field '{field}'")
            
            # Cross-reference vitamins mentioned in mapping with knowledge base
            all_vitamin_names = [v['name'] for v in knowledge.get('multivitamins', [])]
            
            for domain_name, domain_data in domains.items():
                recommended = domain_data.get('recommended_vitamins', [])
                for rec in recommended:
                    vitamin_name = rec.get('name', '')
                    if vitamin_name not in all_vitamin_names:
                        issues["warnings"].append(f"Domain {domain_name}: References unknown vitamin '{vitamin_name}'")
            
            logger.info(f"Data validation complete: {len(issues['errors'])} errors, {len(issues['warnings'])} warnings")
            
        except Exception as e:
            issues["errors"].append(f"Validation failed: {str(e)}")
        
        return issues
    
    def get_data_statistics(self) -> Dict:
        """Get statistics about the loaded data."""
        try:
            knowledge = self.load_multivitamin_knowledge()
            mapping = self.load_cognitive_mapping()
            
            stats = {
                "vitamins": {
                    "total": len(knowledge.get('multivitamins', [])),
                    "categories": len(set(v['category'] for v in knowledge.get('multivitamins', []))),
                    "evidence_levels": {}
                },
                "combinations": len(knowledge.get('combinations', [])),
                "cognitive_domains": len(mapping.get('cognitive_domains', {})),
                "contraindications": {
                    "medications": len(mapping.get('contraindication_checks', {}).get('medication_interactions', {})),
                    "conditions": len(mapping.get('contraindication_checks', {}).get('health_conditions', {}))
                }
            }
            
            # Evidence level distribution
            for vitamin in knowledge.get('multivitamins', []):
                evidence = vitamin.get('evidence_level', 'Unknown')
                stats["vitamins"]["evidence_levels"][evidence] = stats["vitamins"]["evidence_levels"].get(evidence, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to generate statistics: {e}")
            return {}

def main():
    """Test data loader functionality."""
    loader = DataLoader()
    
    print("=== Data Validation ===")
    issues = loader.validate_data_integrity()
    
    if issues["errors"]:
        print("Errors found:")
        for error in issues["errors"]:
            print(f"  • {error}")
    
    if issues["warnings"]:
        print("⚠️ Warnings:")
        for warning in issues["warnings"]:
            print(f"  • {warning}")
    
    if not issues["errors"] and not issues["warnings"]:
        print("Data validation passed!")
    
    print("\n=== Data Statistics ===")
    stats = loader.get_data_statistics()
    
    print(f"Vitamins: {stats.get('vitamins', {}).get('total', 0)}")
    print(f"Categories: {stats.get('vitamins', {}).get('categories', 0)}")
    print(f"Combinations: {stats.get('combinations', 0)}")
    print(f"Cognitive Domains: {stats.get('cognitive_domains', 0)}")
    
    evidence_levels = stats.get('vitamins', {}).get('evidence_levels', {})
    if evidence_levels:
        print("Evidence Levels:")
        for level, count in evidence_levels.items():
            print(f"  • {level}: {count}")

if __name__ == "__main__":
    main()