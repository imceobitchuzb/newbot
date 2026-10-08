"""Base interfaces and data structures for parameterized SAT question generation."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from backend.app.models.enums import Difficulty, QuestionType, Subject


@dataclass
class GeneratedOption:
    label: str  # 'A', 'B', 'C', 'D'
    text: str
    is_correct: bool


@dataclass
class GeneratedQuestionVariant:
    template_id: str
    variant_group: str
    subject: str
    domain: str
    skill: str
    subskill: Optional[str]
    difficulty: str
    question_type: str
    question_text: str
    explanation: str
    hint: Optional[str]
    sat_shortcut: Optional[str]
    options: List[GeneratedOption]
    estimated_time_seconds: int
    desmos_allowed: bool
    desmos_recommended: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)


class BaseQuestionTemplate(ABC):
    """Abstract interface for all SAT parameterized question templates."""

    @property
    @abstractmethod
    def template_id(self) -> str:
        """Unique template identifier, e.g. 'math_linear_eq_001'."""
        pass

    @property
    @abstractmethod
    def subject(self) -> str:
        pass

    @property
    @abstractmethod
    def domain(self) -> str:
        pass

    @property
    @abstractmethod
    def skill(self) -> str:
        pass

    @property
    @abstractmethod
    def default_difficulty(self) -> str:
        pass

    @abstractmethod
    def generate_variant(self, seed: Optional[int] = None) -> GeneratedQuestionVariant:
        """Generate a single concrete question variant with randomized parameters."""
        pass

    @abstractmethod
    def validate_variant(self, variant: GeneratedQuestionVariant) -> ValidationResult:
        """Mathematically verify variant correctness, uniqueness of options, and formatting."""
        pass
