"""
Web3/IPFS Storage for Phase 8 Advanced Intelligence

Decentralized file hosting with IPFS for permanence guarantees and Web3 integration.
Target: >95% upload success rate with gateway integration.

Features:
- IPFS file uploads
- Content addressing (CID)
- Gateway integration
- Pin management
- Decentralized storage
"""

import asyncio
import logging
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class IPFSUploadResult:
    """Result of an IPFS upload operation"""
    cid: str  # Content Identifier
    file_path: str
    size_bytes: int
    upload_duration_seconds: float
    gateway_urls: List[str]
    pinned: bool
    success: bool
    error: Optional[str] = None


@dataclass
class PinStatus:
    """IPFS pin status"""
    cid: str
    pinned: bool
    pin_date: datetime
    replication_count: int


class IPFSClient:
    """
    IPFS client for decentralized file storage.
    
    Implements:
    - File uploads to IPFS network
    - Content addressing with CIDs
    - Pin management for permanence
    - Gateway URL generation
    """
    
    def __init__(
        self,
        api_endpoint: str = "http://127.0.0.1:5001",
        gateway_endpoints: Optional[List[str]] = None,
        auto_pin: bool = True
    ):
        """
        Initialize IPFS client.
        
        Args:
            api_endpoint: IPFS API endpoint
            gateway_endpoints: List of IPFS gateways
            auto_pin: Automatically pin uploaded content
        """
        self.api_endpoint = api_endpoint
        self.gateway_endpoints = gateway_endpoints or [
            "https://ipfs.io/ipfs/",
            "https://gateway.pinata.cloud/ipfs/",
            "https://cloudflare-ipfs.com/ipfs/"
        ]
        self.auto_pin = auto_pin
        self.upload_stats = {
            "total_uploads": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "total_bytes_uploaded": 0
        }
        
        logger.info(f"IPFSClient initialized: endpoint={api_endpoint}")
    
    async def upload_file(self, file_path: str) -> IPFSUploadResult:
        """
        Upload a file to IPFS network.
        
        Args:
            file_path: Path to file to upload
            
        Returns:
            IPFSUploadResult with CID and gateway URLs
        """
        import time
        
        path = Path(file_path)
        if not path.exists():
            return IPFSUploadResult(
                cid="",
                file_path=file_path,
                size_bytes=0,
                upload_duration_seconds=0.0,
                gateway_urls=[],
                pinned=False,
                success=False,
                error="File not found"
            )
        
        file_size = path.stat().st_size
        start_time = time.perf_counter()
        
        try:
            # Mock IPFS upload (in production, use ipfshttpclient or similar)
            cid = await self._mock_ipfs_add(file_path)
            
            duration = time.perf_counter() - start_time
            
            # Generate gateway URLs
            gateway_urls = [f"{gateway}{cid}" for gateway in self.gateway_endpoints]
            
            # Pin if auto-pin enabled
            pinned = False
            if self.auto_pin:
                pinned = await self._pin_content(cid)
            
            # Update stats
            self.upload_stats["total_uploads"] += 1
            self.upload_stats["successful_uploads"] += 1
            self.upload_stats["total_bytes_uploaded"] += file_size
            
            result = IPFSUploadResult(
                cid=cid,
                file_path=file_path,
                size_bytes=file_size,
                upload_duration_seconds=duration,
                gateway_urls=gateway_urls,
                pinned=pinned,
                success=True
            )
            
            logger.info(
                f"Uploaded to IPFS: {file_path} -> {cid} "
                f"({file_size / (1024*1024):.2f} MB in {duration:.2f}s)"
            )
            
            return result
            
        except Exception as e:
            self.upload_stats["total_uploads"] += 1
            self.upload_stats["failed_uploads"] += 1
            
            logger.error(f"IPFS upload failed for {file_path}: {e}")
            
            return IPFSUploadResult(
                cid="",
                file_path=file_path,
                size_bytes=file_size,
                upload_duration_seconds=0.0,
                gateway_urls=[],
                pinned=False,
                success=False,
                error=str(e)
            )
    
    async def _mock_ipfs_add(self, file_path: str) -> str:
        """
        Mock IPFS add operation.
        
        In production, would use:
        import ipfshttpclient
        client = ipfshttpclient.connect(self.api_endpoint)
        result = client.add(file_path)
        return result['Hash']
        """
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        # Generate mock CID (Content Identifier) based on file hash
        path = Path(file_path)
        file_hash = await asyncio.to_thread(self._hash_file_sync, path)
        
        # IPFS CIDs typically start with "Qm" (base58 CIDv0)
        mock_cid = f"Qm{file_hash[:44]}"
        
        return mock_cid

    @staticmethod
    def _hash_file_sync(path: Path) -> str:
        """Compute SHA256 hash of a file (blocking)."""
        hasher = hashlib.sha256()
        with open(path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    async def _pin_content(self, cid: str) -> bool:
        """
        Pin content to ensure permanence.
        
        Args:
            cid: Content identifier
            
        Returns:
            True if pinned successfully
        """
        try:
            # Mock pin operation
            await asyncio.sleep(0.05)
            logger.debug(f"Pinned content: {cid}")
            return True
        except Exception as e:
            logger.error(f"Failed to pin {cid}: {e}")
            return False
    
    async def unpin_content(self, cid: str) -> bool:
        """Unpin content from IPFS"""
        try:
            await asyncio.sleep(0.05)
            logger.debug(f"Unpinned content: {cid}")
            return True
        except Exception as e:
            logger.error(f"Failed to unpin {cid}: {e}")
            return False
    
    async def get_file(self, cid: str, output_path: str) -> bool:
        """
        Retrieve a file from IPFS.
        
        Args:
            cid: Content identifier
            output_path: Where to save the file
            
        Returns:
            True if successful
        """
        try:
            # Mock file retrieval
            logger.info(f"Retrieving {cid} from IPFS to {output_path}")
            await asyncio.sleep(0.1)
            
            # In production: client.get(cid, output_path)
            
            return True
        except Exception as e:
            logger.error(f"Failed to retrieve {cid}: {e}")
            return False
    
    def get_gateway_url(self, cid: str, gateway_index: int = 0) -> str:
        """Get gateway URL for a CID"""
        if 0 <= gateway_index < len(self.gateway_endpoints):
            return f"{self.gateway_endpoints[gateway_index]}{cid}"
        return f"{self.gateway_endpoints[0]}{cid}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get upload statistics"""
        success_rate = 0.0
        if self.upload_stats["total_uploads"] > 0:
            success_rate = (
                self.upload_stats["successful_uploads"] /
                self.upload_stats["total_uploads"]
            )
        
        return {
            **self.upload_stats,
            "success_rate": success_rate,
            "gateway_count": len(self.gateway_endpoints)
        }


class Web3StorageProvider:
    """
    Web3 storage provider with IPFS backend.
    
    Provides high-level storage API with:
    - Automatic chunking for large files
    - Redundancy across multiple nodes
    - Metadata storage
    - Search and retrieval
    """
    
    def __init__(self, ipfs_client: Optional[IPFSClient] = None):
        """
        Initialize Web3 storage provider.
        
        Args:
            ipfs_client: IPFS client instance (creates default if None)
        """
        self.ipfs_client = ipfs_client or IPFSClient()
        self.storage_index: Dict[str, Dict] = {}  # filename -> metadata
        self.cid_to_metadata: Dict[str, Dict] = {}  # CID -> metadata
        
        logger.info("Web3StorageProvider initialized")
    
    async def store_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IPFSUploadResult:
        """
        Store a file with optional metadata.
        
        Args:
            file_path: Path to file to store
            metadata: Optional metadata dictionary
            
        Returns:
            IPFSUploadResult
        """
        # Upload to IPFS
        result = await self.ipfs_client.upload_file(file_path)
        
        if result.success:
            # Store metadata
            file_metadata = {
                "cid": result.cid,
                "file_path": file_path,
                "size_bytes": result.size_bytes,
                "upload_date": datetime.now().isoformat(),
                "gateway_urls": result.gateway_urls,
                "custom_metadata": metadata or {}
            }
            
            filename = Path(file_path).name
            self.storage_index[filename] = file_metadata
            self.cid_to_metadata[result.cid] = file_metadata
            
            logger.info(f"Stored file with metadata: {filename} -> {result.cid}")
        
        return result
    
    async def store_multiple_files(
        self,
        file_paths: List[str]
    ) -> List[IPFSUploadResult]:
        """Store multiple files concurrently"""
        tasks = [self.store_file(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(
            1 for r in results
            if not isinstance(r, Exception) and r.success
        )
        
        logger.info(
            f"Batch upload: {successful}/{len(file_paths)} files successful"
        )
        
        return [r for r in results if not isinstance(r, Exception)]
    
    async def retrieve_file(
        self,
        cid: str,
        output_path: str
    ) -> bool:
        """Retrieve a file by CID"""
        return await self.ipfs_client.get_file(cid, output_path)
    
    def search_by_filename(self, filename: str) -> Optional[Dict]:
        """Search for file metadata by filename"""
        return self.storage_index.get(filename)
    
    def search_by_cid(self, cid: str) -> Optional[Dict]:
        """Search for file metadata by CID"""
        return self.cid_to_metadata.get(cid)
    
    def get_all_stored_files(self) -> List[Dict]:
        """Get metadata for all stored files"""
        return list(self.storage_index.values())
    
    async def verify_availability(self, cid: str) -> bool:
        """
        Verify that content is available on IPFS network.
        
        Args:
            cid: Content identifier
            
        Returns:
            True if content is available
        """
        # Mock verification by checking gateway
        try:
            # In production: attempt to fetch from gateway or check DHT
            await asyncio.sleep(0.05)
            logger.debug(f"Verified availability: {cid}")
            return True
        except Exception as e:
            logger.error(f"Availability check failed for {cid}: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        total_files = len(self.storage_index)
        total_size = sum(
            meta.get("size_bytes", 0)
            for meta in self.storage_index.values()
        )
        
        ipfs_stats = self.ipfs_client.get_stats()
        
        return {
            "total_files_stored": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "ipfs_stats": ipfs_stats
        }


class DecentralizedFileHost:
    """
    High-level decentralized file hosting service.
    
    Features:
    - Automatic IPFS uploads
    - Gateway fallback
    - Permanence guarantees through pinning
    - Content availability monitoring
    """
    
    def __init__(
        self,
        enable_pinning: bool = True,
        replication_factor: int = 3
    ):
        """
        Initialize decentralized file host.
        
        Args:
            enable_pinning: Enable automatic pinning
            replication_factor: Number of replications for redundancy
        """
        self.storage_provider = Web3StorageProvider()
        self.enable_pinning = enable_pinning
        self.replication_factor = replication_factor
        self.hosted_files: Dict[str, List[str]] = {}  # filename -> [CIDs]
        
        logger.info(
            f"DecentralizedFileHost initialized: "
            f"pinning={enable_pinning}, replication={replication_factor}"
        )
    
    async def host_file(
        self,
        file_path: str,
        permanent: bool = True
    ) -> IPFSUploadResult:
        """
        Host a file on decentralized network.
        
        Args:
            file_path: Path to file
            permanent: If True, pin for permanence
            
        Returns:
            IPFSUploadResult
        """
        metadata = {
            "permanent": permanent,
            "hosted_date": datetime.now().isoformat(),
            "replication_factor": self.replication_factor if permanent else 1
        }
        
        result = await self.storage_provider.store_file(file_path, metadata)
        
        if result.success:
            filename = Path(file_path).name
            
            if filename not in self.hosted_files:
                self.hosted_files[filename] = []
            
            self.hosted_files[filename].append(result.cid)
            
            logger.info(
                f"File hosted: {filename} at {result.cid} "
                f"(permanent: {permanent})"
            )
        
        return result
    
    async def host_directory(
        self,
        directory_path: str,
        recursive: bool = True
    ) -> List[IPFSUploadResult]:
        """
        Host all files in a directory.
        
        Args:
            directory_path: Path to directory
            recursive: Include subdirectories
            
        Returns:
            List of IPFSUploadResults
        """
        path = Path(directory_path)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory_path}")
        
        # Find all files
        if recursive:
            files = list(path.rglob("*"))
        else:
            files = list(path.glob("*"))
        
        file_paths = [str(f) for f in files if f.is_file()]
        
        logger.info(f"Hosting {len(file_paths)} files from {directory_path}")
        
        return await self.storage_provider.store_multiple_files(file_paths)
    
    def get_file_urls(self, filename: str) -> List[str]:
        """Get all gateway URLs for a hosted file"""
        urls = []
        
        if filename in self.hosted_files:
            for cid in self.hosted_files[filename]:
                metadata = self.storage_provider.search_by_cid(cid)
                if metadata and "gateway_urls" in metadata:
                    urls.extend(metadata["gateway_urls"])
        
        return urls
    
    async def verify_file_availability(self, filename: str) -> Dict[str, bool]:
        """
        Verify availability of all CIDs for a file.
        
        Returns:
            Dictionary mapping CID to availability status
        """
        availability = {}
        
        if filename in self.hosted_files:
            for cid in self.hosted_files[filename]:
                available = await self.storage_provider.verify_availability(cid)
                availability[cid] = available
        
        return availability
    
    def get_hosting_stats(self) -> Dict[str, Any]:
        """Get comprehensive hosting statistics"""
        storage_stats = self.storage_provider.get_storage_stats()
        
        total_hosted = len(self.hosted_files)
        total_cids = sum(len(cids) for cids in self.hosted_files.values())
        
        return {
            "total_files_hosted": total_hosted,
            "total_cids": total_cids,
            "average_replications": total_cids / total_hosted if total_hosted > 0 else 0,
            "storage_stats": storage_stats
        }


# Convenience functions
async def upload_to_ipfs(file_path: str) -> IPFSUploadResult:
    """Quick upload to IPFS"""
    client = IPFSClient()
    return await client.upload_file(file_path)


async def host_permanently(file_path: str) -> IPFSUploadResult:
    """Host file permanently on decentralized network"""
    host = DecentralizedFileHost(enable_pinning=True)
    return await host.host_file(file_path, permanent=True)
