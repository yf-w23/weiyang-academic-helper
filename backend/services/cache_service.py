"""OCR result cache service using MD5-based file system storage."""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class CacheService:
    """OCR result cache service.
    
    Uses file system storage with MD5 as filename.
    Maintains a manifest.json for metadata.
    """
    
    def __init__(self, cache_dir: str = "backend/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.cache_dir / "manifest.json"
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load manifest from disk."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"entries": {}, "version": "1.0"}
    
    def _save_manifest(self) -> None:
        """Save manifest to disk."""
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)
    
    def _compute_md5(self, file_path: str) -> str:
        """Compute file MD5 hash."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_cached_result(self, pdf_path: str) -> Optional[str]:
        """Get cached OCR result.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Cached markdown content or None if not cached
        """
        if not self.is_cached(pdf_path):
            return None
        
        md5 = self._compute_md5(pdf_path)
        cache_file = self.cache_dir / f"{md5}.md"
        
        try:
            return cache_file.read_text(encoding="utf-8")
        except IOError:
            return None
    
    def cache_result(self, pdf_path: str, transcript_md: str) -> str:
        """Cache OCR result.
        
        Args:
            pdf_path: Path to the PDF file
            transcript_md: Markdown content to cache
            
        Returns:
            Path to the cache file
        """
        md5 = self._compute_md5(pdf_path)
        cache_file = self.cache_dir / f"{md5}.md"
        
        # Write cache file
        cache_file.write_text(transcript_md, encoding="utf-8")
        
        # Update manifest
        self.manifest["entries"][md5] = {
            "pdf_path": str(pdf_path),
            "cache_file": str(cache_file),
            "cached_at": datetime.now().isoformat(),
            "size": len(transcript_md),
        }
        self._save_manifest()
        
        return str(cache_file)
    
    def is_cached(self, pdf_path: str) -> bool:
        """Check if file is cached.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            True if cached and valid, False otherwise
        """
        if not Path(pdf_path).exists():
            return False
        
        md5 = self._compute_md5(pdf_path)
        cache_file = self.cache_dir / f"{md5}.md"
        
        if not cache_file.exists():
            return False
        
        # Check manifest entry
        entry = self.manifest.get("entries", {}).get(md5)
        if not entry:
            return False
        
        return True
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        entries = self.manifest.get("entries", {})
        total_size = sum(
            entry.get("size", 0) 
            for entry in entries.values()
        )
        
        # Calculate cache files disk usage
        disk_usage = 0
        for cache_file in self.cache_dir.glob("*.md"):
            disk_usage += cache_file.stat().st_size
        
        return {
            "total_entries": len(entries),
            "total_cached_size": total_size,
            "disk_usage_bytes": disk_usage,
            "cache_dir": str(self.cache_dir),
            "manifest_version": self.manifest.get("version", "1.0"),
        }
    
    def invalidate_cache(self, pdf_path: str) -> bool:
        """Invalidate cache for a file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            True if cache was invalidated, False if not cached
        """
        md5 = self._compute_md5(pdf_path)
        cache_file = self.cache_dir / f"{md5}.md"
        
        removed = False
        if cache_file.exists():
            cache_file.unlink()
            removed = True
        
        if md5 in self.manifest.get("entries", {}):
            del self.manifest["entries"][md5]
            self._save_manifest()
            removed = True
        
        return removed
    
    def clear_all_cache(self) -> int:
        """Clear all cached results.
        
        Returns:
            Number of entries cleared
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.md"):
            cache_file.unlink()
            count += 1
        
        self.manifest["entries"] = {}
        self._save_manifest()
        
        return count


# Convenience functions
def get_cache_service(cache_dir: str = "backend/cache") -> CacheService:
    """Get or create cache service instance."""
    return CacheService(cache_dir)


def check_cache(pdf_path: str, cache_dir: str = "backend/cache") -> Optional[str]:
    """Check and return cached result if exists."""
    service = CacheService(cache_dir)
    return service.get_cached_result(pdf_path)


def save_to_cache(
    pdf_path: str, 
    transcript_md: str, 
    cache_dir: str = "backend/cache"
) -> str:
    """Save OCR result to cache."""
    service = CacheService(cache_dir)
    return service.cache_result(pdf_path, transcript_md)
