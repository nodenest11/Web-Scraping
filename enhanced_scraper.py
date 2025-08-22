import asyncio
import logging
import time
import random
from typing import List, Optional, Tuple, Dict
from urllib.parse import quote_plus, urlparse
from datetime import datetime
import re
import threading
from concurrent.futures import ThreadPoolExecutor

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import httpx
from bs4 import BeautifulSoup

from models import OrganicResult, RelatedQuestion, KnowledgeGraph, ScrapedContent
from utils import sanitize_text, extract_domain

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION SECTION - Easy to configure
# =============================================================================

import os

# Proxy Configuration - Load from environment or use defaults
PROXY_LIST = []
if os.getenv('PROXY_LIST'):
    PROXY_LIST = [p.strip() for p in os.getenv('PROXY_LIST').split(',') if p.strip()]

# Add your proxies here if not using environment variables
if not PROXY_LIST:
    PROXY_LIST = [
        # Add your proxies here in format: "http://username:password@host:port"
        # "http://user:pass@proxy1.example.com:8080",
        # "http://user:pass@proxy2.example.com:8080", 
        # "https://user:pass@proxy3.example.com:8080",
        # For proxies without auth: "http://proxy.example.com:8080"
    ]

# User-Agent List - High-quality, recent user agents
USER_AGENT_LIST = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    
    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# Delay Configuration (in seconds)
MIN_DELAY = 2.0
MAX_DELAY = 5.0
TYPING_DELAY_MIN = 0.1
TYPING_DELAY_MAX = 0.3

# Browser Configuration
HEADLESS_MODE = True  # Set to False for debugging
WINDOW_SIZE = (1920, 1080)

# =============================================================================
# Enhanced Undetected Chrome Scraper
# =============================================================================

class EnhancedUndetectedScraper:
    """Enhanced web scraper using undetected-chromedriver with advanced anti-detection"""
    
    def __init__(self):
        self.driver = None
        self.request_count = 0
        self.start_time = time.time()
        self.last_search_url = None
        self.current_proxy = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    def _get_random_proxy(self) -> Optional[str]:
        """Get a random proxy from the list"""
        if not PROXY_LIST:
            return None
        return random.choice(PROXY_LIST)
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the list"""
        return random.choice(USER_AGENT_LIST)
    
    def _get_random_delay(self) -> float:
        """Get a random delay between actions"""
        return random.uniform(MIN_DELAY, MAX_DELAY)
    
    def _get_typing_delay(self) -> float:
        """Get a random typing delay"""
        return random.uniform(TYPING_DELAY_MIN, TYPING_DELAY_MAX)
    
    async def initialize(self):
        """Initialize undetected Chrome browser with advanced anti-detection"""
        try:
            logger.info("🚀 Initializing undetected Chrome browser...")
            
            # Run browser initialization in thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, self._initialize_driver)
            
            logger.info("✅ Undetected Chrome browser initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize browser: {e}")
            await self.cleanup()
            raise
    
    def _initialize_driver(self):
        """Initialize the undetected Chrome driver (runs in thread)"""
        try:
            # Configure Chrome options for maximum stealth
            options = uc.ChromeOptions()
            
            # Basic stealth options
            if HEADLESS_MODE:
                options.add_argument('--headless=new')
            
            options.add_argument(f'--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # Faster loading
            options.add_argument('--disable-javascript')  # Optional, comment out if JS needed
            
            # Advanced anti-detection
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--exclude-switches=enable-automation')
            options.add_argument('--disable-extensions-file-access-check')
            options.add_argument('--disable-extensions-http-throttling')
            options.add_argument('--disable-default-apps')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
            
            # Memory optimization
            options.add_argument('--memory-pressure-off')
            options.add_argument('--max_old_space_size=4096')
            
            # Set random user agent
            user_agent = self._get_random_user_agent()
            options.add_argument(f'--user-agent={user_agent}')
            logger.info(f"🕵️  Using User-Agent: {user_agent}")
            
            # Configure proxy if available
            proxy = self._get_random_proxy()
            if proxy:
                self.current_proxy = proxy
                # Parse proxy URL
                if '@' in proxy:
                    # Proxy with authentication
                    auth_part, server_part = proxy.split('@')
                    protocol = auth_part.split('://')[0]
                    credentials = auth_part.split('://')[1]
                    options.add_argument(f'--proxy-server={protocol}://{server_part}')
                    logger.info(f"🔄 Using proxy: {protocol}://{server_part}")
                else:
                    # Proxy without authentication
                    options.add_argument(f'--proxy-server={proxy}')
                    logger.info(f"🔄 Using proxy: {proxy}")
            
            # Additional performance optimizations
            prefs = {
                "profile.default_content_setting_values": {
                    "images": 2,  # Block images
                    "stylesheets": 2,  # Block CSS (optional)
                    "plugins": 2,  # Block plugins
                    "popups": 2,  # Block popups
                    "geolocation": 2,  # Block location sharing
                    "notifications": 2,  # Block notifications
                    "media_stream": 2,  # Block media
                }
            }
            options.add_experimental_option("prefs", prefs)
            
            # Initialize undetected Chrome
            self.driver = uc.Chrome(
                options=options,
                version_main=None,  # Auto-detect Chrome version
                driver_executable_path=None,  # Auto-download if needed
                browser_executable_path=None,  # Use system Chrome
                user_data_dir=None,  # Use temp directory
                headless=HEADLESS_MODE,
                use_subprocess=True,
                debug=False
            )
            
            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            
            # Execute additional stealth scripts
            self._execute_stealth_scripts()
            
        except Exception as e:
            logger.error(f"❌ Driver initialization failed: {e}")
            raise
    
    def _execute_stealth_scripts(self):
        """Execute additional JavaScript to enhance stealth"""
        try:
            # Remove webdriver property
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Mock Chrome runtime
            self.driver.execute_script("""
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {
                        return {
                            requestTime: Date.now() / 1000,
                            startLoadTime: Date.now() / 1000,
                            commitLoadTime: Date.now() / 1000,
                            finishDocumentLoadTime: Date.now() / 1000,
                            finishLoadTime: Date.now() / 1000,
                            firstPaintTime: Date.now() / 1000,
                            firstPaintAfterLoadTime: 0,
                            navigationType: 'Other',
                            wasFetchedViaSpdy: false,
                            wasNpnNegotiated: false,
                            npnNegotiatedProtocol: 'unknown',
                            wasAlternateProtocolAvailable: false,
                            connectionInfo: 'http/1.1'
                        };
                    },
                    csi: function() {
                        return {
                            startE: Date.now(),
                            onloadT: Date.now(),
                            pageT: Date.now(),
                            tran: 15
                        };
                    }
                };
            """)
            
            # Mock permissions
            self.driver.execute_script("""
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            # Mock plugins
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        return Array.from({length: 5}, (_, i) => ({
                            name: `Plugin ${i + 1}`,
                            description: `Description for plugin ${i + 1}`,
                            filename: `plugin${i + 1}.dll`,
                            length: 1
                        }));
                    },
                });
            """)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not execute stealth scripts: {e}")
    
    async def cleanup(self):
        """Clean shutdown of browser resources"""
        try:
            if self.driver:
                # Run cleanup in thread
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, self._cleanup_driver)
                logger.info("🛑 Browser closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing browser: {e}")
        finally:
            self.driver = None
    
    def _cleanup_driver(self):
        """Cleanup driver (runs in thread)"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
    
    async def is_browser_ready(self) -> bool:
        """Check if browser is operational"""
        try:
            if not self.driver:
                return False
            
            # Run check in thread
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, self._check_browser_health)
            
        except Exception as e:
            logger.warning(f"⚠️ Browser health check failed: {e}")
            return False
    
    def _check_browser_health(self) -> bool:
        """Check browser health (runs in thread)"""
        try:
            self.driver.execute_script("return navigator.userAgent;")
            return True
        except:
            return False
    
    def get_uptime(self) -> float:
        """Get scraper uptime in seconds"""
        return time.time() - self.start_time
    
    def get_last_search_url(self) -> Optional[str]:
        """Get the last search URL used"""
        return self.last_search_url
    
    async def search_comprehensive(self, query: str, engine: str = "google", num_results: int = 10) -> Tuple[List[OrganicResult], List[RelatedQuestion], Optional[KnowledgeGraph]]:
        """Comprehensive search with enhanced anti-detection"""
        self.request_count += 1
        logger.info(f"🔍 Enhanced Search #{self.request_count}: '{query}' (engine: {engine}, results: {num_results})")
        
        if engine.lower() == "google":
            return await self._search_google_enhanced(query, num_results)
        elif engine.lower() == "bing":
            return await self._search_bing_enhanced(query, num_results)
        else:
            logger.warning(f"⚠️ Unknown search engine: {engine}, defaulting to Google")
            return await self._search_google_enhanced(query, num_results)
    
    async def _search_google_enhanced(self, query: str, num_results: int) -> Tuple[List[OrganicResult], List[RelatedQuestion], Optional[KnowledgeGraph]]:
        """Enhanced Google search with undetected Chrome"""
        try:
            # Build Google search URL
            encoded_query = quote_plus(query)
            search_url = f"https://www.google.com/search?q={encoded_query}&num={min(num_results, 20)}&hl=en&gl=us"
            self.last_search_url = search_url
            
            # Run search in thread
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor, 
                self._perform_google_search, 
                search_url, query, num_results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Enhanced Google search failed: {e}")
            # Fallback to Bing
            logger.info("🔄 Falling back to Bing search...")
            return await self._search_bing_enhanced(query, num_results)
    
    def _perform_google_search(self, search_url: str, query: str, num_results: int) -> Tuple[List[OrganicResult], List[RelatedQuestion], Optional[KnowledgeGraph]]:
        """Perform Google search (runs in thread)"""
        try:
            logger.info("🏠 Visiting Google homepage first...")
            
            # Visit Google homepage to get cookies and appear more human
            self.driver.get("https://www.google.com")
            
            # Random delay
            time.sleep(self._get_random_delay())
            
            # Check for cookie consent and handle it
            try:
                accept_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'I agree')]"))
                )
                accept_button.click()
                time.sleep(1)
            except TimeoutException:
                pass  # No cookie consent found
            
            # Navigate to search URL
            logger.info(f"🔍 Searching for: {query}")
            self.driver.get(search_url)
            
            # Random delay after loading
            time.sleep(self._get_random_delay())
            
            # Check for CAPTCHA
            page_source = self.driver.page_source
            if "recaptcha" in page_source.lower() or "unusual traffic" in page_source.lower():
                logger.warning("🚨 Google CAPTCHA detected - trying search box approach...")
                return self._try_alternative_google_search(query, num_results)
            
            # Wait for results to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-ved], .g, .MjjYud"))
                )
            except TimeoutException:
                logger.warning("⚠️ Results took too long to load")
            
            # Extract results
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            organic_results = self._extract_google_organic_results_enhanced(soup)
            related_questions = self._extract_google_related_questions(soup)
            knowledge_graph = self._extract_google_knowledge_graph(soup)
            
            logger.info(f"✅ Enhanced Google search extracted: {len(organic_results)} organic, {len(related_questions)} questions")
            
            return organic_results[:num_results], related_questions, knowledge_graph
            
        except Exception as e:
            logger.error(f"❌ Google search execution failed: {e}")
            return [], [], None
    
    def _try_alternative_google_search(self, query: str, num_results: int) -> Tuple[List[OrganicResult], List[RelatedQuestion], Optional[KnowledgeGraph]]:
        """Alternative Google search method when CAPTCHA is detected"""
        try:
            logger.info("🔄 Trying alternative search approach...")
            
            # Go to Google homepage
            self.driver.get("https://www.google.com")
            time.sleep(self._get_random_delay())
            
            # Find search box and type query with human-like typing
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Clear any existing text
            search_box.clear()
            time.sleep(1)
            
            # Type query with delays to simulate human typing
            for char in query:
                search_box.send_keys(char)
                time.sleep(self._get_typing_delay())
            
            # Random delay before submitting
            time.sleep(random.uniform(1, 2))
            
            # Submit search
            search_box.submit()
            
            # Wait for results
            time.sleep(self._get_random_delay())
            
            # Extract results
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            organic_results = self._extract_google_organic_results_enhanced(soup)
            related_questions = self._extract_google_related_questions(soup)
            knowledge_graph = self._extract_google_knowledge_graph(soup)
            
            return organic_results[:num_results], related_questions, knowledge_graph
            
        except Exception as e:
            logger.error(f"❌ Alternative Google search failed: {e}")
            return [], [], None
    
    async def _search_bing_enhanced(self, query: str, num_results: int) -> Tuple[List[OrganicResult], List[RelatedQuestion], Optional[KnowledgeGraph]]:
        """Enhanced Bing search as fallback"""
        try:
            # Use httpx for Bing as it's more reliable
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                
                encoded_query = quote_plus(query)
                search_url = f"https://www.bing.com/search?q={encoded_query}&count={min(num_results, 20)}&mkt=en-US"
                self.last_search_url = search_url
                
                # Random delay before request
                await asyncio.sleep(self._get_random_delay())
                
                response = await client.get(search_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                organic_results = self._extract_bing_organic_results(soup)
                related_questions = self._extract_bing_related_questions(soup)
                knowledge_graph = self._extract_bing_knowledge_graph(soup)
                
                logger.info(f"✅ Enhanced Bing search extracted: {len(organic_results)} organic, {len(related_questions)} questions")
                
                return organic_results[:num_results], related_questions, knowledge_graph
                
        except Exception as e:
            logger.error(f"❌ Enhanced Bing search failed: {e}")
            return [], [], None
    
    def _extract_google_organic_results_enhanced(self, soup: BeautifulSoup) -> List[OrganicResult]:
        """Enhanced extraction of Google organic results"""
        results = []
        position = 1
        
        # Multiple selector strategies for different Google layouts
        selector_strategies = [
            {
                'container': '.MjjYud, .g, .hlcw0c',
                'title': 'h3, .LC20lb, .DKV0Md',
                'link': 'a[href^="http"]',
                'snippet': '.VwiC3b, .s3v9rd, .aCOpRe, [data-sncf="1"]'
            },
            {
                'container': '.g, .rc',
                'title': 'h3',
                'link': 'a',
                'snippet': '.s, .st'
            },
            {
                'container': '[data-ved]:has(h3)',
                'title': 'h3',
                'link': 'a[href^="http"]',
                'snippet': 'span'
            }
        ]
        
        for strategy_idx, strategy in enumerate(selector_strategies):
            containers = soup.select(strategy['container'])
            
            for container in containers:
                try:
                    # Extract title
                    title_elem = container.select_one(strategy['title'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Extract link
                    link_elem = title_elem.find_parent('a') or container.select_one(strategy['link'])
                    if not link_elem:
                        continue
                    
                    href = link_elem.get('href')
                    if not href or not href.startswith('http'):
                        continue
                    
                    # Skip Google internal links
                    if any(domain in href.lower() for domain in ['google.com', 'youtube.com/results', 'accounts.google']):
                        continue
                    
                    # Extract snippet
                    snippet = ""
                    snippet_elem = container.select_one(strategy['snippet'])
                    if snippet_elem:
                        snippet = snippet_elem.get_text(strip=True)
                        snippet = re.sub(r'\s+', ' ', snippet)
                        snippet = snippet.replace('...', '').strip()
                    
                    # Skip duplicates
                    if any(result.link == href for result in results):
                        continue
                    
                    result = OrganicResult(
                        position=position,
                        title=title,
                        link=href,
                        snippet=snippet[:300],
                        displayed_link=extract_domain(href)
                    )
                    
                    results.append(result)
                    position += 1
                    
                    if len(results) >= 20:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error parsing result: {e}")
                    continue
            
            if results:
                break
        
        return results
    
    def _extract_google_related_questions(self, soup: BeautifulSoup) -> List[RelatedQuestion]:
        """Extract People Also Ask questions from Google"""
        questions = []
        
        # Try to find PAA questions
        paa_elements = soup.select('[data-ved*="2ahUKEwj"] span, .related-question-pair span')
        
        for elem in paa_elements:
            text = elem.get_text(strip=True)
            if text and text.endswith('?') and len(text) > 10:
                questions.append(RelatedQuestion(question=text))
        
        return questions[:10]
    
    def _extract_google_knowledge_graph(self, soup: BeautifulSoup) -> Optional[KnowledgeGraph]:
        """Extract knowledge graph from Google"""
        try:
            kg_container = soup.select_one('.kno-rdesc, .I6TXqe')
            
            if kg_container:
                title_elem = soup.select_one('.qrShPb, .kno-ecr-pt')
                title = title_elem.get_text(strip=True) if title_elem else None
                
                desc_elem = kg_container.select_one('span')
                description = desc_elem.get_text(strip=True) if desc_elem else None
                
                if title or description:
                    return KnowledgeGraph(
                        title=title,
                        description=description,
                        type="knowledge_graph"
                    )
        except Exception as e:
            logger.debug(f"Error extracting knowledge graph: {e}")
        
        return None
    
    def _extract_bing_organic_results(self, soup: BeautifulSoup) -> List[OrganicResult]:
        """Extract organic search results from Bing"""
        results = []
        position = 1
        
        result_containers = soup.select('.b_algo')
        
        for container in result_containers:
            try:
                title_link = container.select_one('h2 a')
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                href = title_link.get('href')
                
                if not href or not href.startswith('http'):
                    continue
                
                snippet_elem = container.select_one('.b_caption p')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                result = OrganicResult(
                    position=position,
                    title=title,
                    link=href,
                    snippet=snippet,
                    displayed_link=extract_domain(href)
                )
                
                results.append(result)
                position += 1
                
            except Exception as e:
                logger.debug(f"Error parsing Bing result: {e}")
                continue
        
        return results
    
    def _extract_bing_related_questions(self, soup: BeautifulSoup) -> List[RelatedQuestion]:
        """Extract related questions from Bing"""
        questions = []
        
        question_elements = soup.select('.b_ans .b_focusTextLarge, .df_alsoasked')
        
        for elem in question_elements:
            text = elem.get_text(strip=True)
            if text and '?' in text:
                questions.append(RelatedQuestion(question=text))
        
        return questions[:10]
    
    def _extract_bing_knowledge_graph(self, soup: BeautifulSoup) -> Optional[KnowledgeGraph]:
        """Extract knowledge graph from Bing"""
        try:
            answer_box = soup.select_one('.b_ans, .b_entityTP')
            
            if answer_box:
                title_elem = answer_box.select_one('.b_entityTitle, h2')
                title = title_elem.get_text(strip=True) if title_elem else None
                
                desc_elem = answer_box.select_one('.b_entitySubTypes, .b_snippet')
                description = desc_elem.get_text(strip=True) if desc_elem else None
                
                if title or description:
                    return KnowledgeGraph(
                        title=title,
                        description=description,
                        type="answer_box"
                    )
        except Exception as e:
            logger.debug(f"Error extracting Bing knowledge graph: {e}")
        
        return None
    
    async def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        """Scrape content from a specific URL with enhanced anti-detection"""
        try:
            self.request_count += 1
            logger.info(f"📄 Enhanced URL Scraping #{self.request_count}: {extract_domain(url)}")
            
            # Run scraping in thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, self._scrape_url_sync, url)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced URL scraping failed for {url}: {e}")
            return None
    
    def _scrape_url_sync(self, url: str) -> Optional[ScrapedContent]:
        """Synchronous URL scraping (runs in thread)"""
        try:
            # Random delay before navigation
            time.sleep(self._get_random_delay())
            
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(self._get_random_delay())
            
            # Get page title
            title = self.driver.title
            
            # Get meta description
            meta_desc = ""
            try:
                meta_elem = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                meta_desc = meta_elem.get_attribute('content') or ""
            except:
                pass
            
            # Extract content using BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
                element.decompose()
            
            content_blocks = []
            
            # Extract from common content selectors
            content_selectors = [
                'article', 'main', '[role="main"]', '.content',
                '.article-content', '.post-content', '.entry-content',
                '.article-body', 'p'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 50:
                        clean_text = sanitize_text(text)
                        if clean_text and clean_text not in content_blocks:
                            content_blocks.append(clean_text)
            
            if content_blocks:
                scraped = ScrapedContent(
                    url=url,
                    title=title,
                    content=content_blocks[:25],  # Limit to 25 blocks
                    meta_description=meta_desc,
                    word_count=sum(len(text.split()) for text in content_blocks)
                )
                
                logger.info(f"✅ Enhanced scraping: {len(content_blocks)} paragraphs, {scraped.word_count} words")
                return scraped
            else:
                logger.warning(f"⚠️ No content extracted from {extract_domain(url)}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Sync URL scraping failed: {e}")
            return None
    
    async def restart_browser(self):
        """Restart browser for maintenance"""
        logger.info("🔄 Restarting enhanced browser...")
        
        try:
            await self.cleanup()
            await asyncio.sleep(2)
            await self.initialize()
            logger.info("✅ Enhanced browser restarted successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Enhanced browser restart failed: {e}")
            raise e
