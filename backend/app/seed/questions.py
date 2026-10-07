import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import async_session_factory
from backend.app.core.logging import logger
from backend.app.models.enums import (
    Difficulty,
    MathDomain,
    QuestionStatus,
    QuestionType,
    ReadingWritingDomain,
    Subject,
)
from backend.app.models.question import Passage, Question, QuestionOption

# 24 Original SAT-Style Questions (12 Math + 12 Reading & Writing)
SEED_QUESTIONS_DATA = [
    # --- MATH (ALGEBRA) ---
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.ALGEBRA.value,
        "skill": "Linear equations in one variable",
        "subskill": "Evaluating algebraic expressions",
        "difficulty": Difficulty.EASY.value,
        "question_text": "If $3x + 7 = 22$, what is the value of $2x - 1$?",
        "explanation": "First solve for $x$: subtract 7 from both sides to get $3x = 15$, then divide by 3 to get $x = 5$. Next, substitute $x = 5$ into the requested expression: $2(5) - 1 = 10 - 1 = 9$.",
        "hint": "Isolate $x$ first, then be careful to calculate $2x - 1$, not just $x$.",
        "sat_shortcut": "Watch out for College Board prompt traps: always double-check what the question specifically asks you to solve for.",
        "estimated_time_seconds": 45,
        "desmos_allowed": True,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "5", "is_correct": False},
            {"label": "B", "text": "9", "is_correct": True},
            {"label": "C", "text": "10", "is_correct": False},
            {"label": "D", "text": "14", "is_correct": False},
        ],
    },
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.ALGEBRA.value,
        "skill": "Systems of two linear equations",
        "subskill": "Algebraic substitution & elimination",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "Consider the system of equations:\n\n$$2x - y = 5$$\n$$3x + 2y = 11$$\n\nWhat is the value of $x + y$?",
        "explanation": "Multiply the first equation by 2: $4x - 2y = 10$. Add this to the second equation: $(4x + 3x) + (-2y + 2y) = 10 + 11 \\implies 7x = 21 \\implies x = 3$. Substitute $x = 3$ back into the first equation: $2(3) - y = 5 \\implies 6 - y = 5 \\implies y = 1$. Therefore, $x + y = 3 + 1 = 4$.",
        "hint": "Use elimination by multiplying the first equation by 2 to cancel the $y$ terms.",
        "sat_shortcut": "In Desmos, graph both lines `2x - y = 5` and `3x + 2y = 11`. Click the intersection point (3, 1) and sum $3 + 1 = 4$.",
        "estimated_time_seconds": 60,
        "desmos_allowed": True,
        "desmos_recommended": True,
        "options": [
            {"label": "A", "text": "3", "is_correct": False},
            {"label": "B", "text": "4", "is_correct": True},
            {"label": "C", "text": "5", "is_correct": False},
            {"label": "D", "text": "7", "is_correct": False},
        ],
    },
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.ALGEBRA.value,
        "skill": "Systems with infinite or no solutions",
        "subskill": "Parallel and coincident lines",
        "difficulty": Difficulty.HARD.value,
        "question_text": "In the system of equations below, $a$ and $b$ are constants:\n\n$$ax + 6y = 18$$\n$$4x + 3y = b$$\n\nIf the system has infinitely many solutions, what is the value of $a + b$?",
        "explanation": "For a linear system to have infinitely many solutions, both equations must represent the exact same line (proportional coefficients). Notice that multiplying the second equation by 2 yields $8x + 6y = 2b$. Matching coefficients with the first equation ($ax + 6y = 18$): $a = 8$ and $2b = 18 \\implies b = 9$. Thus, $a + b = 8 + 9 = 17$.",
        "hint": "Make the $y$-coefficients equal by multiplying the second equation by 2, then set the corresponding coefficients equal.",
        "sat_shortcut": "Ratio rule for infinite solutions: $\\frac{a}{4} = \\frac{6}{3} = \\frac{18}{b}$. Since $\\frac{6}{3} = 2$, we have $a = 4 \\times 2 = 8$ and $b = 18 / 2 = 9$.",
        "estimated_time_seconds": 75,
        "desmos_allowed": True,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "12", "is_correct": False},
            {"label": "B", "text": "15", "is_correct": False},
            {"label": "C", "text": "17", "is_correct": True},
            {"label": "D", "text": "26", "is_correct": False},
        ],
    },
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.ALGEBRA.value,
        "skill": "Linear functions and slope-intercept form",
        "subskill": "Calculating intercepts from coordinate pairs",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "A line in the $xy$-plane passes through the points $(2, 5)$ and $(6, 13)$. What is the $y$-intercept of the line?",
        "explanation": "Find slope: $m = \\frac{13 - 5}{6 - 2} = \\frac{8}{4} = 2$. Using point-slope form with $(2, 5)$: $y - 5 = 2(x - 2) \\implies y = 2x - 4 + 5 \\implies y = 2x + 1$. The $y$-intercept is $(0, 1)$, meaning $b = 1$.",
        "hint": "First calculate the slope $m = \\frac{y_2 - y_1}{x_2 - x_1}$, then solve for $b$ in $y = mx + b$.",
        "sat_shortcut": "Desmos table trick: create a table with $(2, 5)$ and $(6, 13)$, then type `y1 ~ m x1 + b` to immediately read $b = 1$.",
        "estimated_time_seconds": 60,
        "desmos_allowed": True,
        "desmos_recommended": True,
        "options": [
            {"label": "A", "text": "1", "is_correct": True},
            {"label": "B", "text": "2", "is_correct": False},
            {"label": "C", "text": "3", "is_correct": False},
            {"label": "D", "text": "5", "is_correct": False},
        ],
    },

    # --- MATH (ADVANCED MATH) ---
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.ADVANCED_MATH.value,
        "skill": "Quadratic equations & factoring",
        "subskill": "Roots of quadratic polynomials",
        "difficulty": Difficulty.EASY.value,
        "question_text": "What is the sum of the solutions to the equation $x^2 - 9x + 20 = 0$?",
        "explanation": "Factoring gives $(x - 4)(x - 5) = 0$, so the solutions are $x = 4$ and $x = 5$. Their sum is $4 + 5 = 9$. Alternatively, using Vieta's formulas, for $ax^2 + bx + c = 0$, the sum of roots is $-\\frac{b}{a} = -\\frac{-9}{1} = 9$.",
        "hint": "Factor into $(x - p)(x - q) = 0$ or use Vieta's theorem ($-\\frac{b}{a}$).",
        "sat_shortcut": "Vieta's shortcut: sum of solutions is always $-\\frac{b}{a} = -(-9)/1 = 9$. Takes 3 seconds!",
        "estimated_time_seconds": 40,
        "desmos_allowed": True,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "-9", "is_correct": False},
            {"label": "B", "text": "4", "is_correct": False},
            {"label": "C", "text": "9", "is_correct": True},
            {"label": "D", "text": "20", "is_correct": False},
        ],
    },
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.ADVANCED_MATH.value,
        "skill": "Parabolas & Vertex form",
        "subskill": "Maximum and minimum values",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "The function $f$ is defined by $f(x) = -2(x - 3)^2 + 8$. For what value of $x$ does $f(x)$ reach its maximum value?",
        "explanation": "The equation is in vertex form $f(x) = a(x - h)^2 + k$, where $(h, k)$ is the vertex. Since $a = -2 < 0$, the parabola opens downwards and achieves its maximum value of $8$ at $x = h = 3$.",
        "hint": "Look at vertex form $a(x - h)^2 + k$. The vertex occurs when $(x - h) = 0$.",
        "sat_shortcut": "Be careful: the question asks for the VALUE OF $x$ where the maximum occurs ($x = 3$), not the maximum value itself ($8$).",
        "estimated_time_seconds": 50,
        "desmos_allowed": True,
        "desmos_recommended": True,
        "options": [
            {"label": "A", "text": "-3", "is_correct": False},
            {"label": "B", "text": "3", "is_correct": True},
            {"label": "C", "text": "6", "is_correct": False},
            {"label": "D", "text": "8", "is_correct": False},
        ],
    },
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.ADVANCED_MATH.value,
        "skill": "Quadratic discriminant & roots",
        "subskill": "Conditions for exactly one real solution",
        "difficulty": Difficulty.HARD.value,
        "question_text": "The equation $3x^2 - 12x + c = 0$ has exactly one real solution. What is the value of $c$?",
        "explanation": "A quadratic equation $ax^2 + bx + c = 0$ has exactly one real solution when its discriminant $\\Delta = b^2 - 4ac$ equals $0$. Here, $a = 3$, $b = -12$. So $(-12)^2 - 4(3)(c) = 0 \\implies 144 - 12c = 0 \\implies 12c = 144 \\implies c = 12$.",
        "hint": "Set the discriminant $b^2 - 4ac = 0$.",
        "sat_shortcut": "Divide by 3: $x^2 - 4x + (c/3) = 0$. For a perfect square $(x - 2)^2 = x^2 - 4x + 4$, so $c/3 = 4 \\implies c = 12$.",
        "estimated_time_seconds": 65,
        "desmos_allowed": True,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "6", "is_correct": False},
            {"label": "B", "text": "12", "is_correct": True},
            {"label": "C", "text": "24", "is_correct": False},
            {"label": "D", "text": "36", "is_correct": False},
        ],
    },
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.ADVANCED_MATH.value,
        "skill": "Exponential growth & decay",
        "subskill": "Interpreting exponential parameters",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "A population of a certain bird species in a nature reserve is modeled by the function $P(t) = 450(1.06)^t$, where $t$ is the number of years after 2020. Which of the following is the best interpretation of the number $1.06$ in this context?",
        "explanation": "In standard exponential growth $P(t) = P_0(1 + r)^t$, the base $1.06 = 1 + 0.06$ represents a growth rate of $r = 0.06 = 6\\%$ per year. Thus, the population increases by 6% each year.",
        "hint": "Rewrite $1.06$ as $1 + 0.06$ and convert the decimal to a percentage.",
        "sat_shortcut": "Base $> 1$ indicates growth. $1.06 - 1.00 = 0.06 = 6\\%$ increase.",
        "estimated_time_seconds": 45,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "The population increases by 6 birds each year.", "is_correct": False},
            {"label": "B", "text": "The population increases by 6% each year.", "is_correct": True},
            {"label": "C", "text": "The population in the year 2020 was 106 birds.", "is_correct": False},
            {"label": "D", "text": "The population multiplies by 106 every 10 years.", "is_correct": False},
        ],
    },

    # --- MATH (PROBLEM-SOLVING & DATA ANALYSIS) ---
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.PROBLEM_SOLVING_DATA_ANALYSIS.value,
        "skill": "Ratios and proportions",
        "subskill": "Part-to-whole relationships",
        "difficulty": Difficulty.EASY.value,
        "question_text": "In a chemistry laboratory, the ratio of milliliters of acid to milliliters of water in a solution is $3:5$. If the total volume of the solution is $240\\text{ mL}$, how many milliliters of acid are in the solution?",
        "explanation": "The total number of ratio parts is $3 + 5 = 8$ parts. Each part corresponds to $240 / 8 = 30\\text{ mL}$. Since acid constitutes 3 parts, the volume of acid is $3 \\times 30 = 90\\text{ mL}$.",
        "hint": "Divide the total volume by the sum of the ratio terms ($3 + 5 = 8$).",
        "sat_shortcut": "Acid fraction is $\\frac{3}{3 + 5} = \\frac{3}{8}$. Multiply: $\\frac{3}{8} \\times 240 = 3 \\times 30 = 90$.",
        "estimated_time_seconds": 45,
        "desmos_allowed": True,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "60", "is_correct": False},
            {"label": "B", "text": "90", "is_correct": True},
            {"label": "C", "text": "120", "is_correct": False},
            {"label": "D", "text": "150", "is_correct": False},
        ],
    },
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.PROBLEM_SOLVING_DATA_ANALYSIS.value,
        "skill": "Percentages & Successive discounts",
        "subskill": "Compound percentage reductions",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "An electronics retailer discounts a tablet by $20\\%$. During a weekend promotion, an additional $15\\%$ discount is applied to the already discounted price. What is the total effective percentage discount from the original price?",
        "explanation": "Assume original price is \\$100. After the 20% discount, the price is $100 \\times 0.80 = \\$80$. The second discount of 15% is applied to \\$80: $80 \\times (1 - 0.15) = 80 \\times 0.85 = \\$68$. The total discount is $100 - 68 = \\$32$, which represents a $32\\%$ overall reduction.",
        "hint": "Successive discounts multiply factors: $(1 - 0.20)(1 - 0.15) = 0.80 \\times 0.85$.",
        "sat_shortcut": "NEVER simply add percentage discounts ($20\\% + 15\\% \\neq 35\\%$). Effective factor = $0.80 \\times 0.85 = 0.68 \\implies 32\\%$ discount.",
        "estimated_time_seconds": 60,
        "desmos_allowed": True,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "30%", "is_correct": False},
            {"label": "B", "text": "32%", "is_correct": True},
            {"label": "C", "text": "35%", "is_correct": False},
            {"label": "D", "text": "38%", "is_correct": False},
        ],
    },

    # --- MATH (GEOMETRY & TRIGONOMETRY) ---
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.GEOMETRY_TRIGONOMETRY.value,
        "skill": "Right triangles and trigonometry",
        "subskill": "Complementary angle relationships",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "In right triangle $ABC$, the measure of angle $C$ is $90^\\circ$. If $\\sin(A) = \\frac{7}{25}$, what is the value of $\\cos(B)$?",
        "explanation": "In any right triangle where $C = 90^\\circ$, acute angles $A$ and $B$ are complementary ($A + B = 90^\\circ$). By the complementary angle trigonometric identity, $\\sin(A) = \\cos(90^\\circ - A) = \\cos(B)$. Therefore, $\\cos(B) = \\frac{7}{25}$.",
        "hint": "Remember the fundamental identity: $\\sin(\\theta) = \\cos(90^\\circ - \\theta)$.",
        "sat_shortcut": "In a right triangle with acute angles $A$ and $B$, $\\sin(A)$ ALWAYS equals $\\cos(B)$. No calculation needed!",
        "estimated_time_seconds": 30,
        "desmos_allowed": True,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "7/25", "is_correct": True},
            {"label": "B", "text": "24/25", "is_correct": False},
            {"label": "C", "text": "7/24", "is_correct": False},
            {"label": "D", "text": "25/7", "is_correct": False},
        ],
    },
    {
        "subject": Subject.MATH.value,
        "domain": MathDomain.GEOMETRY_TRIGONOMETRY.value,
        "skill": "Circle equations in the coordinate plane",
        "subskill": "Finding radius from standard equation",
        "difficulty": Difficulty.HARD.value,
        "question_text": "In the $xy$-plane, the equation of a circle is $x^2 - 6x + y^2 + 8y = 24$. What is the radius of the circle?",
        "explanation": "Complete the square for $x$ and $y$: $(x^2 - 6x + 9) + (y^2 + 8y + 16) = 24 + 9 + 16 \\implies (x - 3)^2 + (y + 4)^2 = 49$. The standard form is $(x - h)^2 + (y - k)^2 = r^2$, so $r^2 = 49 \\implies r = 7$.",
        "hint": "Add $(b/2)^2$ to both sides for both the $x$ terms and $y$ terms.",
        "sat_shortcut": "Desmos trick: type the equation $x^2 - 6x + y^2 + 8y = 24$ directly. Click the center $(3, -4)$ and the rightmost point $(10, -4)$. Distance is $10 - 3 = 7$.",
        "estimated_time_seconds": 75,
        "desmos_allowed": True,
        "desmos_recommended": True,
        "options": [
            {"label": "A", "text": "5", "is_correct": False},
            {"label": "B", "text": "7", "is_correct": True},
            {"label": "C", "text": "14", "is_correct": False},
            {"label": "D", "text": "49", "is_correct": False},
        ],
    },

    # --- READING & WRITING (INFORMATION & IDEAS) ---
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.INFORMATION_IDEAS.value,
        "skill": "Central ideas and details",
        "subskill": "Synthesizing main claim",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "Deep-sea anglerfish inhabit bathypelagic depths where solar radiation is entirely absent and prey encounters are extraordinarily sparse. Rather than maintaining active metabolic exertion through continuous foraging, female anglerfish remain nearly stationary, using a photophore—a bioluminescent dorsal spine lure populated with symbiotic bacteria—to draw unsuspecting prey into striking range. This sit-and-wait predatory tactic allows them to minimize calorie expenditure while maximizing feeding opportunities in a resource-deprived biome.\n\nWhich choice best states the main idea of the text?",
        "explanation": "The passage describes how female anglerfish inhabit a lightless, food-scarce environment and employ stationary bioluminescent lures to conserve vital metabolic energy while securing scarce prey. Choice B accurately captures this core thesis.",
        "hint": "Look for the sentence that brings together the environment, the bioluminescent lure, and metabolic conservation.",
        "sat_shortcut": "Eliminate extreme or narrow options that focus only on bacterial symbiosis without mentioning predatory energy strategy.",
        "estimated_time_seconds": 75,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "Symbiotic bacteria provide the primary source of nutrition for bathypelagic anglerfish.", "is_correct": False},
            {"label": "B", "text": "Bioluminescent luring enables anglerfish to conserve metabolic energy in a nutrient-scarce habitat.", "is_correct": True},
            {"label": "C", "text": "Deep-sea organisms forage constantly to compensate for extreme hydrodynamic pressure.", "is_correct": False},
            {"label": "D", "text": "Anglerfish are uniquely vulnerable to starvation because they cannot swim efficiently.", "is_correct": False},
        ],
    },
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.INFORMATION_IDEAS.value,
        "skill": "Command of evidence",
        "subskill": "Supporting an archaeological hypothesis",
        "difficulty": Difficulty.HARD.value,
        "question_text": "Archaeologist Dr. Lena Morales posits that the ancient Indus Valley settlement of Dholavira survived cyclical monsoon failures not through regional grain trade, but through an intricate municipal hydraulic network of interconnected stone-cut reservoirs that captured ephemeral runoff from surrounding seasonal streams.\n\nWhich finding, if true, would most directly support Dr. Morales's hypothesis?",
        "explanation": "Dr. Morales's hypothesis specifically claims that Dholavira survived local droughts via internal reservoir systems collecting seasonal rainwater rather than importing external food. Choice C directly substantiates this by demonstrating that sedimentary layers within the reservoirs show continuous local water storage throughout historically documented drought periods.",
        "hint": "Find evidence specifically linking survival to the stone reservoirs and local rainwater capture rather than external trade.",
        "sat_shortcut": "Disregard choices that discuss regional trade agreements or pottery styles, as they contradict or fail to address the hydraulic hypothesis.",
        "estimated_time_seconds": 90,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "Excavations revealed extensive clay records detailing grain purchases from Mesopotamian coastal ports.", "is_correct": False},
            {"label": "B", "text": "Surrounding settlements without stone architecture flourished during the same multi-decade drought.", "is_correct": False},
            {"label": "C", "text": "Sedimentary core samples from the reservoirs reveal continuous freshwater accumulation during documented regional drought eras.", "is_correct": True},
            {"label": "D", "text": "Decorative pottery discovered in residential sectors depicted maritime trading expeditions.", "is_correct": False},
        ],
    },
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.INFORMATION_IDEAS.value,
        "skill": "Inferences",
        "subskill": "Logical conclusions without speculation",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "Avian biologists studying night-migrating warblers determined that when planetary night skies are clear, the birds orient their heading with high precision by referencing the rotational axis of circumpolar star constellations. However, when artificial planetarium projections simulated an overcast ceiling lacking visible astral landmarks, the birds' headings exhibited random orientation, unless low-frequency geomagnetic cues were simultaneously amplified.\n\nBased on the text, what can be reasonably inferred about migratory warblers?",
        "explanation": "The text demonstrates that under cloudy conditions (no celestial markers), warblers lose directional orientation UNLESS geomagnetic cues are boosted. Thus, in the absence of stars, their navigation relies critically on geomagnetic fields.",
        "hint": "Notice what happens when stars disappear: what condition restored their navigation?",
        "sat_shortcut": "Select the choice strictly bound by the text. Avoid speculative choices claiming warblers never fly during cloudy weather.",
        "estimated_time_seconds": 80,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "Warblers rely primarily on landmarks like rivers and mountain ridges during overcast nights.", "is_correct": False},
            {"label": "B", "text": "Geomagnetic cues can serve as an alternative navigation mechanism when stellar markers are obscured.", "is_correct": True},
            {"label": "C", "text": "Warblers avoid nocturnal migration entirely during seasonal overcast weather.", "is_correct": False},
            {"label": "D", "text": "Artificial planetarium lighting permanently damages the birds' internal directional compass.", "is_correct": False},
        ],
    },

    # --- READING & WRITING (CRAFT & STRUCTURE) ---
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.CRAFT_STRUCTURE.value,
        "skill": "Words in context",
        "subskill": "Determining precise contextual definition",
        "difficulty": Difficulty.EASY.value,
        "question_text": "Rejecting the flamboyant ornamentation favored by his contemporaries, the minimalist sculptor insisted on an aesthetic that was intentionally austere, utilizing unpolished granite blocks and spare geometrical silhouettes to evoke contemplative stillness.\n\nAs used in the text, what does \"austere\" most nearly mean?",
        "explanation": "\"Austere\" is placed in direct contrast to \"flamboyant ornamentation\" and is paired with \"unpolished granite\" and \"spare geometrical silhouettes.\" In this context, it clearly means severe, unadorned, or simple.",
        "hint": "Contrast clue: 'Rejecting flamboyant ornamentation'.",
        "sat_shortcut": "Substitute options into the sentence: 'an aesthetic that was intentionally unadorned' preserves the precise contrast.",
        "estimated_time_seconds": 45,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "unadorned", "is_correct": True},
            {"label": "B", "text": "fragile", "is_correct": False},
            {"label": "C", "text": "extravagant", "is_correct": False},
            {"label": "D", "text": "gloomy", "is_correct": False},
        ],
    },
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.CRAFT_STRUCTURE.value,
        "skill": "Words in context",
        "subskill": "Academic Tier 2 vocabulary",
        "difficulty": Difficulty.HARD.value,
        "question_text": "While earlier economic historians characterized the sudden collapse of nineteenth-century agricultural cooperatives as an aberrant anomaly resulting from singular weather events, contemporary researchers view the decline as the predictable consequence of chronic credit deficits.\n\nAs used in the text, what does \"aberrant\" most nearly mean?",
        "explanation": "The text pairs \"aberrant\" with \"anomaly\" and contrasts it with \"predictable consequence.\" An aberrant anomaly is something atypical, abnormal, or deviating from standard patterns.",
        "hint": "Look at the paired word 'anomaly' and the contrast with 'predictable'.",
        "sat_shortcut": "Look for a synonym of atypical or deviating from normal.",
        "estimated_time_seconds": 55,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "catastrophic", "is_correct": False},
            {"label": "B", "text": "atypical", "is_correct": True},
            {"label": "C", "text": "premeditated", "is_correct": False},
            {"label": "D", "text": "cyclical", "is_correct": False},
        ],
    },
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.CRAFT_STRUCTURE.value,
        "skill": "Text structure and purpose",
        "subskill": "Analyzing rhetorical function of sentences",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "Neuroscientists have long observed that sleep deprivation impedes declarative memory consolidation. In a 2023 study, researcher Dr. Miriam Chen recorded micro-voltage fluctuations across hippocampal synapses during non-REM rest phases, demonstrating that slow-wave oscillations literally synchronize electrical pulses between the hippocampus and neocortex. By demonstrating this physical electrical coupling, Chen provided the first direct mechanistic blueprint of how memories physically migrate to long-term storage.\n\nWhich choice best describes the overall function of the underlined portion in the text?",
        "explanation": "The text first introduces the long-standing observation about sleep and memory, then describes Dr. Chen's specific empirical discovery, and finally emphasizes how her discovery provided the physical mechanistic explanation for the previously unexplained phenomenon.",
        "hint": "The last sentence shows how Chen's study explains the mechanism behind the first sentence's observation.",
        "sat_shortcut": "Focus on the transition from empirical observation to mechanistic validation.",
        "estimated_time_seconds": 75,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "It refutes an outdated hypothesis regarding synaptic degeneration.", "is_correct": False},
            {"label": "B", "text": "It explains the broader significance of the empirical findings described earlier.", "is_correct": True},
            {"label": "C", "text": "It proposes an experimental methodology for subsequent clinical trials.", "is_correct": False},
            {"label": "D", "text": "It introduces a controversial claim that challenges accepted neurology.", "is_correct": False},
        ],
    },

    # --- READING & WRITING (EXPRESSION OF IDEAS) ---
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.EXPRESSION_IDEAS.value,
        "skill": "Transitions",
        "subskill": "Logical connecting words (Cause & Effect)",
        "difficulty": Difficulty.EASY.value,
        "question_text": "Over the past two decades, high-efficiency photovoltaic manufacturing techniques have slashed the production cost of solar silicon cells by more than eighty percent. __________, residential rooftop installations have expanded rapidly across suburban neighborhoods nationwide.",
        "explanation": "The first sentence describes a steep reduction in production costs. The second describes the resulting surge in residential installations. This is a direct cause-and-effect relationship, requiring 'Consequently'.",
        "hint": "Cost drops -> Installations surge. What type of relationship is this?",
        "sat_shortcut": "Cause and effect requires 'Consequently'. 'In contrast' or 'Similarly' would misstate the logical connection.",
        "estimated_time_seconds": 40,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "In contrast,", "is_correct": False},
            {"label": "B", "text": "Consequently,", "is_correct": True},
            {"label": "C", "text": "Nevertheless,", "is_correct": False},
            {"label": "D", "text": "For instance,", "is_correct": False},
        ],
    },
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.EXPRESSION_IDEAS.value,
        "skill": "Transitions",
        "subskill": "Logical connecting words (Contrast)",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "Renaissance fresco painters were obliged to mix mineral pigments with fresh wet plaster every morning, requiring swift execution before the surface cured. __________, oil painters of the Baroque period could rework canvas layers over months due to the exceptionally slow oxidation rate of linseed oil.",
        "explanation": "The first sentence describes fresco painters needing to paint quickly before wet plaster dries. The second contrasts this with Baroque oil painters who had months to rework canvas due to slow-drying linseed oil. This is a clear contrast relationship, best served by 'Conversely'.",
        "hint": "Fresco painters had to rush; oil painters could take months. This is a contrast.",
        "sat_shortcut": "'Conversely' signals an opposing or differing counter-case.",
        "estimated_time_seconds": 45,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "Furthermore,", "is_correct": False},
            {"label": "B", "text": "Conversely,", "is_correct": True},
            {"label": "C", "text": "Likewise,", "is_correct": False},
            {"label": "D", "text": "Specifically,", "is_correct": False},
        ],
    },
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.EXPRESSION_IDEAS.value,
        "skill": "Rhetorical synthesis",
        "subskill": "Selecting notes to achieve a specified goal",
        "difficulty": Difficulty.HARD.value,
        "question_text": "While researching agricultural biodiversity, a student took the following notes:\n• Teff is an ancient cereal grain domesticated in the Horn of Africa around 4000 BCE.\n• It thrives in marginal soil conditions prone to both waterlogging and drought.\n• Its seed contains high concentrations of iron, calcium, and essential amino acids.\n• Agronomist Dr. Samuel Kassa bred modern high-yield teff cultivars for smallholder farmers.\n• Kassa's cultivars yield 35% more grain while maintaining climate resilience.\n\nThe student wants to emphasize the nutritional and ecological advantages of cultivating teff. Which choice most effectively uses relevant information from the notes to accomplish this goal?",
        "explanation": "The prompt specifies two goals: emphasizing (1) nutritional advantages and (2) ecological advantages. Choice B directly addresses both: it notes teff's resilience in drought/waterlogged soil (ecological) and its rich concentrations of iron, calcium, and amino acids (nutritional).",
        "hint": "Check that the answer addresses BOTH 'nutritional' and 'ecological' advantages.",
        "sat_shortcut": "Eliminate choices that focus solely on Dr. Kassa's breeding project without detailing both nutrition and climate ecology.",
        "estimated_time_seconds": 85,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "Domestication of teff began around 4000 BCE in the Horn of Africa, where smallholder farmers cultivate it today.", "is_correct": False},
            {"label": "B", "text": "Teff offers remarkable ecological resilience by thriving in both flood and drought, while providing vital nutrition through high levels of iron, calcium, and amino acids.", "is_correct": True},
            {"label": "C", "text": "Dr. Samuel Kassa developed high-yield teff varieties that produce 35% more grain for smallholder agricultural communities.", "is_correct": False},
            {"label": "D", "text": "Although teff was cultivated thousands of years ago, modern agronomists have recently improved its yield.", "is_correct": False},
        ],
    },

    # --- READING & WRITING (STANDARD ENGLISH CONVENTIONS) ---
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.STANDARD_ENGLISH_CONVENTIONS.value,
        "skill": "Sentence boundaries",
        "subskill": "Joining independent clauses without comma splices",
        "difficulty": Difficulty.EASY.value,
        "question_text": "The astronomers calibrated the spectrometer before nightfall __________ the overcast cloud cover dissipated just as the telescope's tracking motors engaged.",
        "explanation": "Both 'The astronomers calibrated the spectrometer before nightfall' and 'the overcast cloud cover dissipated just as the telescope's tracking motors engaged' are complete independent clauses. Joining two independent clauses requires a semicolon or a comma with a coordinating conjunction (FANBOYS). Choice B correctly uses '; fortunately,' with a semicolon preceding the conjunctive adverb.",
        "hint": "Identify the two independent clauses. A comma alone creates a comma splice.",
        "sat_shortcut": "Two complete thoughts need a semicolon or period unless accompanied by a FANBOYS conjunction.",
        "estimated_time_seconds": 45,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": ", fortunately,", "is_correct": False},
            {"label": "B", "text": "; fortunately,", "is_correct": True},
            {"label": "C", "text": " fortunately", "is_correct": False},
            {"label": "D", "text": ", and fortunately;", "is_correct": False},
        ],
    },
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.STANDARD_ENGLISH_CONVENTIONS.value,
        "skill": "Subject-verb agreement",
        "subskill": "Intervening prepositional phrases",
        "difficulty": Difficulty.MEDIUM.value,
        "question_text": "A comprehensive compilation of archaeological field reports from several excavation sites in the Andes __________ currently housed in the university archives.",
        "explanation": "The head noun of the subject is 'compilation' (singular), not 'reports' or 'sites', which are objects of intervening prepositional phrases ('of archaeological field reports', 'from several excavation sites'). A singular subject requires the singular verb 'is'.",
        "hint": "Cross out the prepositional phrases 'of archaeological field reports' and 'from several excavation sites'. What is the true subject?",
        "sat_shortcut": "Singular subject ('compilation') -> singular verb ('is'). Ignore plural nouns inside prepositional phrases.",
        "estimated_time_seconds": 45,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "is", "is_correct": True},
            {"label": "B", "text": "are", "is_correct": False},
            {"label": "C", "text": "were", "is_correct": False},
            {"label": "D", "text": "have been", "is_correct": False},
        ],
    },
    {
        "subject": Subject.READING_WRITING.value,
        "domain": ReadingWritingDomain.STANDARD_ENGLISH_CONVENTIONS.value,
        "skill": "Modifier placement",
        "subskill": "Dangling participial modifiers",
        "difficulty": Difficulty.HARD.value,
        "question_text": "Having cataloged over four thousand ceramic shards from the submerged Roman galley, __________",
        "explanation": "The opening participial phrase 'Having cataloged over four thousand ceramic shards from the submerged Roman galley' describes an action performed by people. Therefore, the noun immediately following the comma must be the person or team who did the cataloging ('the marine archaeologists'). In other choices, the shards, museum, or research conclusions become nonsensical dangling modifiers.",
        "hint": "Who did the cataloging? That person/group must immediately follow the comma.",
        "sat_shortcut": "Dangling modifier rule: Subject after comma MUST be the actor performing the opening participle action.",
        "estimated_time_seconds": 55,
        "desmos_allowed": False,
        "desmos_recommended": False,
        "options": [
            {"label": "A", "text": "the marine archaeologists presented their chronological timeline to the symposium.", "is_correct": True},
            {"label": "B", "text": "the chronological timeline was presented to the symposium by the marine archaeologists.", "is_correct": False},
            {"label": "C", "text": "the museum's collection was expanded significantly with the new artifacts.", "is_correct": False},
            {"label": "D", "text": "a comprehensive excavation report was finalized by the research team.", "is_correct": False},
        ],
    },
]


async def seed_questions(db: AsyncSession) -> int:
    """
    Seeds original SAT-style questions into the database if not already present.
    Returns the count of questions inserted.
    """
    seeded_count = 0

    for item in SEED_QUESTIONS_DATA:
        # Check if question already exists by matching text snippet
        existing = await db.execute(
            select(Question).where(Question.question_text == item["question_text"])
        )
        if existing.scalar_one_or_none():
            continue

        q = Question(
            subject=item["subject"],
            domain=item["domain"],
            skill=item["skill"],
            subskill=item.get("subskill"),
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            difficulty=item["difficulty"],
            question_text=item["question_text"],
            explanation=item["explanation"],
            hint=item.get("hint"),
            sat_shortcut=item.get("sat_shortcut"),
            estimated_time_seconds=item.get("estimated_time_seconds", 75),
            desmos_allowed=item.get("desmos_allowed", True),
            desmos_recommended=item.get("desmos_recommended", False),
            status=QuestionStatus.PUBLISHED.value,
        )

        for idx, opt_data in enumerate(item["options"]):
            opt = QuestionOption(
                label=opt_data["label"],
                text=opt_data["text"],
                order_index=idx,
                is_correct=opt_data["is_correct"],
            )
            q.options.append(opt)

        db.add(q)
        seeded_count += 1

    if seeded_count > 0:
        await db.commit()
        logger.info(f"Seeded {seeded_count} original SAT questions.")

    return seeded_count


async def run_seed():
    async with async_session_factory() as session:
        count = await seed_questions(session)
        print(f"Successfully seeded {count} questions.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_seed())
