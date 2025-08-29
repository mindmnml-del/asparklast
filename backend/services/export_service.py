"""
Export Service for AISpark Studio
Handles exporting user prompts to various formats (JSON, CSV, TXT)
"""

import json
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException

from core.models import GeneratedPrompt


class ExportService:
    """Service for exporting user prompts in different formats"""
    
    @staticmethod
    def _prepare_prompt_data(prompts: List[GeneratedPrompt]) -> List[Dict[str, Any]]:
        """Prepare prompt data for export - only prompt and critic suggestions"""
        export_data = []
        
        for prompt in prompts:
            raw_response = prompt.raw_response if prompt.raw_response else {}
            
            # Get the main prompt text
            main_prompt = (
                raw_response.get("paragraphPrompt", "") or 
                raw_response.get("paragraph_prompt", "") or 
                raw_response.get("prompt", "")
            )
            
            # Get critic suggestions if any
            critic_suggestions = raw_response.get("critic_suggestions", "")
            
            prompt_data = {
                "prompt": main_prompt,
                "critic_suggestions": critic_suggestions
            }
            
            export_data.append(prompt_data)
        
        return export_data
    
    @staticmethod
    def export_to_json(prompts: List[GeneratedPrompt]) -> str:
        """Export prompts to JSON format"""
        try:
            export_data = ExportService._prepare_prompt_data(prompts)
            
            export_structure = {
                "export_info": {
                    "format": "json",
                    "exported_at": datetime.utcnow().isoformat(),
                    "total_prompts": len(export_data),
                    "exported_by": "AISpark Studio"
                },
                "prompts": export_data
            }
            
            return json.dumps(export_structure, indent=2, ensure_ascii=False)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"JSON export failed: {str(e)}")
    
    @staticmethod
    def export_to_csv(prompts: List[GeneratedPrompt]) -> str:
        """Export prompts to CSV format"""
        try:
            export_data = ExportService._prepare_prompt_data(prompts)
            
            if not export_data:
                return "No prompts to export"
            
            output = io.StringIO()
            fieldnames = export_data[0].keys()
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(export_data)
            
            return output.getvalue()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"CSV export failed: {str(e)}")
    
    @staticmethod
    def export_to_txt(prompts: List[GeneratedPrompt]) -> str:
        """Export prompts to human-readable TXT format"""
        try:
            export_data = ExportService._prepare_prompt_data(prompts)
            
            output_lines = [
                "=== AISpark Studio - Prompt Export ===",
                f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
                f"Total Prompts: {len(export_data)}",
                "=" * 50,
                ""
            ]
            
            for i, prompt in enumerate(export_data, 1):
                output_lines.extend([
                    f"PROMPT #{i}",
                    "-" * 20,
                    f"Prompt: {prompt['prompt']}",
                    "",
                    f"Critic Suggestions: {prompt['critic_suggestions'] or 'None'}",
                    "",
                    "=" * 50,
                    ""
                ])
            
            return "\n".join(output_lines)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TXT export failed: {str(e)}")


export_service = ExportService()