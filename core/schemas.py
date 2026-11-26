"""Data models and request/response schemas for Text Intelligence Engine."""

from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator


class EditingMode(str, Enum):
    """Supported editing modes."""
    PROOFREAD = "proofread"
    CLARITY = "clarity"
    NATURAL = "natural"          # Natural / Fluent
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    CONVERSATIONAL = "conversational"
    CONCISE = "concise"
    SIMPLIFY = "simplify"
    CUSTOM = "custom"
    LEGACY = "legacy"            # Safe legacy deterministic mode for backwards compatibility


class EditingIntensity(str, Enum):
    """Editing intensity level (depth/scope of revisions, not detector evasion strength)."""
    LIGHT = "light"
    BALANCED = "balanced"
    SUBSTANTIAL = "substantial"


class ProtectedSpan(BaseModel):
    """Represents a factual element, entity, or formatting span that should be preserved."""
    text: str
    span_type: str  # e.g., "number", "name", "date", "citation", "url", "code", "term"
    start: int
    end: int


class DetectorSegment(BaseModel):
    """Sentence-level detector signal for review, never proof of authorship."""
    text: str
    start: int
    end: int
    flagged: bool = False
    signal_score: int = 0
    reasons: List[str] = Field(default_factory=list)


class StyleProfile(BaseModel):
    """User-defined style profile (opt-in and editable)."""
    name: str = "Default"
    preferred_tone: Optional[str] = None
    target_audience: Optional[str] = None
    forbidden_words: List[str] = Field(default_factory=list)
    custom_guidelines: Optional[str] = None


class TokenUsage(BaseModel):
    """Estimated token counts and cost."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class TextMetrics(BaseModel):
    """Descriptive structural and readability metrics for a text."""
    char_count: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    avg_sentence_length: float
    avg_word_length: float
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    lexical_diversity: float
    reading_time_minutes: float
    detected_language: str = "en"
    metric_notice: str = (
        "Descriptive writing metrics. These do not measure or estimate AI authorship or detection probability."
    )


class ChangeSummary(BaseModel):
    """Summary of modifications made during editing."""
    added_words: int = 0
    removed_words: int = 0
    net_word_change: int = 0
    key_modifications: List[str] = Field(default_factory=list)


class RewriteRequest(BaseModel):
    """Incoming request to rewrite text."""
    text: str
    mode: EditingMode = EditingMode.PROOFREAD
    intensity: EditingIntensity = EditingIntensity.BALANCED
    tone: Optional[str] = None
    audience: Optional[str] = None
    instructions: Optional[str] = None
    preserve_formatting: bool = True
    include_change_summary: bool = True
    fallback_to_local: bool = True

    # Phase 6 additions: Selection-based editing & style profile
    selection_range: Optional[Tuple[int, int]] = None
    selected_text: Optional[str] = None
    style_profile: Optional[StyleProfile] = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Input text must not be empty or whitespace-only.")
        return v

    @model_validator(mode="after")
    def validate_selection(self) -> "RewriteRequest":
        """Reject stale or malformed selection metadata instead of silently clamping it."""
        if self.selection_range is None:
            if self.selected_text is not None:
                raise ValueError("selected_text requires selection_range.")
            return self

        start, end = self.selection_range
        if start < 0 or end <= start or end > len(self.text):
            raise ValueError("selection_range must be within text and have end greater than start.")
        selected = self.text[start:end]
        if self.selected_text is not None and self.selected_text != selected:
            raise ValueError("selected_text does not match selection_range.")
        return self


class AnalysisRequest(BaseModel):
    """Incoming request to analyze text metrics and protected spans without rewriting."""
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Input text must not be empty or whitespace-only.")
        return v


class AnalysisResponse(BaseModel):
    """Response containing metrics, protected entities, and transparent detector signals."""
    metrics: TextMetrics
    protected_spans: List[ProtectedSpan]
    paragraphs: int
    sentences: int
    detected_language: str = "en"
    ai_likelihood_percent: int = Field(default=0, ge=0, le=100)
    detector_status: str = "ready"
    detector_method: str = "conservative linguistic-signal estimate"
    detector_segments: List[DetectorSegment] = Field(default_factory=list)
    detector_notice: str = (
        "This is a probabilistic writing signal, not proof of AI authorship. "
        "Use longer text and human review; formulaic writing can be flagged."
    )


class RewriteResponse(BaseModel):
    """Outgoing response for a completed text rewrite."""
    original_text: str
    revised_text: str
    mode: str
    intensity: str
    provider: str
    model: str
    is_fallback: bool = False
    warnings: List[str] = Field(default_factory=list)
    change_summary: Optional[ChangeSummary] = None
    metrics: Optional[TextMetrics] = None
    token_usage: Optional[TokenUsage] = None
    selection_applied: bool = False
    request_id: str
    duration_ms: float = 0.0
