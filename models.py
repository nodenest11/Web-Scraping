from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class SearchRequest(BaseModel):
    """Request model for search API"""
    q: str = Field(..., description="Search query")
    engine: str = Field("google", description="Search engine (google, bing)")
    num: int = Field(10, description="Number of results (1-20)")
    country: str = Field("us", description="Country code for search")
    location: str = Field("United States", description="Location for search")


class ScrapeRequest(BaseModel):
    """Request model for scraping API"""
    q: Optional[str] = Field(None, description="Search query")
    url: Optional[HttpUrl] = Field(None, description="Direct URL to scrape")
    engine: str = Field("google", description="Search engine")
    num: int = Field(10, description="Number of search results")
    scrape_content: bool = Field(False, description="Whether to scrape content")


class SearchMetadata(BaseModel):
    """Search metadata for SERP-like response"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:13])
    status: str = Field("Success")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    processed_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    total_time_taken: float = Field(0.0)
    engine_url: Optional[str] = None


class SearchParameters(BaseModel):
    """Search parameters for SERP-like response"""
    q: str
    engine: str
    num: int = 10
    country: str = "us"
    location: str = "United States"


class OrganicResult(BaseModel):
    """Individual organic search result"""
    position: int
    title: str
    link: str
    snippet: str
    displayed_link: Optional[str] = None
    cached_page_link: Optional[str] = None
    source: Optional[str] = None
    rich_snippet: Optional[Dict[str, Any]] = None


class RelatedQuestion(BaseModel):
    """Related question from PAA (People Also Ask)"""
    question: str
    snippet: Optional[str] = None
    title: Optional[str] = None
    link: Optional[str] = None


class KnowledgeGraph(BaseModel):
    """Knowledge graph information"""
    title: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    source: Optional[Dict[str, str]] = None
    thumbnail: Optional[str] = None


class SerpApiResponse(BaseModel):
    """Main SERP API response model"""
    search_metadata: SearchMetadata
    search_parameters: SearchParameters
    organic_results: List[OrganicResult] = []
    related_questions: List[RelatedQuestion] = []
    knowledge_graph: Optional[KnowledgeGraph] = None
    scraped_content: Optional[Dict[str, Any]] = None


class ScrapedContent(BaseModel):
    """Scraped content from a URL"""
    url: str
    title: str
    content: List[str]
    meta_description: Optional[str] = None
    word_count: int = 0
    extracted_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    """Error response model"""
    error: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
