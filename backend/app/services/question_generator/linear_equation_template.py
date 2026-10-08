"""Concrete parameterized generator template for Linear Equations."""
import random
from typing import Optional

from backend.app.models.enums import Difficulty, MathDomain, QuestionType, Subject
from backend.app.services.question_generator.base import (
    BaseQuestionTemplate,
    GeneratedOption,
    GeneratedQuestionVariant,
    ValidationResult,
)


class LinearEquationTemplate(BaseQuestionTemplate):
    """
    Template for:
    "If ax + b = c, what is the value of dx + e?"
    Guarantees integer solutions, clean distractor generation, and rigorous explanation.
    """

    @property
    def template_id(self) -> str:
        return "math_algebra_linear_001"

    @property
    def subject(self) -> str:
        return Subject.MATH.value

    @property
    def domain(self) -> str:
        return MathDomain.ALGEBRA.value

    @property
    def skill(self) -> str:
        return "Linear equations in one variable"

    @property
    def default_difficulty(self) -> str:
        return Difficulty.EASY.value

    def generate_variant(self, seed: Optional[int] = None) -> GeneratedQuestionVariant:
        rng = random.Random(seed) if seed is not None else random.Random()

        # Generate integer parameters
        a = rng.choice([2, 3, 4, 5, 6, 7, 8])
        x = rng.choice([2, 3, 4, 5, 6, 7, 8, 9, 10])
        b = rng.randint(3, 19)
        c = a * x + b

        d = rng.choice([2, 3, 4])
        e = rng.choice([-5, -3, -1, 1, 3, 5])
        target_value = d * x + e

        # Target expression string
        op_sign = "+" if e >= 0 else "-"
        abs_e = abs(e)
        expr_str = f"{d}x {op_sign} {abs_e}"

        question_text = f"If ${a}x + {b} = {c}$, what is the value of ${expr_str}$?"

        explanation = (
            f"Step 1: Solve for $x$ in the equation ${a}x + {b} = {c}$.\n"
            f"Subtract {b} from both sides: ${a}x = {c - b}$.\n"
            f"Divide by {a}: $x = {x}$.\n\n"
            f"Step 2: Evaluate the requested expression ${expr_str}$ for $x = {x}$:\n"
            f"${d}({x}) {op_sign} {abs_e} = {d * x} {op_sign} {abs_e} = {target_value}$."
        )

        hint = f"Isolate $x$ first, then substitute it into ${expr_str}$."
        sat_shortcut = "Beware of answering just $x$; the SAT asks for the value of the full expression."

        # Distractor generation
        distractor_1 = x  # Just x
        distractor_2 = target_value + rng.choice([2, 4, 6])
        distractor_3 = max(1, target_value - rng.choice([2, 4, 6]))

        # Ensure all 4 values are distinct
        all_vals = {target_value}
        while len(all_vals) < 4:
            cand = rng.randint(max(1, target_value - 10), target_value + 15)
            all_vals.add(cand)

        # Shuffle and assign to A, B, C, D
        val_list = list(all_vals)
        rng.shuffle(val_list)

        options = []
        labels = ["A", "B", "C", "D"]
        for idx, val in enumerate(val_list):
            options.append(
                GeneratedOption(
                    label=labels[idx],
                    text=str(val),
                    is_correct=(val == target_value),
                )
            )

        return GeneratedQuestionVariant(
            template_id=self.template_id,
            variant_group=f"linear_eq_{a}x_{b}",
            subject=self.subject,
            domain=self.domain,
            skill=self.skill,
            subskill="Evaluating algebraic expressions",
            difficulty=self.default_difficulty,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            question_text=question_text,
            explanation=explanation,
            hint=hint,
            sat_shortcut=sat_shortcut,
            options=options,
            estimated_time_seconds=45,
            desmos_allowed=True,
            desmos_recommended=False,
            metadata={
                "a": a,
                "b": b,
                "c": c,
                "d": d,
                "e": e,
                "x": x,
                "target_value": target_value,
            },
        )

    def validate_variant(self, variant: GeneratedQuestionVariant) -> ValidationResult:
        errors = []
        if len(variant.options) != 4:
            errors.append("Variant must have exactly 4 options.")
        correct_count = sum(1 for opt in variant.options if opt.is_correct)
        if correct_count != 1:
            errors.append(f"Variant must have exactly 1 correct option, found {correct_count}.")

        # Check unique option texts
        texts = [opt.text for opt in variant.options]
        if len(set(texts)) != 4:
            errors.append("Options must have distinct values.")

        # Check metadata consistency
        m = variant.metadata
        if m:
            if m["a"] * m["x"] + m["b"] != m["c"]:
                errors.append("Equation a*x + b = c does not balance.")
            if m["d"] * m["x"] + m["e"] != m["target_value"]:
                errors.append("Target expression calculation mismatch.")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
