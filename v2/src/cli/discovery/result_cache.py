"""
Discovery Result Cache for Theodore CLI.

Provides intelligent caching for discovery results with query fingerprinting.
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any
from pathlib import Path

from src.core.use_cases.discover_similar_companies import DiscoveryFilters, DiscoverySource, DiscoveryResult


class DiscoveryResultCache:
    """Intelligent caching system for discovery results."""
    
    def __init__(self, cache_dir: Optional[str] = None, ttl_seconds: int = 3600):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".theodore" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
    
    async def get_cached_result(
        self,
        company_name: str,
        filters: DiscoveryFilters,
        limit: int,
        source: DiscoverySource
    ) -> Optional[DiscoveryResult]:
        """Get cached discovery result if available and valid."""
        
        cache_key = self._generate_cache_key(company_name, filters, limit, source)
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            cached_data = self._memory_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.ttl_seconds:
                return self._deserialize_result(cached_data['result'])
            else:
                del self._memory_cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                if time.time() - cached_data['timestamp'] < self.ttl_seconds:
                    result = self._deserialize_result(cached_data['result'])
                    # Store in memory cache for faster access
                    self._memory_cache[cache_key] = cached_data
                    return result
                else:
                    cache_file.unlink()  # Remove expired cache
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                pass
        
        return None
    
    async def cache_result(
        self,
        company_name: str,
        filters: DiscoveryFilters,
        limit: int,
        source: DiscoverySource,
        result: DiscoveryResult
    ) -> None:
        """Cache discovery result."""
        
        cache_key = self._generate_cache_key(company_name, filters, limit, source)
        
        cached_data = {
            'timestamp': time.time(),
            'result': self._serialize_result(result),
            'company_name': company_name,
            'limit': limit,
            'source': source.value
        }
        
        # Store in memory cache
        self._memory_cache[cache_key] = cached_data
        
        # Store in disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(cached_data, f, default=str)
        except Exception:
            pass  # Gracefully handle cache write failures
    
    def _generate_cache_key(
        self,
        company_name: str,
        filters: DiscoveryFilters,
        limit: int,
        source: DiscoverySource
    ) -> str:
        """Generate cache key for the given parameters."""
        
        # Create a string representation of all parameters
        key_data = {
            'company_name': company_name.lower().strip(),
            'limit': limit,
            'source': source.value,
            'filters': {
                'business_model': filters.business_model.value if filters.business_model else None,
                'company_size': filters.company_size.value if filters.company_size else None,
                'industry': filters.industry,
                'growth_stage': filters.growth_stage.value if filters.growth_stage else None,
                'location': filters.location,
                'similarity_threshold': filters.similarity_threshold,
                'founded_after': filters.founded_after,
                'founded_before': filters.founded_before,
                'exclude_competitors': filters.exclude_competitors,
                'include_subsidiaries': filters.include_subsidiaries
            }
        }
        
        # Create hash of the key data
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _serialize_result(self, result: DiscoveryResult) -> Dict[str, Any]:
        """Serialize discovery result for caching."""
        return {
            'companies': [
                {
                    'name': company.name,
                    'website': company.website,
                    'description': company.description
                }
                for company in result.companies
            ],
            'target_company': result.target_company,
            'similarity_scores': result.similarity_scores,
            'source': result.source.value,
            'search_time_ms': result.search_time_ms
        }
    
    def _deserialize_result(self, data: Dict[str, Any]) -> DiscoveryResult:
        """Deserialize cached result data."""
        from src.core.domain.entities.company import Company
        
        companies = [
            Company(
                name=company_data['name'],
                website=company_data['website'],
                description=company_data['description']
            )
            for company_data in data['companies']
        ]
        
        return DiscoveryResult(
            companies=companies,
            target_company=data['target_company'],
            similarity_scores=data['similarity_scores'],
            source=DiscoverySource(data['source']),
            search_time_ms=data['search_time_ms']
        )