"""Canonical SAT Math Taxonomy and Skills definition.

Provides centralized domain structure, canonical skills per domain,
descriptions, alias normalizations, and validator utilities.
"""
from typing import Dict, List, Optional
from backend.app.models.enums import MathDomain, SkillMasteryLevel

CANONICAL_MATH_DOMAINS: Dict[str, Dict] = {
    MathDomain.ALGEBRA.value: {
        "domain": MathDomain.ALGEBRA.value,
        "title": "Algebra",
        "description": "Linear equations, systems, linear inequalities, and functions that form the foundation of Digital SAT Math.",
        "skills": [
            "Linear equations in one variable",
            "Linear equations in two variables",
            "Linear functions",
            "Systems of linear equations",
            "Linear inequalities",
            "Slope and intercept",
            "Word problems with linear relationships",
        ],
    },
    MathDomain.ADVANCED_MATH.value: {
        "domain": MathDomain.ADVANCED_MATH.value,
        "title": "Advanced Math",
        "description": "Quadratic, exponential, polynomial, and nonlinear expressions and systems essential for reaching 700+ Math scores.",
        "skills": [
            "Quadratic equations",
            "Quadratic functions",
            "Polynomial expressions",
            "Exponential functions",
            "Equivalent expressions",
            "Nonlinear equations",
            "Nonlinear systems",
        ],
    },
    MathDomain.PROBLEM_SOLVING_DATA_ANALYSIS.value: {
        "domain": MathDomain.PROBLEM_SOLVING_DATA_ANALYSIS.value,
        "title": "Problem-Solving and Data Analysis",
        "description": "Ratios, percentages, rates, unit conversions, statistics, probability, and interpreting graphs and tables.",
        "skills": [
            "Ratios and proportions",
            "Percentages",
            "Rates and units",
            "Tables and graphs",
            "Scatterplots",
            "Statistics",
            "Probability",
            "Data interpretation",
        ],
    },
    MathDomain.GEOMETRY_TRIGONOMETRY.value: {
        "domain": MathDomain.GEOMETRY_TRIGONOMETRY.value,
        "title": "Geometry and Trigonometry",
        "description": "Lines, angles, triangles, circles, area/volume, right-triangle trigonometry, and radians.",
        "skills": [
            "Lines and angles",
            "Triangles",
            "Similarity",
            "Area and volume",
            "Circles",
            "Right triangles",
            "Trigonometry",
        ],
    },
}

# Alias mappings for canonical skill resolution
SKILL_ALIASES: Dict[str, str] = {
    # Algebra
    "systems of two linear equations": "Systems of linear equations",
    "systems with infinite or no solutions": "Systems of linear equations",
    "linear functions and slope-intercept form": "Slope and intercept",
    "linear functions and modeling": "Linear functions",
    "linear inequalities in one or two variables": "Linear inequalities",
    "linear expressions & modeling": "Word problems with linear relationships",
    # Advanced Math
    "quadratic equations & factoring": "Quadratic equations",
    "quadratic equations in one variable": "Quadratic equations",
    "parabolas & vertex form": "Quadratic functions",
    "quadratic discriminant & roots": "Quadratic equations",
    "exponential growth & decay": "Exponential functions",
    "polynomial factors and division": "Polynomial expressions",
    "radicals and rational exponents": "Equivalent expressions",
    # Problem Solving
    "percentages & successive discounts": "Percentages",
    "rates, units, and unit conversions": "Rates and units",
    "two-way tables and conditional probability": "Probability",
    "one-variable statistics": "Statistics",
    "sample surveys and margin of error": "Statistics",
    "data distributions and standard deviation": "Statistics",
    "linear and exponential scatterplots": "Scatterplots",
    # Geometry & Trig
    "circle equations in the coordinate plane": "Circles",
    "lines, angles, and triangles": "Lines and angles",
    "right triangles and trigonometry": "Right triangles",
    "trigonometric ratios and radians": "Trigonometry",
    "area and volume formulas": "Area and volume",
    "congruence and similarity": "Similarity",
}


def normalize_skill(skill: str) -> str:
    """Normalize any skill string to its canonical title if an alias exists."""
    if not skill:
        return ""
    clean = skill.strip()
    clean_lower = clean.lower()
    if clean_lower in SKILL_ALIASES:
        return SKILL_ALIASES[clean_lower]
    # Check if exact match in any domain
    for domain_info in CANONICAL_MATH_DOMAINS.values():
        for canonical in domain_info["skills"]:
            if canonical.lower() == clean_lower:
                return canonical
    return clean


def get_skills_for_domain(domain: str) -> List[str]:
    """Return all canonical skills for a given domain."""
    domain_key = domain.upper()
    if domain_key in CANONICAL_MATH_DOMAINS:
        return list(CANONICAL_MATH_DOMAINS[domain_key]["skills"])
    return []


def get_domain_for_skill(skill: str) -> Optional[str]:
    """Find the domain containing the specified skill."""
    norm = normalize_skill(skill).lower()
    for domain_name, data in CANONICAL_MATH_DOMAINS.items():
        for s in data["skills"]:
            if s.lower() == norm:
                return domain_name
    return None


def calculate_mastery_level(attempts: int, accuracy: float) -> SkillMasteryLevel:
    """Calculate skill mastery level based on attempt count and accuracy (0.0 to 1.0).

    Thresholds:
    - NOT_STARTED: 0 attempts
    - LEARNING: >0 attempts, accuracy < 60%
    - PRACTICING: 60% <= accuracy < 80% (or 1 attempt with 100%)
    - STRONG: >=2 attempts AND accuracy >= 80%
    """
    if attempts == 0:
        return SkillMasteryLevel.NOT_STARTED
    if attempts >= 2 and accuracy >= 0.8:
        return SkillMasteryLevel.STRONG
    if accuracy >= 0.6:
        return SkillMasteryLevel.PRACTICING
    return SkillMasteryLevel.LEARNING
