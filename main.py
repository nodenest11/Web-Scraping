from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import time
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import uuid
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import (
    SearchRequest,
    ScrapeRequest,
    SerpApiResponse,
    SearchMetadata,
    SearchParameters,
    OrganicResult,
    RelatedQuestion,
    KnowledgeGraph,
    ScrapedContent,
    ErrorResponse,
    HealthResponse
)
from scraper import UniversalScraper
from enhanced_scraper import EnhancedUndetectedScraper
from utils import setup_logging, get_client_ip

# Setup logging
logger = setup_logging()

# Global scraper instance with enhanced metrics
scraper = None

# Configuration: Choose scraper type
# Set to True to use undetected Chrome (better for avoiding CAPTCHAs)
# Set to False to use original Playwright scraper
USE_UNDETECTED_CHROME = os.getenv('USE_UNDETECTED_CHROME', 'true').lower() == 'true'
request_counter = 0

# Ultra-robust performance tracking
start_time = datetime.now()
error_count = 0
success_count = 0
performance_metrics = {
    "total_requests": 0,
    "search_requests": 0,
    "scrape_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "average_response_time": 0.0,
    "uptime_start": datetime.now(),
    "browser_restarts": 0,
    "errors_last_hour": 0,
    "last_error_time": None
}

def log_request_analytics(endpoint: str, duration: float, result_count: int):
    """Enhanced analytics logging with performance tracking"""
    performance_metrics["total_requests"] += 1
    
    if endpoint == "search":
        performance_metrics["search_requests"] += 1
    elif endpoint == "scrape":
        performance_metrics["scrape_requests"] += 1
    
    # Update rolling average response time
    current_avg = performance_metrics["average_response_time"]
    total_requests = performance_metrics["total_requests"]
    performance_metrics["average_response_time"] = (
        (current_avg * (total_requests - 1) + duration) / total_requests
    )
    
    logger.info(f"📊 Analytics: {endpoint} - {duration:.3f}s - {result_count} results - Avg: {performance_metrics['average_response_time']:.3f}s")

def log_error_metrics():
    """Track errors for comprehensive monitoring"""
    performance_metrics["failed_requests"] += 1
    performance_metrics["errors_last_hour"] += 1
    performance_metrics["last_error_time"] = datetime.now().isoformat()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ultra-robust application lifespan manager with comprehensive health checks"""
    global scraper
    
    # Enhanced startup sequence
    logger.info("🚀 Starting Ultra-Robust Universal Web Scraping API...")
    
    if USE_UNDETECTED_CHROME:
        logger.info("🔍 Initializing Enhanced Undetected Chrome engine for maximum CAPTCHA avoidance...")
        scraper = EnhancedUndetectedScraper()
    else:
        logger.info("🔍 Initializing browser engine for 100% reliability...")
        scraper = UniversalScraper()
    
    try:
        await scraper.initialize()
        
        # Browser health verification
        logger.info("🧪 Running startup health checks...")
        if USE_UNDETECTED_CHROME:
            # For undetected Chrome, just check if browser is ready
            if await scraper.is_browser_ready():
                logger.info("✅ Enhanced Undetected Chrome engine verified and operational")
            else:
                logger.warning("⚠️ Enhanced browser not ready - may affect performance")
        else:
            # Original test for Playwright
            test_search = await scraper.search_comprehensive("test startup", "bing", 1)
            if test_search[0]:  # organic_results
                logger.info("✅ Browser engine verified and operational")
            else:
                logger.warning("⚠️ Browser test returned no results - may affect performance")
        
        performance_metrics["uptime_start"] = datetime.now()
        scraper_type = "Enhanced Undetected Chrome" if USE_UNDETECTED_CHROME else "Playwright"
        logger.info(f"🎯 Ultra-Robust Web Scraping API ({scraper_type}) is fully operational and ready!")
        logger.info("📊 Performance monitoring active - tracking all metrics")
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: Failed to start scraper: {e}")
        logger.error("🚨 API startup failed - manual intervention required")
        raise
    
    yield
    
    # Enhanced shutdown sequence
    logger.info("🛑 Initiating graceful shutdown of Ultra-Robust Web Scraping API...")
    try:
        if scraper:
            await scraper.cleanup()
            logger.info("✅ Browser cleanup completed successfully")
        
        # Log final performance metrics
        uptime = datetime.now() - performance_metrics["uptime_start"]
        logger.info(f"📊 Final Stats: {performance_metrics['total_requests']} requests processed in {uptime}")
        logger.info(f"🎯 Success Rate: {performance_metrics['successful_requests']}/{performance_metrics['total_requests']}")
        logger.info("✅ Ultra-Robust Web Scraping API shutdown completed")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
        logger.error("⚠️ Cleanup may be incomplete")


# Initialize FastAPI app
app = FastAPI(
    title="Universal Web Scraping API",
    description="A high-performance web scraping API that mimics SERP API responses",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "search",
            "description": "Search operations returning SERP-like results",
        },
        {
            "name": "scrape",
            "description": "Content scraping operations",
        },
        {
            "name": "health",
            "description": "Health and monitoring endpoints",
        },
    ]
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ultra_robust_middleware(request: Request, call_next):
    """Ultra-robust request middleware with comprehensive analytics and error tracking"""
    start_time = time.time()
    client_ip = get_client_ip(request)
    request_id = str(uuid.uuid4())[:13]
    
    logger.info(f"📥 [{request_id}] {request.method} {request.url.path} from {client_ip}")
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Track success/failure metrics
        if response.status_code < 400:
            performance_metrics["successful_requests"] += 1
            logger.info(f"✅ [{request_id}] {request.method} {request.url.path} completed in {duration:.3f}s - Status: {response.status_code}")
        else:
            log_error_metrics()
            logger.warning(f"⚠️ [{request_id}] {request.method} {request.url.path} failed in {duration:.3f}s - Status: {response.status_code}")
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        response.headers["X-Request-ID"] = request_id
        response.headers["X-API-Version"] = "2.0.0"
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_metrics()
        logger.error(f"❌ [{request_id}] {request.method} {request.url.path} crashed in {duration:.3f}s - Error: {e}")
        
        # Return structured error response
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "middleware_error",
                    "message": "Internal server error occurred",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )


@app.get("/", response_model=HealthResponse, tags=["health"])
async def root():
    """Root endpoint - health check"""
    return HealthResponse(status="ok", version="2.0.0")


@app.get("/health", tags=["health"])
async def health_check():
    """Ultra-comprehensive health check endpoint for 100% robustness"""
    try:
        browser_ready = await scraper.is_browser_ready() if scraper else False
        uptime = datetime.now() - performance_metrics["uptime_start"]
        uptime_seconds = uptime.total_seconds()
        
        # Memory usage check for system health
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
        except:
            memory_mb = 0
        
        health_status = {
            "status": "healthy" if browser_ready else "degraded",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "engine": "Enhanced Undetected Chrome" if USE_UNDETECTED_CHROME else "Playwright",
            "anti_detection": "Maximum" if USE_UNDETECTED_CHROME else "Standard",
            "uptime": {
                "seconds": round(uptime_seconds, 2),
                "human_readable": str(uptime)
            },
            "services": {
                "browser": "ready" if browser_ready else "not_ready",
                "requests_processed": scraper.request_count if scraper else 0
            },
            "performance": {
                "total_requests": performance_metrics["total_requests"],
                "success_rate": round(
                    (performance_metrics["successful_requests"] / max(1, performance_metrics["total_requests"])) * 100, 2
                ) if performance_metrics["total_requests"] > 0 else 100.0,
                "average_response_time_ms": round(performance_metrics["average_response_time"] * 1000, 2),
                "requests_per_minute": round(performance_metrics["total_requests"] / (uptime_seconds / 60), 2) if uptime_seconds > 60 else 0
            },
            "system": {
                "memory_usage_mb": round(memory_mb, 2),
                "browser_restarts": performance_metrics["browser_restarts"],
                "errors_last_hour": performance_metrics["errors_last_hour"]
            },
            "environment": os.getenv('ENVIRONMENT', 'development')
        }
        
        return health_status
        
    except Exception as e:
        log_error_metrics()
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "version": "2.0.0",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/metrics", tags=["health"])
async def get_detailed_metrics():
    """Get comprehensive performance and operational metrics"""
    uptime = datetime.now() - performance_metrics["uptime_start"]
    
    return {
        "api_metrics": performance_metrics.copy(),
        "uptime": {
            "started": performance_metrics["uptime_start"].isoformat(),
            "total_seconds": uptime.total_seconds(),
            "human_readable": str(uptime)
        },
        "request_breakdown": {
            "search_percentage": round((performance_metrics["search_requests"] / max(1, performance_metrics["total_requests"])) * 100, 2),
            "scrape_percentage": round((performance_metrics["scrape_requests"] / max(1, performance_metrics["total_requests"])) * 100, 2)
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/browser/restart", tags=["health"])
async def restart_browser():
    """Force restart browser for maintenance - ultra-robust recovery"""
    try:
        if scraper:
            await scraper.restart_browser()
            performance_metrics["browser_restarts"] += 1
            logger.info("🔄 Browser manually restarted for optimal performance")
            return {"status": "success", "message": "Browser restarted successfully", "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(status_code=503, detail="Scraper not initialized")
    except Exception as e:
        log_error_metrics()
        logger.error(f"Browser restart failed: {e}")
        raise HTTPException(status_code=500, detail=f"Browser restart failed: {e}")


@app.post("/search", response_model=SerpApiResponse, tags=["search"])
async def search_serp(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    High-performance search endpoint that returns SERP-like results.
    
    This endpoint is optimized to compete with SerpAPI and similar services,
    providing fast, reliable search results with comprehensive metadata.
    """
    global request_counter, success_count, error_count
    request_counter += 1
    start_time = time.time()
    request_id = str(uuid.uuid4())[:13]
    
    try:
        logger.info(f"🔍 [{request_id}] Search request: '{request.q}' (engine: {request.engine}, num: {request.num})")
        
        # Input validation and sanitization
        if not request.q or len(request.q.strip()) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
        
        if request.num > 20:
            request.num = 20
        elif request.num < 1:
            request.num = 1
        
        # Enhanced browser health check before processing
        if not await scraper.is_browser_ready():
            logger.warning(f"[{request_id}] Browser not ready, reinitializing...")
            await scraper.cleanup()
            await scraper.initialize()
        
        # Get search results with timeout protection
        try:
            organic_results, related_questions, knowledge_graph = await asyncio.wait_for(
                scraper.search_comprehensive(
                    query=request.q,
                    engine=request.engine,
                    num_results=request.num
                ),
                timeout=30.0  # 30-second timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"[{request_id}] Search timeout after 30 seconds")
            raise HTTPException(status_code=504, detail="Search request timed out")
        
        # Calculate processing time
        total_time = time.time() - start_time
        
        # Build robust response
        search_metadata = SearchMetadata(
            id=request_id,
            status="Success",
            total_time_taken=round(total_time, 3),
            engine_url=scraper.get_last_search_url()
        )
        
        search_parameters = SearchParameters(
            q=request.q,
            engine=request.engine,
            num=request.num,
            country=request.country,
            location=request.location
        )
        
        response = SerpApiResponse(
            search_metadata=search_metadata,
            search_parameters=search_parameters,
            organic_results=organic_results,
            related_questions=related_questions,
            knowledge_graph=knowledge_graph
        )
        
        success_count += 1
        logger.info(f"✅ [{request_id}] Search completed: {len(organic_results)} results in {total_time:.3f}s")
        
        # Background task for analytics
        background_tasks.add_task(log_request_analytics, "search", total_time, len(organic_results))
        
        return response
        
    except HTTPException:
        error_count += 1
        raise
    except Exception as e:
        error_count += 1
        logger.error(f"❌ [{request_id}] Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "type": "search_error",
                    "message": "Internal search error occurred",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )


@app.post("/scrape", response_model=SerpApiResponse, tags=["scrape"])
async def scrape_content(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Ultra-robust scraping endpoint that rivals FireCrawl and similar services.
    
    Features:
    - Smart content extraction with multiple fallback strategies
    - Robust error handling and retry mechanisms
    - Performance optimization with resource blocking
    - Anti-detection measures
    """
    global request_counter, success_count, error_count
    request_counter += 1
    start_time = time.time()
    request_id = str(uuid.uuid4())[:13]
    
    try:
        if request.url:
            logger.info(f"🎯 [{request_id}] Direct URL scraping: {request.url}")
            
            # Enhanced URL validation
            url_str = str(request.url)
            if not url_str.startswith(('http://', 'https://')):
                raise HTTPException(status_code=400, detail="Invalid URL format")
            
            # Smart content extraction with retries
            scraped_content = None
            for attempt in range(3):
                try:
                    scraped_content = await asyncio.wait_for(
                        scraper.scrape_url(url_str), 
                        timeout=45.0
                    )
                    if scraped_content:
                        break
                    await asyncio.sleep(1)  # Brief pause between retries
                except asyncio.TimeoutError:
                    if attempt == 2:  # Last attempt
                        logger.error(f"[{request_id}] Scraping timeout after 45 seconds")
                        raise HTTPException(status_code=504, detail="Scraping request timed out")
                    continue
            
            if not scraped_content:
                raise HTTPException(status_code=422, detail="Could not extract content from URL")
            
            # Build minimal SERP response with scraped content
            search_metadata = SearchMetadata(
                id=request_id,
                status="Success",
                total_time_taken=round(time.time() - start_time, 3)
            )
            
            search_parameters = SearchParameters(
                q=request.q or "Direct URL scraping",
                engine=request.engine
            )
            
            response = SerpApiResponse(
                search_metadata=search_metadata,
                search_parameters=search_parameters,
                organic_results=[],
                scraped_content=scraped_content.dict() if scraped_content else None
            )
            
        elif request.q:
            logger.info(f"🔍 [{request_id}] Search and scrape: '{request.q}'")
            
            # Input validation
            if len(request.q.strip()) < 2:
                raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
            
            # Get search results with timeout
            organic_results, related_questions, knowledge_graph = await asyncio.wait_for(
                scraper.search_comprehensive(
                    query=request.q,
                    engine=request.engine,
                    num_results=request.num
                ),
                timeout=30.0
            )
            
            # Enhanced content scraping from first result
            scraped_content = None
            if request.scrape_content and organic_results:
                first_url = organic_results[0].link
                logger.info(f"📄 [{request_id}] Scraping first result: {first_url}")
                
                try:
                    scraped_content = await asyncio.wait_for(
                        scraper.scrape_url(first_url),
                        timeout=45.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"[{request_id}] Content scraping timed out, returning search results only")
                except Exception as e:
                    logger.warning(f"[{request_id}] Content scraping failed: {e}")
            
            # Build comprehensive response
            search_metadata = SearchMetadata(
                id=request_id,
                status="Success",
                total_time_taken=round(time.time() - start_time, 3),
                engine_url=scraper.get_last_search_url()
            )
            
            search_parameters = SearchParameters(
                q=request.q,
                engine=request.engine,
                num=request.num
            )
            
            response = SerpApiResponse(
                search_metadata=search_metadata,
                search_parameters=search_parameters,
                organic_results=organic_results,
                related_questions=related_questions,
                knowledge_graph=knowledge_graph,
                scraped_content=scraped_content.dict() if scraped_content else None
            )
            
        else:
            raise HTTPException(
                status_code=400, 
                detail="Either 'q' (query) or 'url' must be provided"
            )
        
        success_count += 1
        total_time = time.time() - start_time
        logger.info(f"✅ [{request_id}] Scrape completed in {total_time:.3f}s")
        
        # Background analytics
        background_tasks.add_task(
            log_request_analytics, 
            "scrape", 
            total_time, 
            len(response.organic_results) + (1 if response.scraped_content else 0)
        )
        
        return response
        
    except HTTPException:
        error_count += 1
        log_error_metrics()
        raise
    except asyncio.TimeoutError:
        error_count += 1
        log_error_metrics()
        logger.error(f"[{request_id}] Request timeout")
        raise HTTPException(status_code=504, detail="Request timed out")
    except Exception as e:
        error_count += 1
        log_error_metrics()
        logger.error(f"❌ [{request_id}] Scraping failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "type": "scrape_error",
                    "message": "Internal scraping error occurred",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )


@app.get("/status", tags=["health"])
async def get_status():
    """Get detailed API status and statistics"""
    if not scraper:
        return {"status": "initializing"}
    
    return {
        "status": "operational",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_requests": scraper.request_count,
            "browser_ready": await scraper.is_browser_ready(),
            "uptime_seconds": scraper.get_uptime()
        },
        "capabilities": {
            "search_engines": ["google", "bing"],
            "max_results": 20,
            "content_scraping": True,
            "proxy_rotation": scraper.proxy_enabled,
            "user_agent_rotation": True
        }
    }


@app.get("/api/info", tags=["info"])
async def get_api_info():
    """Get comprehensive API information and capabilities"""
    return {
        "api": {
            "name": "Universal Web Scraping API",
            "version": "2.0.0",
            "description": "High-performance web scraping API that mimics SERP API responses",
            "documentation_url": "/docs",
            "redoc_url": "/redoc"
        },
        "endpoints": {
            "search": {
                "path": "/search",
                "method": "POST",
                "description": "Get SERP-style search results",
                "supported_engines": ["google", "bing"],
                "max_results": 20
            },
            "scrape": {
                "path": "/scrape",
                "method": "POST", 
                "description": "Scrape content from URLs or search results",
                "modes": ["direct_url", "search_and_scrape"]
            },
            "health": {
                "paths": ["/health", "/status", "/metrics"],
                "description": "Health checks and performance metrics"
            }
        },
        "features": {
            "serp_compatible": True,
            "anti_detection": True,
            "async_processing": True,
            "docker_ready": True,
            "production_ready": True
        },
        "limits": {
            "query_min_length": 2,
            "max_results_per_request": 20,
            "request_timeout_seconds": 30,
            "scraping_timeout_seconds": 45
        }
    }


@app.get("/api/engines", tags=["info"])
async def get_supported_engines():
    """Get list of supported search engines with their capabilities"""
    return {
        "supported_engines": [
            {
                "name": "google",
                "display_name": "Google",
                "description": "Google Search with comprehensive results",
                "features": ["organic_results", "related_questions", "knowledge_graph"],
                "countries_supported": ["us", "uk", "ca", "au", "de", "fr", "es", "it"],
                "default": True
            },
            {
                "name": "bing", 
                "display_name": "Bing",
                "description": "Microsoft Bing Search",
                "features": ["organic_results", "related_questions"],
                "countries_supported": ["us", "uk", "ca", "au", "de", "fr", "es", "it"],
                "default": False
            }
        ],
        "default_engine": "google",
        "engine_rotation": False,
        "proxy_support": True
    }


@app.post("/api/validate", tags=["utility"])
async def validate_request(request: SearchRequest):
    """Validate a search request without executing it"""
    try:
        # Validate query length
        if not request.q or len(request.q.strip()) < 2:
            return {
                "valid": False,
                "errors": ["Query must be at least 2 characters long"]
            }
        
        # Validate number of results
        if request.num > 20 or request.num < 1:
            return {
                "valid": False,
                "errors": ["Number of results must be between 1 and 20"]
            }
        
        # Validate engine
        if request.engine not in ["google", "bing"]:
            return {
                "valid": False,
                "errors": ["Engine must be 'google' or 'bing'"]
            }
        
        return {
            "valid": True,
            "message": "Request is valid",
            "estimated_time": "2-5 seconds",
            "will_return": {
                "organic_results": f"Up to {request.num} results",
                "related_questions": "0-5 questions",
                "knowledge_graph": "Possibly included"
            }
        }
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"]
        }


@app.post("/api/bulk-search", tags=["search"])
async def bulk_search(queries: List[str], engine: str = "google", num: int = 10):
    """
    Perform bulk search operations for multiple queries.
    Limited to 5 queries per request to prevent abuse.
    """
    if len(queries) > 5:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 5 queries allowed per bulk request"
        )
    
    if len(queries) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one query must be provided"
        )
    
    request_id = str(uuid.uuid4())[:13]
    start_time = time.time()
    
    try:
        logger.info(f"🔍 [{request_id}] Bulk search: {len(queries)} queries")
        
        results = []
        for i, query in enumerate(queries):
            try:
                # Create individual search request
                search_req = SearchRequest(q=query, engine=engine, num=num)
                
                # Get search results
                organic_results, related_questions, knowledge_graph = await scraper.search_comprehensive(
                    query=query,
                    engine=engine,
                    num_results=num
                )
                
                # Build response for this query
                search_metadata = SearchMetadata(
                    id=f"{request_id}-{i+1}",
                    status="Success",
                    total_time_taken=time.time() - start_time
                )
                
                query_result = {
                    "query": query,
                    "search_metadata": search_metadata.dict(),
                    "organic_results": [result.dict() for result in organic_results],
                    "related_questions": [q.dict() for q in related_questions],
                    "knowledge_graph": knowledge_graph.dict() if knowledge_graph else None
                }
                
                results.append(query_result)
                
                # Small delay between queries
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"[{request_id}] Query '{query}' failed: {e}")
                error_result = {
                    "query": query,
                    "error": {
                        "type": "query_error",
                        "message": str(e)
                    }
                }
                results.append(error_result)
        
        total_time = time.time() - start_time
        logger.info(f"✅ [{request_id}] Bulk search completed in {total_time:.3f}s")
        
        return {
            "bulk_search_metadata": {
                "id": request_id,
                "status": "Success",
                "total_queries": len(queries),
                "successful_queries": len([r for r in results if "error" not in r]),
                "failed_queries": len([r for r in results if "error" in r]),
                "total_time_taken": round(total_time, 3),
                "processed_at": datetime.now().isoformat()
            },
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ [{request_id}] Bulk search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "type": "bulk_search_error",
                    "message": "Bulk search operation failed",
                    "request_id": request_id
                }
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"💥 Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.now().isoformat()
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Environment-based configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    workers = int(os.getenv('WORKERS', '1'))
    is_development = os.getenv('ENVIRONMENT', 'development') == 'development'
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=is_development,
        workers=workers if not is_development else 1,
        access_log=True
    )
