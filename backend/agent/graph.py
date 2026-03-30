"""LangGraph state machine for graduation schema gap analysis."""

from typing import Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from backend.agent.tools import extract_transcript_from_pdf, load_graduation_schema


class GapAnalysisState(TypedDict, total=False):
    """State for the gap analysis workflow."""
    year: str
    class_name: str
    transcript_md: Optional[str]
    schema_md: Optional[str]
    result: Optional[str]
    error: Optional[str]


def extract_transcript_node(state: GapAnalysisState) -> Command:
    """Node: Extract transcript from PDF using OCR."""
    # Transcript is already extracted before the graph runs
    # This node just validates it exists
    if not state.get("transcript_md"):
        return Command(update={"error": "Transcript markdown not provided"})
    return Command(update={})


def load_schema_node(state: GapAnalysisState) -> Command:
    """Node: Load graduation schema based on year and class."""
    year = state.get("year")
    class_name = state.get("class_name")

    if not year or not class_name:
        return Command(update={"error": "Missing year or class_name in state"})

    try:
        schema_md = load_graduation_schema(year, class_name)
        return Command(update={"schema_md": schema_md})
    except Exception as e:
        return Command(update={"error": f"Failed to load schema: {str(e)}"})


def analyze_gap_node(state: GapAnalysisState) -> Command:
    """Node: Analyze gaps between schema requirements and transcript using LLM."""
    from backend.services.llm_service import LLMService, LLMServiceError

    schema_md = state.get("schema_md")
    transcript_md = state.get("transcript_md")
    year = state.get("year", "")
    class_name = state.get("class_name", "")

    if not schema_md:
        return Command(update={"error": "Schema not loaded"})
    if not transcript_md:
        return Command(update={"error": "Transcript not provided"})

    try:
        # 调用 LLM 进行分析
        llm = LLMService()
        result = llm.analyze_gap(
            schema=schema_md,
            transcript=transcript_md,
            year=year,
            class_name=class_name,
        )
        return Command(update={"result": result})
    except LLMServiceError as e:
        return Command(update={"error": f"LLM analysis failed: {str(e)}"})
    except Exception as e:
        return Command(update={"error": f"Analysis failed: {str(e)}"})


def build_gap_analysis_graph() -> StateGraph:
    """Build and return the gap analysis workflow graph."""
    builder = StateGraph(GapAnalysisState)

    builder.add_node("extract_transcript", extract_transcript_node)
    builder.add_node("load_schema", load_schema_node)
    builder.add_node("analyze_gap", analyze_gap_node)

    builder.add_edge(START, "extract_transcript")
    builder.add_edge("extract_transcript", "load_schema")
    builder.add_edge("load_schema", "analyze_gap")
    builder.add_edge("analyze_gap", END)

    return builder.compile()


_gap_analysis_graph = None


def get_graph() -> StateGraph:
    """Get or create the compiled gap analysis graph."""
    global _gap_analysis_graph
    if _gap_analysis_graph is None:
        _gap_analysis_graph = build_gap_analysis_graph()
    return _gap_analysis_graph
