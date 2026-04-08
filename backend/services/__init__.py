"""Services module for the application."""

from .course_data_service import CourseDataService, course_service
from .transcript_parser import TranscriptParser, parse_transcript
from .gap_calculator import GapCalculator, calculate_gaps
from .cache_service import CacheService, get_cache_service
from .prerequisite_graph import PrerequisiteGraph, load_prerequisite_graph
from .recommendation import RecommendationEngine, get_recommendation_engine

__all__ = [
    # Course data
    'CourseDataService',
    'course_service',
    # Transcript parsing
    'TranscriptParser',
    'parse_transcript',
    # Gap calculation
    'GapCalculator',
    'calculate_gaps',
    # Cache
    'CacheService',
    'get_cache_service',
    # Prerequisite graph
    'PrerequisiteGraph',
    'load_prerequisite_graph',
    # Recommendation
    'RecommendationEngine',
    'get_recommendation_engine',
]
