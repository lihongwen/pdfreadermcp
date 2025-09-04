"""
Caching system for PDF processing results.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    data: Any
    created_at: float
    file_mtime: float
    file_size: int
    cache_key: str
    
    def is_valid(self, file_path: Union[str, Path]) -> bool:
        """Check if cache entry is still valid."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            stat = path.stat()
            return (
                self.file_mtime == stat.st_mtime and
                self.file_size == stat.st_size
            )
        except (OSError, AttributeError):
            return False


class PDFCache:
    """
    In-memory cache for PDF processing results with file modification tracking.
    """
    
    def __init__(self, max_entries: int = 100, max_age_seconds: int = 3600):
        """
        Initialize the PDF cache.
        
        Args:
            max_entries: Maximum number of entries to keep in memory
            max_age_seconds: Maximum age of cache entries in seconds
        """
        self.max_entries = max_entries
        self.max_age_seconds = max_age_seconds
        self._cache: Dict[str, CacheEntry] = {}
    
    def _generate_cache_key(self, file_path: Union[str, Path], operation: str, **kwargs) -> str:
        """
        Generate a unique cache key for the operation.
        
        Args:
            file_path: Path to the file
            operation: Type of operation (e.g., 'extract_text', 'ocr')
            **kwargs: Additional parameters that affect the result
            
        Returns:
            Unique cache key
        """
        # Create a string representation of all parameters
        params = {
            'file_path': str(file_path),
            'operation': operation,
            **kwargs
        }
        
        # Sort keys for consistent hashing
        params_str = json.dumps(params, sort_keys=True)
        
        # Generate hash
        return hashlib.md5(params_str.encode()).hexdigest()
    
    def get(self, file_path: Union[str, Path], operation: str, **kwargs) -> Optional[Any]:
        """
        Get cached result if available and valid.
        
        Args:
            file_path: Path to the file
            operation: Type of operation
            **kwargs: Additional parameters
            
        Returns:
            Cached result or None if not found/invalid
        """
        cache_key = self._generate_cache_key(file_path, operation, **kwargs)
        
        if cache_key not in self._cache:
            return None
        
        entry = self._cache[cache_key]
        
        # Check if entry is still valid
        if not entry.is_valid(file_path):
            self._remove_entry(cache_key)
            return None
        
        # Check if entry has expired
        if time.time() - entry.created_at > self.max_age_seconds:
            self._remove_entry(cache_key)
            return None
        
        return entry.data
    
    def set(self, file_path: Union[str, Path], operation: str, data: Any, **kwargs) -> None:
        """
        Store result in cache.
        
        Args:
            file_path: Path to the file
            operation: Type of operation
            data: Data to cache
            **kwargs: Additional parameters
        """
        cache_key = self._generate_cache_key(file_path, operation, **kwargs)
        
        try:
            path = Path(file_path)
            stat = path.stat()
            
            entry = CacheEntry(
                data=data,
                created_at=time.time(),
                file_mtime=stat.st_mtime,
                file_size=stat.st_size,
                cache_key=cache_key
            )
            
            self._cache[cache_key] = entry
            
            # Clean up old entries if needed
            self._cleanup_if_needed()
            
        except (OSError, AttributeError):
            # If we can't get file stats, don't cache
            pass
    
    def _remove_entry(self, cache_key: str) -> None:
        """Remove a cache entry."""
        if cache_key in self._cache:
            del self._cache[cache_key]
    
    def _cleanup_if_needed(self) -> None:
        """Clean up old or excess cache entries."""
        current_time = time.time()
        
        # Remove expired entries
        expired_keys = []
        for key, entry in self._cache.items():
            if current_time - entry.created_at > self.max_age_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
        
        # Remove excess entries (LRU-style, remove oldest)
        if len(self._cache) > self.max_entries:
            # Sort by creation time and remove oldest
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].created_at
            )
            
            entries_to_remove = len(self._cache) - self.max_entries
            for i in range(entries_to_remove):
                key, _ = sorted_entries[i]
                self._remove_entry(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        current_time = time.time()
        
        valid_entries = 0
        expired_entries = 0
        total_size = 0
        
        for entry in self._cache.values():
            if current_time - entry.created_at > self.max_age_seconds:
                expired_entries += 1
            else:
                valid_entries += 1
            
            # Rough estimate of memory usage
            try:
                total_size += len(str(entry.data))
            except:
                pass
        
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "max_entries": self.max_entries,
            "max_age_seconds": self.max_age_seconds,
            "estimated_size_bytes": total_size
        }