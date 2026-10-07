from enum import Enum


class Subject(str, Enum):
    MATH = "MATH"
    READING_WRITING = "READING_WRITING"


class MathDomain(str, Enum):
    ALGEBRA = "ALGEBRA"
    ADVANCED_MATH = "ADVANCED_MATH"
    PROBLEM_SOLVING_DATA_ANALYSIS = "PROBLEM_SOLVING_DATA_ANALYSIS"
    GEOMETRY_TRIGONOMETRY = "GEOMETRY_TRIGONOMETRY"


class ReadingWritingDomain(str, Enum):
    INFORMATION_IDEAS = "INFORMATION_IDEAS"
    CRAFT_STRUCTURE = "CRAFT_STRUCTURE"
    EXPRESSION_IDEAS = "EXPRESSION_IDEAS"
    STANDARD_ENGLISH_CONVENTIONS = "STANDARD_ENGLISH_CONVENTIONS"


class Difficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    SPR = "SPR"  # Student-Produced Response (Grid-in)


class QuestionStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class DiagnosticStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class DiagnosticModuleStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class DomainClassification(str, Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class MathPracticeSessionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class SkillMasteryLevel(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    LEARNING = "LEARNING"
    PRACTICING = "PRACTICING"
    STRONG = "STRONG"


