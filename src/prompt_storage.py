"""
Prompt Storage System
====================

Manages persistent storage of custom prompts using JSON files.
This allows users to modify prompts through the settings page
and have those changes persist and be used by the extraction pipeline.
"""

import json
import os
import logging
from typing import Dict, Optional
from src.theodore_prompts import (
    get_field_extraction_prompt,
    get_page_selection_prompt,
    get_company_analysis_prompt
)

logger = logging.getLogger(__name__)

class PromptStorage:
    """Manages storage and retrieval of custom prompts"""
    
    def __init__(self, storage_dir: str = None):
        """Initialize prompt storage
        
        Args:
            storage_dir: Directory to store prompt files. Defaults to data/prompts/
        """
        if storage_dir is None:
            # Use data/prompts directory relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            storage_dir = os.path.join(project_root, 'data', 'prompts')
        
        self.storage_dir = storage_dir
        self.prompts_file = os.path.join(storage_dir, 'custom_prompts.json')
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing prompts or initialize with defaults
        self._load_prompts()
    
    def _load_prompts(self):
        """Load prompts from file or initialize with defaults"""
        if os.path.exists(self.prompts_file):
            try:
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    self.prompts = json.load(f)
                logger.info(f"Loaded custom prompts from {self.prompts_file}")
            except Exception as e:
                logger.error(f"Error loading prompts: {e}")
                self._initialize_defaults()
        else:
            self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialize with default prompts"""
        self.prompts = {
            'extraction': get_field_extraction_prompt(),
            'page_selection': get_page_selection_prompt(),
            'analysis': get_company_analysis_prompt()
        }
        self._save_prompts()
        logger.info("Initialized with default prompts")
    
    def _save_prompts(self):
        """Save prompts to file"""
        try:
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved prompts to {self.prompts_file}")
        except Exception as e:
            logger.error(f"Error saving prompts: {e}")
            raise
    
    def get_prompt(self, prompt_type: str) -> Optional[str]:
        """Get a prompt by type
        
        Args:
            prompt_type: Type of prompt ('extraction', 'page_selection', 'analysis')
            
        Returns:
            The prompt text or None if not found
        """
        return self.prompts.get(prompt_type)
    
    def save_prompt(self, prompt_type: str, prompt_content: str) -> bool:
        """Save a custom prompt
        
        Args:
            prompt_type: Type of prompt to save
            prompt_content: The prompt content
            
        Returns:
            True if saved successfully
        """
        try:
            self.prompts[prompt_type] = prompt_content
            self._save_prompts()
            return True
        except Exception as e:
            logger.error(f"Failed to save prompt: {e}")
            return False
    
    def reset_prompt(self, prompt_type: str) -> str:
        """Reset a prompt to its default
        
        Args:
            prompt_type: Type of prompt to reset
            
        Returns:
            The default prompt content
        """
        defaults = {
            'extraction': get_field_extraction_prompt(),
            'page_selection': get_page_selection_prompt(),
            'analysis': get_company_analysis_prompt()
        }
        
        if prompt_type in defaults:
            self.prompts[prompt_type] = defaults[prompt_type]
            self._save_prompts()
            return defaults[prompt_type]
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    def reset_all_prompts(self):
        """Reset all prompts to defaults"""
        self._initialize_defaults()
        logger.info("All prompts reset to defaults")
    
    def get_all_prompts(self) -> Dict[str, str]:
        """Get all prompts"""
        return self.prompts.copy()

# Global instance for easy access
_prompt_storage = None

def get_prompt_storage() -> PromptStorage:
    """Get the global prompt storage instance"""
    global _prompt_storage
    if _prompt_storage is None:
        _prompt_storage = PromptStorage()
    return _prompt_storage