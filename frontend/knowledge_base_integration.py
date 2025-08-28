"""
Knowledge Base Integration for AISpark Studio
Integrates Helios master prompt and other knowledge base resources
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

class KnowledgeBaseIntegration:
    """Integrates various knowledge base resources for AISpark"""
    
    def __init__(self, knowledge_base_path: str = None):
        self.kb_path = knowledge_base_path or os.path.join(os.path.dirname(__file__), '..', 'knowledge_base')
        self.helios_prompt = self.load_helios_prompt()
        self.available_resources = self.scan_resources()
    
    def load_helios_prompt(self) -> Optional[str]:
        """Load Helios master prompt"""
        try:
            helios_path = os.path.join(self.kb_path, 'helios_master_prompt.txt')
            if os.path.exists(helios_path):
                with open(helios_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Warning: Could not load Helios prompt: {e}")
        return None
    
    def scan_resources(self) -> List[Dict[str, str]]:
        """Scan available knowledge base resources"""
        resources = []
        
        if not os.path.exists(self.kb_path):
            return resources
        
        resource_types = {
            '.txt': 'text',
            '.docx': 'document',
            '.gdoc': 'google_doc',
            '.py': 'script'
        }
        
        for file_path in Path(self.kb_path).rglob('*'):
            if file_path.is_file():
                ext = ''.join(file_path.suffixes[-2:]) if len(file_path.suffixes) > 1 else file_path.suffix
                
                resource_type = resource_types.get(ext, 'unknown')
                
                resources.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'type': resource_type,
                    'category': self.categorize_resource(file_path.name)
                })
        
        return resources
    
    def categorize_resource(self, filename: str) -> str:
        """Categorize knowledge base resources"""
        filename_lower = filename.lower()
        
        categories = {
            'character': ['character', 'class', 'race'],
            'vehicle': ['vehicle', 'aerial', 'marine', 'land'],
            'weapon': ['armory', 'weapon'],
            'creature': ['creature', 'animal', 'mythology'],
            'style': ['visual_style', 'aesthetic', 'cinematography'],
            'prompt': ['prompt', 'template', 'format'],
            'guide': ['guide', 'manual', 'technique']
        }
        
        for category, keywords in categories.items():
            if any(keyword in filename_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def get_resources_by_category(self, category: str) -> List[Dict[str, str]]:
        """Get resources by category"""
        return [r for r in self.available_resources if r['category'] == category]
    
    def get_gemini_optimized_prompt(self, user_request: str) -> str:
        """Create Gemini 2.5 Flash optimized prompt using Helios guidelines"""
        
        base_prompt = f"""
{self.helios_prompt}

GEMINI 2.5 FLASH OPTIMIZATION:
- Use clear, specific language
- Include technical photography terms
- Optimize for high-quality visual generation
- Structure for JSON response format
- Include Gemini-specific quality markers

USER REQUEST: {user_request}

Generate an optimized prompt following the Helios guidelines above, specifically tailored for Gemini 2.5 Flash model.
"""
        return base_prompt
    
    def get_available_categories(self) -> List[str]:
        """Get list of available resource categories"""
        categories = set(r['category'] for r in self.available_resources)
        return sorted(list(categories))
    
    def get_resource_content(self, resource_name: str) -> Optional[str]:
        """Get content of a specific resource"""
        try:
            resource = next((r for r in self.available_resources if r['name'] == resource_name), None)
            if resource and resource['type'] == 'text':
                with open(resource['path'], 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Error reading resource {resource_name}: {e}")
        return None

# Global instance
kb_integration = KnowledgeBaseIntegration()
