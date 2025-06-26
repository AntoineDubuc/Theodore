"""
User Prompt Management Service
Handles CRUD operations for user-specific prompts in Pinecone
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.models import UserPrompt, UserPromptLibrary

logger = logging.getLogger(__name__)


class UserPromptService:
    """Service for managing user-specific prompts in Pinecone"""
    
    def __init__(self, pinecone_client=None):
        self.pinecone_client = pinecone_client
        self.prompt_namespace = "user_prompts"  # Separate namespace for user prompts
        
        # Default system prompts that users can customize
        self.default_prompts = {
            "analysis": {
                "name": "Company Analysis Prompt",
                "content": """Analyze this company's website content and extract comprehensive business intelligence.

Focus on extracting:
1. Company description and value proposition
2. Business model (B2B, B2C, marketplace, etc.)
3. Target market and industry
4. Key services and products offered
5. Competitive advantages
6. Technology stack and sophistication level
7. Company stage (startup, growth, mature)

Company: {company_name}
Website: {website}
Content: {content}

Provide detailed, factual analysis based on the available content."""
            },
            "page_selection": {
                "name": "Page Selection Prompt", 
                "content": """Analyze the following list of URLs from a company website and select the most valuable pages for extracting business intelligence.

Prioritize pages that likely contain:
- Company information (/about, /company, /team)
- Contact details (/contact, /locations)
- Products/services (/products, /services, /solutions)
- Leadership information (/team, /leadership, /management)
- Company news and updates (/news, /blog, /press)

URLs to analyze:
{urls}

Select up to 15 URLs that would provide the most comprehensive business intelligence. Return as a JSON list of selected URLs with brief reasoning for each."""
            },
            "extraction": {
                "name": "Enhanced Extraction Prompt",
                "content": """Extract specific business intelligence fields from this company's website content.

Target fields to extract:
- Founding year
- Headquarters location  
- Employee count or company size
- Leadership team (CEO, CTO, founders)
- Contact information
- Funding status
- Key partnerships
- Recent news or achievements

Company: {company_name}
Content: {content}

Extract only factual information that is explicitly stated in the content. If information is not available, respond with "Not found" for that field."""
            }
        }
    
    def get_user_prompt_library(self, user_id: str) -> UserPromptLibrary:
        """Get user's complete prompt library from Pinecone"""
        try:
            if not self.pinecone_client or not hasattr(self.pinecone_client, 'index'):
                logger.warning("Pinecone client not available")
                return self._create_default_library(user_id)
            
            # Query Pinecone for user's prompt library
            prompt_id = f"user_prompts_{user_id}"
            
            try:
                fetch_response = self.pinecone_client.index.fetch(ids=[prompt_id])
                
                if prompt_id in fetch_response.vectors:
                    # Parse library from metadata
                    metadata = fetch_response.vectors[prompt_id].metadata
                    library_data = json.loads(metadata.get('library_data', '{}'))
                    
                    # Convert back to UserPromptLibrary object
                    library = UserPromptLibrary(**library_data)
                    library.last_accessed = datetime.utcnow()
                    
                    return library
                else:
                    # Create new library for user
                    return self._create_default_library(user_id)
                    
            except Exception as e:
                logger.error(f"Error fetching user prompt library: {e}")
                return self._create_default_library(user_id)
                
        except Exception as e:
            logger.error(f"Error in get_user_prompt_library: {e}")
            return self._create_default_library(user_id)
    
    def save_user_prompt_library(self, library: UserPromptLibrary) -> bool:
        """Save user's complete prompt library to Pinecone"""
        try:
            if not self.pinecone_client or not hasattr(self.pinecone_client, 'index'):
                logger.warning("Pinecone client not available - cannot save prompts")
                return False
            
            prompt_id = f"user_prompts_{library.user_id}"
            
            # Update library metadata
            library.total_prompts = len(library.prompts)
            library.last_accessed = datetime.utcnow()
            
            # Calculate average success rate
            valid_prompts = [p for p in library.prompts if p.avg_success_rate is not None]
            if valid_prompts:
                library.avg_library_success_rate = sum(p.avg_success_rate for p in valid_prompts) / len(valid_prompts)
            
            # Prepare metadata for Pinecone
            metadata = {
                "user_id": library.user_id,
                "total_prompts": library.total_prompts,
                "total_usage": library.total_usage,
                "avg_library_success_rate": library.avg_library_success_rate,
                "last_accessed": library.last_accessed.isoformat(),
                "created_at": library.created_at.isoformat(),
                "library_data": json.dumps(library.dict())
            }
            
            # Create a dummy embedding (Pinecone requires embeddings)
            dummy_embedding = [0.0] * 1536  # Standard dimension
            
            # Upsert to Pinecone
            self.pinecone_client.index.upsert(
                vectors=[{
                    "id": prompt_id,
                    "values": dummy_embedding,
                    "metadata": metadata
                }]
            )
            
            logger.info(f"Saved prompt library for user {library.user_id} with {library.total_prompts} prompts")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user prompt library: {e}")
            return False
    
    def create_prompt(self, user_id: str, prompt_type: str, prompt_name: str, 
                     prompt_content: str, description: str = None, 
                     is_default: bool = False) -> Optional[UserPrompt]:
        """Create a new user prompt"""
        try:
            # Get user's library
            library = self.get_user_prompt_library(user_id)
            
            # Create new prompt
            new_prompt = UserPrompt(
                user_id=user_id,
                prompt_type=prompt_type,
                prompt_name=prompt_name,
                prompt_content=prompt_content,
                description=description,
                is_default=is_default
            )
            
            # If this is set as default, unset other defaults for this type
            if is_default:
                for prompt in library.prompts:
                    if prompt.prompt_type == prompt_type:
                        prompt.is_default = False
            
            # Add to library
            library.add_prompt(new_prompt)
            
            # Save library
            if self.save_user_prompt_library(library):
                logger.info(f"Created new prompt '{prompt_name}' for user {user_id}")
                return new_prompt
            else:
                logger.error("Failed to save prompt library after creating new prompt")
                return None
                
        except Exception as e:
            logger.error(f"Error creating prompt: {e}")
            return None
    
    def update_prompt(self, user_id: str, prompt_id: str, **updates) -> Optional[UserPrompt]:
        """Update an existing user prompt"""
        try:
            # Get user's library
            library = self.get_user_prompt_library(user_id)
            
            # Find the prompt
            prompt = library.get_prompt_by_id(prompt_id)
            if not prompt:
                logger.warning(f"Prompt {prompt_id} not found for user {user_id}")
                return None
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(prompt, field):
                    setattr(prompt, field, value)
            
            prompt.updated_at = datetime.utcnow()
            
            # Handle default setting
            if updates.get('is_default'):
                library.set_default_prompt(prompt_id)
            
            # Save library
            if self.save_user_prompt_library(library):
                logger.info(f"Updated prompt {prompt_id} for user {user_id}")
                return prompt
            else:
                logger.error("Failed to save prompt library after update")
                return None
                
        except Exception as e:
            logger.error(f"Error updating prompt: {e}")
            return None
    
    def delete_prompt(self, user_id: str, prompt_id: str) -> bool:
        """Delete a user prompt"""
        try:
            # Get user's library
            library = self.get_user_prompt_library(user_id)
            
            # Find and remove the prompt
            prompt = library.get_prompt_by_id(prompt_id)
            if not prompt:
                logger.warning(f"Prompt {prompt_id} not found for user {user_id}")
                return False
            
            # Remove from library
            library.prompts = [p for p in library.prompts if p.id != prompt_id]
            library.total_prompts = len(library.prompts)
            
            # Save library
            if self.save_user_prompt_library(library):
                logger.info(f"Deleted prompt {prompt_id} for user {user_id}")
                return True
            else:
                logger.error("Failed to save prompt library after deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting prompt: {e}")
            return False
    
    def get_prompt(self, user_id: str, prompt_id: str) -> Optional[UserPrompt]:
        """Get a specific user prompt"""
        try:
            library = self.get_user_prompt_library(user_id)
            return library.get_prompt_by_id(prompt_id)
        except Exception as e:
            logger.error(f"Error getting prompt: {e}")
            return None
    
    def get_prompts_by_type(self, user_id: str, prompt_type: str) -> List[UserPrompt]:
        """Get all user prompts of a specific type"""
        try:
            library = self.get_user_prompt_library(user_id)
            return library.get_prompts_by_type(prompt_type)
        except Exception as e:
            logger.error(f"Error getting prompts by type: {e}")
            return []
    
    def get_default_prompt(self, user_id: str, prompt_type: str) -> Optional[UserPrompt]:
        """Get user's default prompt for a specific type"""
        try:
            library = self.get_user_prompt_library(user_id)
            default_prompt = library.get_default_prompt(prompt_type)
            
            # If no user default, return system default
            if not default_prompt and prompt_type in self.default_prompts:
                return UserPrompt(
                    user_id="system",
                    prompt_type=prompt_type,
                    prompt_name=self.default_prompts[prompt_type]["name"],
                    prompt_content=self.default_prompts[prompt_type]["content"],
                    is_default=True
                )
            
            return default_prompt
        except Exception as e:
            logger.error(f"Error getting default prompt: {e}")
            return None
    
    def set_default_prompt(self, user_id: str, prompt_id: str) -> bool:
        """Set a prompt as default for its type"""
        try:
            library = self.get_user_prompt_library(user_id)
            library.set_default_prompt(prompt_id)
            
            return self.save_user_prompt_library(library)
        except Exception as e:
            logger.error(f"Error setting default prompt: {e}")
            return False
    
    def update_prompt_usage_stats(self, user_id: str, prompt_id: str, 
                                 success_rate: float, processing_time: float, cost: float) -> bool:
        """Update prompt usage statistics"""
        try:
            library = self.get_user_prompt_library(user_id)
            prompt = library.get_prompt_by_id(prompt_id)
            
            if prompt:
                prompt.update_usage_stats(success_rate, processing_time, cost)
                library.total_usage += 1
                
                return self.save_user_prompt_library(library)
            
            return False
        except Exception as e:
            logger.error(f"Error updating prompt usage stats: {e}")
            return False
    
    def _create_default_library(self, user_id: str) -> UserPromptLibrary:
        """Create a new library with default prompts for a user"""
        library = UserPromptLibrary(user_id=user_id)
        
        # Add default prompts as user prompts
        for prompt_type, default_data in self.default_prompts.items():
            default_prompt = UserPrompt(
                user_id=user_id,
                prompt_type=prompt_type,
                prompt_name=default_data["name"],
                prompt_content=default_data["content"],
                description=f"Default {prompt_type} prompt",
                is_default=True
            )
            library.add_prompt(default_prompt)
        
        return library
    
    def export_user_prompts(self, user_id: str) -> Dict[str, Any]:
        """Export all user prompts for backup/sharing"""
        try:
            library = self.get_user_prompt_library(user_id)
            
            export_data = {
                "user_id": user_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "total_prompts": library.total_prompts,
                "prompts": []
            }
            
            for prompt in library.prompts:
                export_data["prompts"].append({
                    "id": prompt.id,
                    "prompt_type": prompt.prompt_type,
                    "prompt_name": prompt.prompt_name,
                    "prompt_content": prompt.prompt_content,
                    "description": prompt.description,
                    "is_default": prompt.is_default,
                    "usage_count": prompt.usage_count,
                    "avg_success_rate": prompt.avg_success_rate,
                    "created_at": prompt.created_at.isoformat(),
                    "updated_at": prompt.updated_at.isoformat()
                })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting user prompts: {e}")
            return {"error": str(e)}
    
    def import_user_prompts(self, user_id: str, import_data: Dict[str, Any]) -> bool:
        """Import prompts from export data"""
        try:
            library = self.get_user_prompt_library(user_id)
            
            imported_count = 0
            for prompt_data in import_data.get("prompts", []):
                # Create new prompt with imported data
                imported_prompt = UserPrompt(
                    user_id=user_id,  # Override with current user
                    prompt_type=prompt_data["prompt_type"],
                    prompt_name=f"Imported: {prompt_data['prompt_name']}",
                    prompt_content=prompt_data["prompt_content"],
                    description=prompt_data.get("description"),
                    is_default=False  # Don't import as default
                )
                
                library.add_prompt(imported_prompt)
                imported_count += 1
            
            if self.save_user_prompt_library(library):
                logger.info(f"Imported {imported_count} prompts for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error importing user prompts: {e}")
            return False