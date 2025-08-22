import random
import logging
import os
import time
from typing import List, Optional
from fake_useragent import UserAgent
from fastapi import Request

# Configure logging
def setup_logging():
    """Setup comprehensive logging configuration"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/tmp/scraper.log') if os.path.exists('/tmp') else logging.NullHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}")
    return logging.getLogger("scraper")


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers"""
    # Check for forwarded headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    return request.client.host if request.client else "unknown"


def get_random_delay() -> float:
    """Get a random delay between requests to avoid detection"""
    return random.uniform(1.0, 3.0)


class ProxyRotator:
    """Professional proxy rotation system for avoiding IP blocking"""
    
    def __init__(self, proxies: Optional[List[str]] = None):
        logger = logging.getLogger("scraper")
        
        # Load proxies from environment or parameter
        env_proxies = os.getenv('PROXY_LIST')
        if env_proxies:
            proxy_list = [p.strip() for p in env_proxies.split(',') if p.strip()]
            logger.info(f"Loaded {len(proxy_list)} proxies from environment")
        else:
            proxy_list = proxies or []
        
        # Add some free public proxies for testing (replace with your premium proxies)
        free_proxies = [
            # Note: These are example proxies - replace with real working proxies
            # "http://proxy1.example.com:8080",
            # "http://proxy2.example.com:8080",
        ]
        
        self.proxies = proxy_list + free_proxies
        self.enabled = len(self.proxies) > 0
        self.current_index = 0
        self.failed_proxies = set()
        
        if self.enabled:
            logger.info(f"ProxyRotator initialized with {len(self.proxies)} proxies")
        else:
            logger.info("ProxyRotator initialized without proxies (direct connection)")
    
    def get_random_proxy(self) -> Optional[str]:
        """Get a random working proxy"""
        logger = logging.getLogger("scraper")
        
        if not self.enabled or not self.proxies:
            return None
        
        available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
        
        if not available_proxies:
            # Reset failed proxies if all have failed
            logger.warning("All proxies failed, resetting failure list")
            self.failed_proxies.clear()
            available_proxies = self.proxies
        
        proxy = random.choice(available_proxies)
        logger.debug(f"Using proxy: {proxy}")
        return proxy
    
    def mark_proxy_failed(self, proxy: str):
        """Mark a proxy as failed"""
        logger = logging.getLogger("scraper")
        if proxy:
            self.failed_proxies.add(proxy)
            logger.warning(f"Marked proxy as failed: {proxy}")
    
    def get_proxy_config(self) -> Optional[dict]:
        """Get proxy configuration for httpx/playwright"""
        proxy = self.get_random_proxy()
        if not proxy:
            return None
        
        return {
            "server": proxy,
            "username": os.getenv('PROXY_USERNAME'),
            "password": os.getenv('PROXY_PASSWORD')
        }


class EnhancedUserAgentRotator:
    """Enhanced user agent rotation with browser fingerprint simulation"""
    
    def __init__(self):
        logger = logging.getLogger("scraper")
        
        try:
            self.ua = UserAgent()
            logger.debug("UserAgent library initialized successfully")
        except Exception as e:
            logger.warning(f"UserAgent library failed to initialize: {e}")
            self.ua = None
            
        # Professional browser fingerprints with realistic configurations
        self.browser_profiles = [
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080},
                "platform": "Win32",
                "languages": ["en-US", "en"],
                "timezone": "America/New_York"
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "viewport": {"width": 1440, "height": 900},
                "platform": "MacIntel",
                "languages": ["en-US", "en"],
                "timezone": "America/Los_Angeles"
            },
            {
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "viewport": {"width": 1366, "height": 768},
                "platform": "Linux x86_64",
                "languages": ["en-US", "en"],
                "timezone": "America/Chicago"
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
                "viewport": {"width": 1920, "height": 1080},
                "platform": "Win32",
                "languages": ["en-US", "en"],
                "timezone": "America/New_York"
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
                "viewport": {"width": 1440, "height": 900},
                "platform": "MacIntel",
                "languages": ["en-US", "en"],
                "timezone": "America/Los_Angeles"
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
                "viewport": {"width": 1920, "height": 1080},
                "platform": "Win32",
                "languages": ["en-US", "en"],
                "timezone": "America/New_York"
            }
        ]
        
        logger.info(f"Enhanced UserAgent rotator initialized with {len(self.browser_profiles)} profiles")
    
    def get_random_profile(self) -> dict:
        """Get a random browser profile with all fingerprint data"""
        return random.choice(self.browser_profiles)
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent string (backward compatibility)"""
        logger = logging.getLogger("scraper")
        
        if self.ua:
            try:
                agent = self.ua.random
                logger.debug(f"Using fake-useragent: {agent[:50]}...")
                return agent
            except Exception as e:
                logger.debug(f"fake-useragent failed, using profile: {e}")
        
        profile = self.get_random_profile()
        return profile["user_agent"]


class UserAgentRotator:
    """Legacy UserAgentRotator for backward compatibility"""
    
    def __init__(self):
        self.enhanced = EnhancedUserAgentRotator()
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        return self.enhanced.get_random_user_agent()


def is_social_media_url(url: str) -> bool:
    """Check if URL is from social media platform"""
    social_domains = [
        'twitter.com', 'x.com', 'facebook.com', 'instagram.com', 
        'linkedin.com', 'tiktok.com', 'youtube.com', 'reddit.com',
        'pinterest.com', 'snapchat.com', 'discord.com'
    ]
    return any(domain in url.lower() for domain in social_domains)


def sanitize_text(text: str) -> str:
    """Sanitize and clean extracted text"""
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize
    text = ' '.join(text.split())
    
    # Remove common unwanted patterns
    unwanted_patterns = [
        'Skip to main content',
        'Accept cookies',
        'Privacy policy',
        'Terms of service',
        'Cookie notice'
    ]
    
    for pattern in unwanted_patterns:
        text = text.replace(pattern, '')
    
    return text.strip()


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return url


# Initialize global instances
proxy_rotator = ProxyRotator()
user_agent_rotator = EnhancedUserAgentRotator()
