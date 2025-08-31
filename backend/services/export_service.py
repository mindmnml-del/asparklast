"""
Export Service for AISpark Studio
Handles exporting user prompts to various formats (JSON, CSV, TXT)
"""

import json
import csv
import io
from typing import List, Dict, Any
from datetime import datetime
from fastapi import HTTPException

from core.models import GeneratedPrompt


class ExportService:
    """Service for exporting user prompts in different formats"""
    
    @staticmethod
    def _prepare_prompt_data(prompts: List[GeneratedPrompt]) -> List[Dict[str, Any]]:
        """Prepare prompt data for export, including rich metadata."""
        export_data = []
        
        for prompt in prompts:
            raw_response = prompt.raw_response if prompt.raw_response else {}
            
            # Basic info
            prompt_data = {
                "prompt": raw_response.get("paragraphPrompt", "") or raw_response.get("paragraph_prompt", "") or raw_response.get("prompt", ""),
                "critic_suggestions": raw_response.get("critic_suggestions", "")
            }

            # Extract metadata if it exists
            metadata = raw_response.get("_metadata", {})
            if metadata:
                # Helios metadata
                helios_meta = metadata.get("helios")
                if helios_meta:
                    prompt_data["helios_personality"] = helios_meta.get("primary_personality")
                    prompt_data["helios_reasoning"] = helios_meta.get("selection_reasoning")

                # Character metadata
                character_meta = metadata.get("character")
                if character_meta:
                    prompt_data["character_name"] = character_meta.get("name")
            
            export_data.append(prompt_data)
        
        return export_data
    
    @staticmethod
    def export_to_json(prompts: List[GeneratedPrompt]) -> str:
        """Export prompts to JSON format with rich metadata."""
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
        """Export prompts to CSV format with rich metadata."""
        try:
            export_data = ExportService._prepare_prompt_data(prompts)
            
            if not export_data:
                return "No prompts to export"
            
            # Dynamically find all possible headers
            fieldnames = set()
            for item in export_data:
                fieldnames.update(item.keys())
            
            # Define a preferred order, with new fields at the end
            ordered_fieldnames = ['prompt', 'critic_suggestions', 'helios_personality', 'helios_reasoning', 'character_name']
            # Add any other discovered fields that weren't in the preferred list
            for field in sorted(list(fieldnames)):
                if field not in ordered_fieldnames:
                    ordered_fieldnames.append(field)

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=ordered_fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(export_data)
            
            return output.getvalue()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"CSV export failed: {str(e)}")
    
    @staticmethod
    def export_to_txt(prompts: List[GeneratedPrompt]) -> str:
        """Export prompts to human-readable TXT format with rich metadata."""
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
                    f"Prompt: {prompt.get('prompt', 'N/A')}",
                ])

                if prompt.get('critic_suggestions'):
                    output_lines.append(f"Critic Suggestions: {prompt['critic_suggestions']}")

                # Add Helios Info
                if prompt.get('helios_personality'):
                    output_lines.append(f"Helios Personality: {prompt.get('helios_personality')}")

                # Add Character Info
                if prompt.get('character_name'):
                    output_lines.append(f"Character Name: {prompt.get('character_name')}")

                output_lines.extend(["", "=" * 50, ""])
            
            return "\n".join(output_lines)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TXT export failed: {str(e)}")


export_service = ExportService()