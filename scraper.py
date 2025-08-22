import asyncio
import logging
import time
import random
from typing import List, Optional, Tuple
from urllib.parse import quote_plus, urlparse
from datetime import datetime
import re

import httpx
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

from models import OrganicResult, RelatedQuestion, KnowledgeGraph, ScrapedContent
from utils import (
    user_agent_rotator, 
    proxy_rotator, 
    is_social_media_url, 
    sanitize_text, 
    extract_domain,
    get_random_delay
)

logger = logging.getLogger(__name__)


class UniversalScraper:
    """High-performance universal web scraper optimized for SERP-like responses"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.request_count = 0
        self.start_time = time.time()
        self.last_search_url = None
        self.proxy_enabled = proxy_rotator.enabled
        
        # Performance settings
        self.max_retries = 3
        self.request_timeout = 30000
        self.navigation_timeout = 30000
        
    async def initialize(self):
        """Initialize browser with professional anti-detection settings"""
        try:
            logger.info("🚀 Initializing Playwright browser with professional anti-detection...")
            
            self.playwright = await async_playwright().start()
            
            # Get proxy configuration if available
            proxy_config = proxy_rotator.get_proxy_config()
            
            # Cloud-optimized browser launch arguments
            launch_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-translate',
                '--hide-scrollbars',
                '--metrics-recording-only',
                '--mute-audio',
                '--no-default-browser-check',
                '--no-pings',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                # Enhanced anti-detection
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor,AutofillShowTypePredictions',
                '--disable-ipc-flooding-protection',
                '--exclude-switches=enable-automation',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--disable-extensions',
                # Cloud deployment optimizations
                '--single-process',
                '--disable-background-networking',
                '--disable-features=TranslateUI',
                '--disable-client-side-phishing-detection',
                '--disable-default-apps',
                '--memory-pressure-off',
                '--max_old_space_size=4096',
                # For DigitalOcean and cloud environments
                '--disable-software-rasterizer',
                '--disable-accelerated-2d-canvas',
                '--disable-accelerated-jpeg-decoding',
                '--disable-accelerated-mjpeg-decode',
                '--disable-accelerated-video-decode'
            ]
            
            # Launch browser with or without proxy
            if proxy_config:
                logger.info(f"🔄 Using proxy: {proxy_config['server']}")
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=launch_args,
                    proxy=proxy_config
                )
            else:
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=launch_args
                )
            
            logger.info("✅ Browser initialized successfully with professional anti-detection")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize browser: {e}")
            await self.cleanup()
            raise
    
    async def cleanup(self):
        """Clean shutdown of browser resources"""
        try:
            if self.browser:
                await self.browser.close()
                logger.info("🛑 Browser closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing browser: {e}")
        
        try:
            if self.playwright:
                await self.playwright.stop()
                logger.info("🛑 Playwright stopped")
        except Exception as e:
            logger.warning(f"⚠️ Error stopping playwright: {e}")
        
        self.browser = None
        self.playwright = None
    
    async def restart_browser(self):
        """Restart browser for maintenance and optimal performance"""
        logger.info("🔄 Restarting browser for optimal performance...")
        
        try:
            # Close existing browser
            if self.browser:
                await self.browser.close()
                logger.info("✅ Old browser closed")
            
            # Reinitialize browser
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-web-security',
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-extensions',
                    '--disable-plugins'
                ]
            )
            
            logger.info("✅ Browser restarted successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser restart failed: {e}")
            raise e

    async def is_browser_ready(self) -> bool:
        """Check if browser is operational"""
        try:
            if not self.browser:
                return False
            
            # Quick health check
            context = await self.browser.new_context()
            await context.close()
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Browser health check failed: {e}")
            return False
    
    def get_uptime(self) -> float:
        """Get scraper uptime in seconds"""
        return time.time() - self.start_time
    
    def get_last_search_url(self) -> Optional[str]:
        """Get the last search URL used"""
        return self.last_search_url
    
    async def search_comprehensive(self, query: str, engine: str = "google", num_results: int = 10) -> Tuple[List[OrganicResult], List[RelatedQuestion], Optional[KnowledgeGraph]]:
        """
        Comprehensive search that extracts organic results, related questions, and knowledge graph
        """
        self.request_count += 1
        logger.info(f"🔍 Search #{self.request_count}: '{query}' (engine: {engine}, results: {num_results})")
        
        if engine.lower() == "google":
            return await self._search_google(query, num_results)
        elif engine.lower() == "bing":
            return await self._search_bing(query, num_results)
        else:
            logger.warning(f"⚠️ Unknown search engine: {engine}, defaulting to Google")
            return await self._search_google(query, num_results)
    
    async def _search_google(self, query: str, num_results: int) -> Tuple[List[OrganicResult], List[RelatedQuestion], Optional[KnowledgeGraph]]:
        """Search Google and extract comprehensive results with enhanced anti-detection"""
        
        # Build Google search URL
        encoded_query = quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}&num={min(num_results, 20)}&hl=en&gl=us"
        self.last_search_url = search_url
        
        context = None
        page = None
        
        try:
            # Enhanced professional browser fingerprinting
            profile = user_agent_rotator.get_random_profile()
            logger.info(f"🕵️  Using professional profile: {profile['user_agent'][:50]}...")
            
            # Create browser context with professional anti-detection fingerprint
            context = await self.browser.new_context(
                user_agent=profile['user_agent'],
                viewport=profile['viewport'],
                locale='en-US',
                timezone_id=profile['timezone'],
                permissions=['geolocation'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # NYC
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': ','.join(profile['languages']) + ';q=0.9,*;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0',
                    'Sec-CH-UA': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                    'Sec-CH-UA-Mobile': '?0',
                    'Sec-CH-UA-Platform': f'"{profile["platform"]}"'
                }
            )
            
            page = await context.new_page()
            
            # Professional stealth script injection
            await page.add_init_script(f"""
                // Remove webdriver traces
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => undefined,
                }});
                
                // Simulate realistic navigator properties
                Object.defineProperty(navigator, 'plugins', {{
                    get: () => {{
                        return Array.from({{length: 5}}, (_, i) => ({{
                            name: `Plugin ${{i + 1}}`,
                            description: `Description for plugin ${{i + 1}}`,
                            filename: `plugin${{i + 1}}.dll`
                        }}));
                    }},
                }});
                
                Object.defineProperty(navigator, 'languages', {{
                    get: () => {profile['languages']},
                }});
                
                Object.defineProperty(navigator, 'platform', {{
                    get: () => '{profile["platform"]}',
                }});
                
                // Mock Chrome runtime
                window.chrome = {{
                    runtime: {{
                        onConnect: undefined,
                        onMessage: undefined,
                        connect: function() {{}},
                        sendMessage: function() {{}}
                    }},
                    loadTimes: function() {{
                        return {{
                            requestTime: Date.now() / 1000 - Math.random(),
                            startLoadTime: Date.now() / 1000 - Math.random(),
                            commitLoadTime: Date.now() / 1000 - Math.random(),
                            finishDocumentLoadTime: Date.now() / 1000 - Math.random(),
                            finishLoadTime: Date.now() / 1000 - Math.random(),
                            firstPaintTime: Date.now() / 1000 - Math.random(),
                            firstPaintAfterLoadTime: 0,
                            navigationType: 'Other',
                            wasFetchedViaSpdy: false,
                            wasNpnNegotiated: false,
                            npnNegotiatedProtocol: 'unknown',
                            wasAlternateProtocolAvailable: false,
                            connectionInfo: 'http/1.1'
                        }};
                    }},
                    csi: function() {{
                        return {{
                            startE: Date.now(),
                            onloadT: Date.now() + Math.random() * 1000,
                            pageT: Date.now() + Math.random() * 2000,
                            tran: 15
                        }};
                    }},
                    app: {{
                        isInstalled: false,
                        InstallState: {{
                            DISABLED: 'disabled',
                            INSTALLED: 'installed',
                            NOT_INSTALLED: 'not_installed'
                        }},
                        RunningState: {{
                            CANNOT_RUN: 'cannot_run',
                            READY_TO_RUN: 'ready_to_run',
                            RUNNING: 'running'
                        }}
                    }}
                }};
                
                // Mock permissions API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({{ state: Notification.permission }}) :
                        originalQuery(parameters)
                );
                
                // Remove automation indicators
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                
                // Mock connection speed
                Object.defineProperty(navigator, 'connection', {{
                    get: () => ({{
                        effectiveType: '4g',
                        rtt: 50 + Math.random() * 50,
                        downlink: 10 + Math.random() * 10
                    }}),
                }});
                
                // Mock device memory
                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => 8,
                }});
                
                // Random mouse movements to simulate human behavior
                let mouseX = Math.random() * window.innerWidth;
                let mouseY = Math.random() * window.innerHeight;
                
                setInterval(() => {{
                    mouseX += (Math.random() - 0.5) * 5;
                    mouseY += (Math.random() - 0.5) * 5;
                    mouseX = Math.max(0, Math.min(window.innerWidth, mouseX));
                    mouseY = Math.max(0, Math.min(window.innerHeight, mouseY));
                }}, 100 + Math.random() * 200);
            """)
            
            # Block unnecessary resources but keep essential ones for search
            await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,mp4,mp3}", lambda route: route.abort())
            await page.route("**/ads/**", lambda route: route.abort())
            await page.route("**/analytics/**", lambda route: route.abort())
            await page.route("**/tracking/**", lambda route: route.abort())
            
            # Allow CSS for layout detection but block heavy assets
            await page.route("**/*.css", lambda route: route.continue_() if "google" in route.request.url else route.abort())
            
            # First visit Google homepage to get cookies
            logger.info("🏠 Visiting Google homepage first...")
            await page.goto("https://www.google.com", wait_until='domcontentloaded', timeout=15000)
            
            # Random delay to appear more human-like
            await asyncio.sleep(random.uniform(2, 4))
            
            # Navigate to search results
            logger.info(f"🔍 Searching for: {query}")
            await page.goto(search_url, wait_until='domcontentloaded', timeout=self.navigation_timeout)
            
            # Check for CAPTCHA or bot detection
            content = await page.content()
            if "recaptcha" in content.lower() or "unusual traffic" in content.lower():
                logger.warning("🚨 Google CAPTCHA detected - trying alternative approach...")
                
                # Try alternative approach: search via input box
                try:
                    await page.goto("https://www.google.com", wait_until='domcontentloaded')
                    await asyncio.sleep(2)
                    
                    # Find search input and type query
                    search_input = await page.wait_for_selector('input[name="q"]', timeout=5000)
                    await search_input.type(query, delay=random.randint(50, 150))
                    await asyncio.sleep(1)
                    
                    # Press Enter
                    await page.keyboard.press('Enter')
                    await page.wait_for_load_state('domcontentloaded')
                    
                    content = await page.content()
                    
                except Exception as e:
                    logger.error(f"Alternative search approach failed: {e}")
                    # Fallback to Bing if Google consistently fails
                    logger.info("🔄 Falling back to Bing search...")
                    return await self._search_bing(query, num_results)
            
            # Wait for results with multiple possible selectors
            result_selectors = ['div[data-ved]', '.g', '.MjjYud', '.hlcw0c']
            
            for selector in result_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"✅ Found results with selector: {selector}")
                    break
                except:
                    continue
            else:
                logger.warning("⚠️ No standard result selectors found, continuing with content extraction...")
            
            # Extract page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Enhanced result extraction with multiple strategies
            organic_results = self._extract_google_organic_results_enhanced(soup)
            related_questions = self._extract_google_related_questions(soup)
            knowledge_graph = self._extract_google_knowledge_graph(soup)
            
            logger.info(f"✅ Google search extracted: {len(organic_results)} organic, {len(related_questions)} questions")
            
            return organic_results[:num_results], related_questions, knowledge_graph
            
        except Exception as e:
            logger.error(f"❌ Google search failed: {e}")
            # Fallback to Bing
            logger.info("🔄 Falling back to Bing search...")
            return await self._search_bing(query, num_results)
            
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
    
    async def _search_bing(self, query: str, num_results: int) -> Tuple[List[OrganicResult], List[RelatedQuestion], Optional[KnowledgeGraph]]:
        """Search Bing and extract comprehensive results"""
        
        # Build Bing search URL
        encoded_query = quote_plus(query)
        search_url = f"https://www.bing.com/search?q={encoded_query}&count={min(num_results, 20)}&mkt=en-US"
        self.last_search_url = search_url
        
        try:
            # Use httpx for Bing as it's more reliable for this search engine
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    'User-Agent': user_agent_rotator.get_random_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                
                response = await client.get(search_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract different types of results
                organic_results = self._extract_bing_organic_results(soup)
                related_questions = self._extract_bing_related_questions(soup)
                knowledge_graph = self._extract_bing_knowledge_graph(soup)
                
                logger.info(f"✅ Bing search extracted: {len(organic_results)} organic, {len(related_questions)} questions")
                
                return organic_results[:num_results], related_questions, knowledge_graph
                
        except Exception as e:
            logger.error(f"❌ Bing search failed: {e}")
            return [], [], None
    
    def _extract_google_organic_results(self, soup: BeautifulSoup) -> List[OrganicResult]:
        """Extract organic search results from Google"""
        results = []
        position = 1
        
        # Try multiple selectors for Google results
        result_selectors = [
            'div[data-ved] h3',
            '.g h3',
            '[data-header-feature] h3',
            '.rc h3'
        ]
        
        for selector in result_selectors:
            elements = soup.select(selector)
            for element in elements:
                try:
                    # Get the link element
                    link_elem = element.find_parent('a') or element.find('a')
                    if not link_elem:
                        continue
                    
                    href = link_elem.get('href')
                    if not href or not href.startswith('http'):
                        continue
                    
                    # Skip Google internal links
                    if 'google.com' in href:
                        continue
                    
                    title = element.get_text(strip=True)
                    if not title:
                        continue
                    
                    # Find snippet
                    snippet = ""
                    result_container = element.find_parent('[data-ved]') or element.find_parent('.g')
                    if result_container:
                        snippet_elem = result_container.select_one('[data-ved] span, .VwiC3b, .s3v9rd')
                        if snippet_elem:
                            snippet = snippet_elem.get_text(strip=True)
                    
                    # Create result
                    result = OrganicResult(
                        position=position,
                        title=title,
                        link=href,
                        snippet=snippet,
                        displayed_link=extract_domain(href)
                    )
                    
                    results.append(result)
                    position += 1
                    
                    if len(results) >= 20:  # Limit results
                        break
                        
                except Exception as e:
                    logger.debug(f"Error parsing Google result: {e}")
                    continue
            
            if results:  # If we found results with this selector, stop trying others
                break
        
        return results
    
    def _extract_google_organic_results_enhanced(self, soup: BeautifulSoup) -> List[OrganicResult]:
        """Enhanced extraction of Google organic results with multiple fallback strategies"""
        results = []
        position = 1
        
        # Multiple selector strategies for different Google layouts
        selector_strategies = [
            # Strategy 1: Modern Google (2023-2025)
            {
                'container': '.MjjYud, .g, .hlcw0c',
                'title': 'h3, .LC20lb, .DKV0Md',
                'link': 'a[href^="http"]',
                'snippet': '.VwiC3b, .s3v9rd, .aCOpRe, [data-sncf="1"]'
            },
            # Strategy 2: Classic Google
            {
                'container': '.g, .rc',
                'title': 'h3',
                'link': 'a',
                'snippet': '.s, .st'
            },
            # Strategy 3: Data-ved based
            {
                'container': '[data-ved]:has(h3)',
                'title': 'h3',
                'link': 'a[href^="http"]',
                'snippet': 'span:contains("...")'
            },
            # Strategy 4: Aggressive fallback
            {
                'container': 'div:has(h3):has(a[href^="http"])',
                'title': 'h3',
                'link': 'a[href^="http"]',
                'snippet': 'span, div'
            }
        ]
        
        for strategy_idx, strategy in enumerate(selector_strategies):
            logger.debug(f"Trying extraction strategy {strategy_idx + 1}")
            
            containers = soup.select(strategy['container'])
            logger.debug(f"Found {len(containers)} containers with strategy {strategy_idx + 1}")
            
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
                    
                    # Skip Google internal links and ads
                    if any(domain in href.lower() for domain in ['google.com', 'youtube.com/results', 'accounts.google']):
                        continue
                    
                    # Extract snippet
                    snippet = ""
                    snippet_elem = container.select_one(strategy['snippet'])
                    if snippet_elem:
                        snippet = snippet_elem.get_text(strip=True)
                        # Clean up snippet
                        snippet = re.sub(r'\s+', ' ', snippet)
                        snippet = snippet.replace('...', '').strip()
                    
                    # Skip if we already have this result
                    if any(result.link == href for result in results):
                        continue
                    
                    # Create result
                    result = OrganicResult(
                        position=position,
                        title=title,
                        link=href,
                        snippet=snippet[:300],  # Limit snippet length
                        displayed_link=extract_domain(href)
                    )
                    
                    results.append(result)
                    position += 1
                    
                    logger.debug(f"Extracted result {position-1}: {title[:50]}...")
                    
                    if len(results) >= 20:  # Limit results
                        break
                        
                except Exception as e:
                    logger.debug(f"Error parsing result with strategy {strategy_idx + 1}: {e}")
                    continue
            
            # If we found results with this strategy, use them
            if results:
                logger.info(f"✅ Successfully extracted {len(results)} results using strategy {strategy_idx + 1}")
                break
        
        if not results:
            logger.warning("⚠️ No results extracted with any strategy - checking for alternative content")
            # Fallback: extract any links that look like search results
            results = self._extract_google_fallback_results(soup)
        
        return results
    
    def _extract_google_fallback_results(self, soup: BeautifulSoup) -> List[OrganicResult]:
        """Fallback extraction for Google when standard selectors fail"""
        results = []
        position = 1
        
        # Find all links that could be results
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            try:
                href = link.get('href')
                
                # Skip non-http links and internal Google links
                if not href or not href.startswith('http'):
                    continue
                
                if any(domain in href.lower() for domain in [
                    'google.com', 'youtube.com/results', 'accounts.google',
                    'support.google', 'policies.google', 'maps.google'
                ]):
                    continue
                
                # Look for title in h3 or similar
                title_elem = link.find('h3') or link.find_parent().find('h3')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                if not title or len(title) < 10:
                    continue
                
                # Look for snippet
                snippet = ""
                parent_container = link.find_parent()
                if parent_container:
                    snippet_texts = []
                    for elem in parent_container.find_all(['span', 'div'], string=True):
                        text = elem.get_text(strip=True)
                        if text and len(text) > 20 and not text.lower().startswith('http'):
                            snippet_texts.append(text)
                    
                    snippet = ' '.join(snippet_texts[:2])  # Take first 2 meaningful texts
                
                # Skip if we already have this result
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
                
                if len(results) >= 10:  # Limit fallback results
                    break
                    
            except Exception as e:
                logger.debug(f"Error in fallback extraction: {e}")
                continue
        
        if results:
            logger.info(f"✅ Fallback extraction found {len(results)} results")
        
        return results
    
    def _extract_bing_organic_results(self, soup: BeautifulSoup) -> List[OrganicResult]:
        """Extract organic search results from Bing"""
        results = []
        position = 1
        
        # Find Bing result containers
        result_containers = soup.select('.b_algo')
        
        for container in result_containers:
            try:
                # Extract title and URL
                title_link = container.select_one('h2 a')
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                href = title_link.get('href')
                
                if not href or not href.startswith('http'):
                    continue
                
                # Handle Bing redirects
                if 'bing.com/ck/a' in href:
                    href = self._decode_bing_redirect(href) or href
                
                # Skip unwanted domains
                if any(domain in href.lower() for domain in ['bing.com', 'microsoft.com']):
                    continue
                
                # Extract snippet
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
    
    def _extract_google_related_questions(self, soup: BeautifulSoup) -> List[RelatedQuestion]:
        """Extract People Also Ask questions from Google"""
        questions = []
        
        # Try to find PAA questions
        paa_elements = soup.select('[data-ved*="2ahUKEwj"] span, .related-question-pair span')
        
        for elem in paa_elements:
            text = elem.get_text(strip=True)
            if text and text.endswith('?') and len(text) > 10:
                questions.append(RelatedQuestion(question=text))
        
        return questions[:10]  # Limit to 10 questions
    
    def _extract_bing_related_questions(self, soup: BeautifulSoup) -> List[RelatedQuestion]:
        """Extract related questions from Bing"""
        questions = []
        
        # Look for Bing's related questions
        question_elements = soup.select('.b_ans .b_focusTextLarge, .df_alsoasked')
        
        for elem in question_elements:
            text = elem.get_text(strip=True)
            if text and '?' in text:
                questions.append(RelatedQuestion(question=text))
        
        return questions[:10]
    
    def _extract_google_knowledge_graph(self, soup: BeautifulSoup) -> Optional[KnowledgeGraph]:
        """Extract knowledge graph from Google"""
        try:
            # Look for knowledge graph container
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
    
    def _extract_bing_knowledge_graph(self, soup: BeautifulSoup) -> Optional[KnowledgeGraph]:
        """Extract knowledge graph from Bing"""
        try:
            # Look for Bing's answer box
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
    
    def _decode_bing_redirect(self, redirect_url: str) -> Optional[str]:
        """Decode Bing redirect URL"""
        try:
            import base64
            from urllib.parse import parse_qs, urlparse
            
            parsed = urlparse(redirect_url)
            params = parse_qs(parsed.query)
            
            if 'u' in params:
                encoded_url = params['u'][0]
                if encoded_url.startswith('a1'):
                    encoded_url = encoded_url[2:]
                
                decoded_bytes = base64.b64decode(encoded_url + '==')
                actual_url = decoded_bytes.decode('utf-8')
                
                if actual_url.startswith('http'):
                    return actual_url
            
            return None
            
        except Exception:
            return None
    
    async def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        """Scrape content from a specific URL"""
        if is_social_media_url(url):
            logger.warning(f"🚫 Blocked social media URL: {extract_domain(url)}")
            return None
        
        self.request_count += 1
        logger.info(f"📄 Scraping URL #{self.request_count}: {extract_domain(url)}")
        
        context = None
        page = None
        
        try:
            # Professional browser fingerprinting for URL scraping
            profile = user_agent_rotator.get_random_profile()
            logger.debug(f"🕵️  Using profile for URL scraping: {profile['user_agent'][:50]}...")
            
            # Create browser context with professional anti-detection
            context = await self.browser.new_context(
                user_agent=profile['user_agent'],
                viewport=profile['viewport'],
                locale='en-US',
                timezone_id=profile['timezone'],
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': ','.join(profile['languages']) + ';q=0.9,*;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-CH-UA': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                    'Sec-CH-UA-Mobile': '?0',
                    'Sec-CH-UA-Platform': f'"{profile["platform"]}"'
                }
            )
            
            page = await context.new_page()
            
            # Apply professional stealth measures
            await page.add_init_script(f"""
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => undefined,
                }});
                Object.defineProperty(navigator, 'platform', {{
                    get: () => '{profile["platform"]}',
                }});
                Object.defineProperty(navigator, 'languages', {{
                    get: () => {profile['languages']},
                }});
                window.chrome = {{
                    runtime: {{}},
                    loadTimes: function() {{}},
                    csi: function() {{}},
                    app: {{}}
                }};
            """)
            
            # Block unnecessary resources for faster loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
            await page.route("**/ads/**", lambda route: route.abort())
            await page.route("**/analytics/**", lambda route: route.abort())
            
            # Navigate to URL
            response = await page.goto(url, wait_until='domcontentloaded', timeout=self.navigation_timeout)
            
            if not response or response.status >= 400:
                logger.warning(f"⚠️ HTTP {response.status if response else 'No response'} for {url}")
                return None
            
            # Wait for content to load
            await page.wait_for_timeout(2000)
            
            # Get page title
            title = await page.title()
            
            # Get meta description
            try:
                meta_desc = await page.eval_on_selector('meta[name="description"]', 'el => el.content')
            except:
                meta_desc = ""
            
            # Extract content
            content = await self._extract_page_content(page)
            
            if content:
                scraped = ScrapedContent(
                    url=url,
                    title=title,
                    content=content,
                    meta_description=meta_desc,
                    word_count=sum(len(text.split()) for text in content)
                )
                
                logger.info(f"✅ Scraped {len(content)} paragraphs, {scraped.word_count} words from {extract_domain(url)}")
                return scraped
            else:
                logger.warning(f"⚠️ No content extracted from {extract_domain(url)}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Scraping failed for {url}: {e}")
            return None
            
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
    
    async def _extract_page_content(self, page: Page) -> List[str]:
        """Extract readable content from a page"""
        try:
            # Get page HTML
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
                element.decompose()
            
            content_blocks = []
            
            # Extract from common content selectors
            content_selectors = [
                'article',
                'main',
                '[role="main"]',
                '.content',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.article-body',
                'p'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 50:  # Only substantial content
                        clean_text = sanitize_text(text)
                        if clean_text and clean_text not in content_blocks:
                            content_blocks.append(clean_text)
            
            # If still no content, try broader extraction
            if not content_blocks:
                all_paragraphs = soup.find_all('p')
                for p in all_paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 50:
                        clean_text = sanitize_text(text)
                        if clean_text and clean_text not in content_blocks:
                            content_blocks.append(clean_text)
            
            return content_blocks[:25]  # Limit to 25 blocks
            
        except Exception as e:
            logger.error(f"❌ Content extraction failed: {e}")
            return []
