"""
Direct Link Handler Registry
Provides centralized domain-to-handler mapping
"""

from urllib.parse import urlparse
from typing import Optional

from ...ext_utils.exceptions import DirectDownloadLinkException
from ...ext_utils.links_utils import is_share_link


class HandlerRegistry:
    """
    Centralized registry for mapping domains to download handlers
    Supports both single-domain and multi-domain mappings
    """

    # Single domain to handler mapping (O(1) lookup)
    SINGLE_DOMAIN_HANDLERS = {
        "buzzheavier.com": "buzzheavier",
        "devuploads": "devuploads",
        "lulacloud.com": "lulacloud",
        "uploadhaven": "uploadhaven",
        "fuckingfast.co": "fuckingfast_dl",
        "mediafile.cc": "mediafile",
        "mediafire.com": "mediafire",
        "osdn.net": "osdn",
        "github.com": "github",
        "transfer.it": "transfer_it",
        "hxfile.co": "hxfile",
        "1drv.ms": "onedrive",
        "racaty": "racaty",
        "1fichier.com": "fichier",
        "solidfiles.com": "solidfiles",
        "krakenfiles.com": "krakenfiles",
        "upload.ee": "uploadee",
        "gofile.io": "gofile",
        "send.cm": "send_cm",
        "tmpsend.com": "tmpsend",
        "easyupload.io": "easyupload",
        "streamvid.net": "streamvid",
        "shrdsk.me": "shrdsk",
        "u.pcloud.link": "pcloud",
        "qiwi.gg": "qiwi",
        "mp4upload.com": "mp4upload",
        "berkasdrive.com": "berkasdrive",
        "swisstransfer.com": "swisstransfer",
        "mediafire.com/folder": "mediafireFolder",
    }

    # Multi-domain to handler mapping
    MULTI_DOMAIN_HANDLERS = {
        ("pixeldrain.com", "pixeldra.in"): "pixeldrain",
        ("akmfiles.com", "akmfls.xyz"): "akmfiles",
        (
            "dood.watch", "doodstream.com", "dood.to", "dood.so", "dood.cx",
            "dood.la", "dood.ws", "dood.sh", "doodstream.co", "dood.pm",
            "dood.wf", "dood.re", "dood.video", "dooood.com", "dood.yt",
            "doods.yt", "dood.stream", "doods.pro", "ds2play.com", "d0o0d.com",
            "ds2video.com", "do0od.com", "d000d.com"
        ): "doods",
        (
            "streamtape.com", "streamtape.co", "streamtape.cc", "streamtape.to",
            "streamtape.net", "streamta.pe", "streamtape.xyz"
        ): "streamtape",
        ("wetransfer.com", "we.tl"): "wetransfer",
        (
            "terabox.com", "nephobox.com", "4funbox.com", "mirrobox.com",
            "momerybox.com", "teraboxapp.com", "1024tera.com", "terabox.app",
            "gibibox.com", "goaibox.com", "terasharelink.com", "teraboxlink.com",
            "freeterabox.com", "1024terabox.com", "teraboxshare.com",
            "terafileshare.com", "terabox.club"
        ): "terabox",
        (
            "filelions.co", "filelions.site", "filelions.live", "filelions.to",
            "mycloudz.cc", "cabecabean.lol", "filelions.online", "embedwish.com",
            "kitabmarkaz.xyz", "wishfast.top", "streamwish.to", "kissmovies.net"
        ): "filelions_and_streamwish",
        ("streamhub.ink", "streamhub.to"): "streamhub",
        (
            "linkbox.to", "lbx.to", "teltobx.net", "telbx.net", "linkbox.cloud"
        ): "linkBox",
        (
            "anonfiles.com", "zippyshare.com", "letsupload.io", "hotfile.io",
            "bayfiles.com", "megaupload.nz", "letsupload.cc", "filechan.org",
            "myfile.is", "vshare.is", "rapidshare.nu", "lolabits.se",
            "openload.cc", "share-online.is", "upvid.cc", "uptobox.com", "uptobox.fr"
        ): "deprecated",
    }

    # Special handlers (require custom logic)
    SPECIAL_HANDLERS = {
        "yandex": "yandex_disk",
        "filepress": "filepress",
        "share_link": "sharer_scraper",
        "cf_bypass": "cf_bypass",
    }

    @classmethod
    def _check_special_handlers(cls, url: str, domain: str) -> Optional[str]:
        """Check for special case handlers"""
        if "yadi.sk" in url or "disk.yandex." in url:
            return cls.SPECIAL_HANDLERS["yandex"]
        
        if is_share_link(url):
            return "filepress" if "filepress" in domain else cls.SPECIAL_HANDLERS["share_link"]
        
        return None
    
    @classmethod
    def _check_deprecated_domains(cls, domain: str) -> None:
        """Check if domain is deprecated and raise exception"""
        for domains, handler in cls.MULTI_DOMAIN_HANDLERS.items():
            if handler == "deprecated" and any(d in domain for d in domains):
                raise DirectDownloadLinkException(f"ERROR: R.I.P {domain}")
    
    @classmethod
    def _lookup_domain_handler(cls, domain: str) -> Optional[str]:
        """Lookup handler by domain (single or multi)"""
        # Try single domain lookup first (O(1))
        if handler := cls.SINGLE_DOMAIN_HANDLERS.get(domain):
            return handler
        
        # Try multi-domain lookup
        for domains, handler in cls.MULTI_DOMAIN_HANDLERS.items():
            if any(d in domain for d in domains):
                return handler
        
        return None
    
    @classmethod
    def get_handler_name(cls, url: str) -> str:
        """Get handler name for a URL
        Returns handler name or raises DirectDownloadLinkException if not found
        """
        parsed = urlparse(url)
        domain = parsed.hostname or ""

        # Check special cases first
        if special_handler := cls._check_special_handlers(url, domain):
            return special_handler

        # Check deprecated domains
        cls._check_deprecated_domains(domain)

        # Lookup domain handler
        if handler := cls._lookup_domain_handler(domain):
            return handler

        # No handler found
        raise DirectDownloadLinkException(
            f"No Direct link function found for {url}"
        )

    @classmethod
    def register_single(cls, domain: str, handler_name: str) -> None:
        """Register a single domain handler"""
        cls.SINGLE_DOMAIN_HANDLERS[domain] = handler_name

    @classmethod
    def register_multi(cls, domains: tuple[str, ...], handler_name: str) -> None:
        """Register multiple domain handler"""
        cls.MULTI_DOMAIN_HANDLERS[domains] = handler_name

    @classmethod
    def register_special(cls, key: str, handler_name: str) -> None:
        """Register special handler"""
        cls.SPECIAL_HANDLERS[key] = handler_name
