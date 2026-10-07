"""Canonical Desmos Techniques seed data for SAT MASTER Desmos Lab.

12 original, comprehensive techniques covering all Digital SAT calculator strategies:
- Step-by-step instructions
- Clear when to use vs when NOT to use guidance
- Common pitfalls
- High-yield SAT speed tricks
"""
from typing import Dict, List
from backend.app.models.enums import DesmosTechniqueType, Difficulty, Subject

CANONICAL_DESMOS_TECHNIQUES: List[Dict] = [
    {
        "slug": "intersection",
        "title": "Find Intersection of Two Equations",
        "description": "Graph two simultaneous equations or functions to pinpoint their exact intersection coordinates $(x, y)$ visually.",
        "technique_type": DesmosTechniqueType.INTERSECTION.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.EASY.value,
        "when_to_use": "When asked to solve systems of linear or nonlinear equations, find where two models are equal, or determine the number of solutions.",
        "when_not_to_use": "When the system is trivial one-step substitution (e.g. $x = 3, y = 2x + 1$) that takes 5 seconds to compute mentally.",
        "steps": [
            "Enter the first equation on line 1 exactly as written (e.g. $y = 3x - 4$).",
            "Enter the second equation on line 2 (e.g. $2x + y = 11$).",
            "Click or tap the gray intersection point on the graph canvas to reveal its $(x, y)$ coordinates.",
            "Read either the $x$-coordinate, $y$-coordinate, or calculate their sum/product as requested.",
        ],
        "common_mistakes": [
            "Forgetting whether the SAT prompt asked for the $x$-coordinate, $y$-coordinate, or an expression like $x + y$.",
            "Typing non-standard variable names instead of $x$ and $y$ without defining them first.",
        ],
        "sat_tip": "If an equation is in implicit standard form like $4x - 5y = 12$, you do NOT need to isolate $y$. Desmos graphs implicit equations natively!",
    },
    {
        "slug": "zero-finding",
        "title": "Find Zeros & X-Intercepts of Functions",
        "description": "Graph polynomial, rational, or quadratic expressions and inspect the $x$-axis to instantly extract real roots without factoring.",
        "technique_type": DesmosTechniqueType.ZERO_FINDING.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.EASY.value,
        "when_to_use": "When solving $f(x) = 0$, finding real solutions to quadratic/cubic equations, or locating $x$-intercepts.",
        "when_not_to_use": "When solutions are complex numbers ($a + bi$), which do not cross the real $x$-axis in Desmos.",
        "steps": [
            "Enter the equation as $y = f(x)$ (e.g. $y = 2x^2 - 5x - 3$).",
            "Inspect the graph along the horizontal $x$-axis where $y = 0$.",
            "Click the gray dot on each $x$-intercept to read the real roots directly.",
        ],
        "common_mistakes": [
            "Confusing the $y$-intercept (where $x = 0$) with $x$-intercepts (where $y = 0$).",
            "Searching for imaginary roots on the real Cartesian coordinate plane.",
        ],
        "sat_tip": "For an equation like $3x^2 - 8x = 11$, type $y = 3x^2 - 8x - 11$ and click the $x$-intercepts to completely bypass the quadratic formula.",
    },
    {
        "slug": "system-of-equations",
        "title": "Solve Systems of Linear & Nonlinear Equations",
        "description": "Resolve systems involving lines, parabolas, and circles to locate multiple intersections or verify solution counts.",
        "technique_type": DesmosTechniqueType.SYSTEM_OF_EQUATIONS.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.MEDIUM.value,
        "when_to_use": "When one equation is linear and the other is quadratic, or when asked for the total number of solutions (0, 1, or 2) to a system.",
        "when_not_to_use": "When the system contains unknown parameter constants like $k$ that require symbolic discriminant analysis.",
        "steps": [
            "Input equation 1 exactly as written on line 1.",
            "Input equation 2 directly on the next line.",
            "Visually count the number of meeting points or click each intersection to note all coordinate pairs.",
        ],
        "common_mistakes": [
            "Missing a second intersection point because it falls outside the default zoom window. Always zoom out or adjust window bounds!",
            "Mixing up solution counts with coordinate values.",
        ],
        "sat_tip": "Pinch-zoom or use the wrench icon to check extreme values if the intersection coordinates might exceed $[-10, 10]$.",
    },
    {
        "slug": "table",
        "title": "Use Tables to Test Values & Patterns",
        "description": "Generate a table of $(x_1, y_1)$ values from an algebraic formula to test answer choices or verify function definitions.",
        "technique_type": DesmosTechniqueType.TABLE.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.EASY.value,
        "when_to_use": "When testing which formula matches a table of data, or evaluating $f(x)$ for multiple distinct inputs.",
        "when_not_to_use": "When calculating a single simple input that can be evaluated on a single calculator line.",
        "steps": [
            "Define the function on line 1: $f(x) = \\text{expression}$.",
            "Click the gear icon and convert to a table, or create a table with $x_1$ and $f(x_1)$.",
            "Enter the problem's given $x$-values into the column and inspect output values against the options.",
        ],
        "common_mistakes": [
            "Typing raw coordinates without linking them to the defined function variable name.",
            "Only testing $x = 0$ or $x = 1$, which frequently match multiple choices accidentally.",
        ],
        "sat_tip": "Always test at least two distinct points (including a negative or larger value) when evaluating equivalent formulas.",
    },
    {
        "slug": "linear-regression",
        "title": "Linear Regression for Rate of Change & Intercept",
        "description": "Use the tilde model $y_1 \\sim m x_1 + b$ on table data to find the exact line of best fit parameters without manual arithmetic.",
        "technique_type": DesmosTechniqueType.LINEAR_REGRESSION.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.MEDIUM.value,
        "when_to_use": "When given two or more coordinate pairs and asked to find slope, $y$-intercept, or linear equation of best fit.",
        "when_not_to_use": "When given standard integer coordinates where $m = \\frac{y_2 - y_1}{x_2 - x_1}$ takes under 10 seconds mentally.",
        "steps": [
            "Click '+' and select 'table' to create columns $x_1$ and $y_1$.",
            "Enter the given data points from the problem into the table.",
            "On the next line, type: $y_1 \\sim m x_1 + b$ using the tilde ($\\sim$) operator.",
            "Read the calculated parameter values for $m$ (slope) and $b$ ($y$-intercept) under Parameters.",
        ],
        "common_mistakes": [
            "Typing standard equals sign '=' instead of the tilde '~'. Desmos requires '~' for regressions.",
            "Typing plain $x$ and $y$ instead of subscripted table headers $x_1$ and $y_1$.",
        ],
        "sat_tip": "Desmos computes exact rational coefficients for linear models, eliminating arithmetic errors on messy decimal coordinates.",
    },
    {
        "slug": "quadratic-regression",
        "title": "Quadratic Regression for Parabolic Models",
        "description": "Fit quadratic models $y_1 \\sim a x_1^2 + b x_1 + c$ to 3 known data points to reveal coefficients, vertices, and maximum heights.",
        "technique_type": DesmosTechniqueType.QUADRATIC_REGRESSION.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.HARD.value,
        "when_to_use": "When given three points on a parabola and asked for the quadratic equation, maximum height, or projectile trajectory.",
        "when_not_to_use": "When the vertex is already explicitly given in vertex form.",
        "steps": [
            "Create a table with columns $x_1$ and $y_1$, inputting the 3 coordinate points.",
            "On the next line, type the regression equation: $y_1 \\sim a x_1^2 + b x_1 + c$.",
            "Inspect the values of $a$, $b$, and $c$.",
            "To find the vertex, type the resulting function $f(x) = a x^2 + b x + c$ and click the highest/lowest point dot.",
        ],
        "common_mistakes": [
            "Forgetting the subscript '1' on the second $x$ term: must write $b x_1$, not $b x$.",
            "Attempting quadratic regression with only 2 points (which cannot uniquely determine a parabola).",
        ],
        "sat_tip": "Desmos regression fits 3 points with $R^2 = 1.0$ (perfect fit), immediately handing you all polynomial coefficients.",
    },
    {
        "slug": "exponential-regression",
        "title": "Exponential Regression for Growth & Decay",
        "description": "Model exponential percentage growth and decay using $y_1 \\sim a \\cdot b^{x_1}$ to identify starting values and multipliers.",
        "technique_type": DesmosTechniqueType.EXPONENTIAL_REGRESSION.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.HARD.value,
        "when_to_use": "When given data points depicting population growth, radioactive decay, or compound interest over time.",
        "when_not_to_use": "When growth percentage $r$ is explicitly stated in prose and simple $(1 + r)^t$ formula applies directly.",
        "steps": [
            "Enter the $(t, y)$ data into a table with columns $x_1$ and $y_1$.",
            "On line 2, enter: $y_1 \\sim a b^{x_1}$.",
            "Observe parameter $a$ (initial value at $x = 0$) and base $b$ (growth/decay factor).",
            "Convert base $b$ to percentage rate: $r = b - 1$ for growth, $r = 1 - b$ for decay.",
        ],
        "common_mistakes": [
            "Confusing base $b$ with annual growth rate $r$. Remember $b = 1 + r$, not $r$ itself.",
            "Using linear regression for compounding relationships.",
        ],
        "sat_tip": "Check the 'Log Mode' checkbox in Desmos if fitting exponential data to ensure College Board standard model parameters.",
    },
    {
        "slug": "inequality-graphing",
        "title": "Graph Inequalities & Identify Feasible Regions",
        "description": "Graph systems of linear inequalities to visually highlight shaded feasible solution sets and test candidate coordinate points.",
        "technique_type": DesmosTechniqueType.INEQUALITY_GRAPHING.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.MEDIUM.value,
        "when_to_use": "When asked whether specific points $(x, y)$ satisfy a system of inequalities, or identifying the vertices of feasible sets.",
        "when_not_to_use": "When a single simple one-variable inequality like $3x - 5 > 7$ is given.",
        "steps": [
            "Type the first inequality (e.g. $y \\ge 2x - 3$). Desmos automatically shades the region.",
            "Type the second inequality (e.g. $x + y < 5$). Desmos overlays the second shaded area.",
            "The double-shaded region represents the valid solution set.",
            "Plot given candidate choices as $(x, y)$ coordinate points to see which point lies strictly inside the intersection.",
        ],
        "common_mistakes": [
            "Forgetting that strict inequalities ($<$ and $>$) have dashed boundary lines; points lying directly on dashed lines are NOT valid solutions.",
            "Misreading shading overlap due to translucent color blending.",
        ],
        "sat_tip": "Plot all 4 answer choice points directly on the graph: $(1, 2), (-2, 4), \\dots$ — the correct choice is visually unmistakable inside the overlap!",
    },
    {
        "slug": "roots",
        "title": "Inspect Radical & Rational Roots",
        "description": "Determine extraneous solutions in radical and rational equations by graphing both sides and looking for valid intersections.",
        "technique_type": DesmosTechniqueType.ROOTS.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.MEDIUM.value,
        "when_to_use": "When solving equations with square roots $\\sqrt{x + a}$ or fractions $\\frac{1}{x - b}$ where algebraic squaring introduces fake solutions.",
        "when_not_to_use": "When equations have obvious domains and simple linear structure.",
        "steps": [
            "Enter left side as $y_1 = \\sqrt{2x + 6}$.",
            "Enter right side as $y_2 = x - 1$.",
            "Look for real intersection points.",
            "Any algebraically computed value where graphs do NOT intersect is an extraneous solution eliminated automatically!",
        ],
        "common_mistakes": [
            "Accepting negative radicands or algebraic artifact solutions that fail the original domain.",
            "Missing the fact that radical graphs terminate at their domain boundary.",
        ],
        "sat_tip": "Graphing eliminates the need to manually plug potential roots back into radical equations to check for extraneous solutions.",
    },
    {
        "slug": "parameter-exploration",
        "title": "Use Sliders & Constants to Test Unknowns",
        "description": "Substitute unknown constants (like $k, c, a$) with Desmos interactive sliders to see how shifting parameters affects intersections.",
        "technique_type": DesmosTechniqueType.PARAMETER_EXPLORATION.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.HARD.value,
        "when_to_use": "When questions ask: 'For what value of $k$ does the system have no solutions / infinitely many solutions / exactly one solution?'",
        "when_not_to_use": "When all values in the equations are fixed constants.",
        "steps": [
            "Type the equation containing the constant, e.g. $y = x^2 + k x + 9$.",
            "Desmos will prompt 'add slider: k'. Click 'k' to activate the slider.",
            "Drag the slider or type the 4 answer choices into $k$ one by one.",
            "Observe when the line becomes tangent (1 solution), parallel (0 solutions), or intersects as requested.",
        ],
        "common_mistakes": [
            "Leaving slider bounds too narrow ($[-10, 10]$). Click the numbers at the ends of the slider to broaden the search range.",
            "Dragging aimlessly instead of plugging the 4 multiple-choice values directly into the slider.",
        ],
        "sat_tip": "Instead of dragging the slider randomly, set $k$ equal to each multiple-choice option (A, B, C, D) one by one to see which creates the required graph behavior instantly!",
    },
    {
        "slug": "graphing-function",
        "title": "Analyze Function Behavior & Transformations",
        "description": "Visualize function translations $f(x - h) + k$, stretches, vertical asymptotes, and maximum/minimum extrema values.",
        "technique_type": DesmosTechniqueType.GRAPHING_FUNCTION.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.MEDIUM.value,
        "when_to_use": "When asked for maximum value of a function, axis of symmetry, domain/range limits, or how $g(x) = f(x + 3) - 2$ shifts the graph.",
        "when_not_to_use": "When questions are purely abstract with no numeric constants or function expressions.",
        "steps": [
            "Define base function $f(x)$ on line 1.",
            "Define transformed function $g(x)$ on line 2 using function notation, e.g. $g(x) = f(x - 4) + 1$.",
            "Compare extrema, intercepts, and vertex coordinates directly on the canvas.",
        ],
        "common_mistakes": [
            "Remembering that $f(x - c)$ shifts RIGHT, not left. Desmos visualizes this immediately so you cannot make the sign error.",
            "Confusing the $x$-value of the maximum with the maximum value itself (which is the $y$-value).",
        ],
        "sat_tip": "Clicking the vertex of any parabola in Desmos reveals $(h, k)$. The question asking 'What is the maximum value?' wants $k$ (the $y$-coordinate)!",
    },
    {
        "slug": "verification",
        "title": "Verify Algebraic Solutions Graphically",
        "description": "Check manually solved answers by testing equivalent expressions or plotting the result alongside the problem statement.",
        "technique_type": DesmosTechniqueType.VERIFICATION.value,
        "subject": Subject.MATH.value,
        "difficulty": Difficulty.EASY.value,
        "when_to_use": "When you have 30 seconds to spare on Module 2 and want 100% confidence on a high-stakes algebra problem.",
        "when_not_to_use": "When running low on time (under 1 minute per remaining question).",
        "steps": [
            "Type the original expression as $y_1 = \\text{original}$.",
            "Type your solved choice as $y_2 = \\text{answer choice}$.",
            "If the expressions are equivalent, the two graphs will overlap perfectly into a single identical line/curve.",
            "Alternatively, subtract them: $y = (\\text{original}) - (\\text{choice})$. If equivalent, the graph is a flat horizontal line at $y = 0$.",
        ],
        "common_mistakes": [
            "Over-relying on verification and running out of time on later challenging problems. Use verification selectively!",
            "Missing subtle coefficient differences when zoomed far out.",
        ],
        "sat_tip": "Subtracting: $(\\text{Original}) - (\\text{Choice}) = 0$ is the ultimate foolproof equivalence test on the Digital SAT.",
    },
]


async def seed_desmos_techniques(db: "AsyncSession") -> int:
    """Seed canonical Desmos techniques and link them to existing Math questions."""
    from sqlalchemy import select
    from backend.app.models.desmos import DesmosTechnique, QuestionDesmosTechnique
    from backend.app.models.question import Question

    seeded = 0
    technique_map = {}

    for t_data in CANONICAL_DESMOS_TECHNIQUES:
        stmt = select(DesmosTechnique).where(DesmosTechnique.slug == t_data["slug"])
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            technique = DesmosTechnique(
                slug=t_data["slug"],
                title=t_data["title"],
                description=t_data["description"],
                technique_type=t_data["technique_type"],
                subject=t_data["subject"],
                difficulty=t_data["difficulty"],
                when_to_use=t_data["when_to_use"],
                when_not_to_use=t_data["when_not_to_use"],
                steps=t_data["steps"],
                common_mistakes=t_data["common_mistakes"],
                sat_tip=t_data["sat_tip"],
            )
            db.add(technique)
            await db.flush()
            technique_map[t_data["technique_type"]] = technique
            seeded += 1
        else:
            technique_map[t_data["technique_type"]] = existing

    # Link existing Math questions to techniques based on skills and keywords
    q_stmt = select(Question).where(
        Question.subject == Subject.MATH.value,
        Question.desmos_allowed == True,
    )
    q_res = await db.execute(q_stmt)
    math_questions = q_res.scalars().all()

    linked_count = 0
    for q in math_questions:
        q_skill = (q.skill or "").lower()
        q_text = (q.question_text or "").lower()
        q_shortcut = (q.sat_shortcut or "").lower()

        # Map to technique types
        target_types = []
        if "system" in q_skill or "system" in q_text:
            target_types.extend([DesmosTechniqueType.INTERSECTION.value, DesmosTechniqueType.SYSTEM_OF_EQUATIONS.value])
        if "quadratic" in q_skill or "parabola" in q_text or "vertex" in q_text:
            target_types.extend([DesmosTechniqueType.ZERO_FINDING.value, DesmosTechniqueType.GRAPHING_FUNCTION.value])
        if "inequalit" in q_skill or "inequalit" in q_text or "feasible" in q_text:
            target_types.append(DesmosTechniqueType.INEQUALITY_GRAPHING.value)
        if "linear equation" in q_skill or "two variables" in q_skill:
            target_types.append(DesmosTechniqueType.LINEAR_REGRESSION.value)
        if "exponential" in q_skill or "growth" in q_text or "decay" in q_text:
            target_types.append(DesmosTechniqueType.EXPONENTIAL_REGRESSION.value)
        if "radical" in q_skill or "rational" in q_skill or "\\sqrt" in q_text:
            target_types.append(DesmosTechniqueType.ROOTS.value)
        if "constant" in q_text or "value of $k$" in q_text or "no solution" in q_text or "infinitely many" in q_text:
            target_types.append(DesmosTechniqueType.PARAMETER_EXPLORATION.value)
        if "table" in q_text or "data" in q_skill:
            target_types.append(DesmosTechniqueType.TABLE.value)
        
        # Every question can be verified
        if q.desmos_recommended:
            target_types.append(DesmosTechniqueType.VERIFICATION.value)

        # Deduplicate target types
        target_types = list(dict.fromkeys(target_types))
        if not target_types:
            # Default to VERIFICATION if no specific mapping
            target_types = [DesmosTechniqueType.VERIFICATION.value]

        for idx, tt in enumerate(target_types):
            tech = technique_map.get(tt)
            if tech:
                # Check if link exists
                link_stmt = select(QuestionDesmosTechnique).where(
                    QuestionDesmosTechnique.question_id == q.id,
                    QuestionDesmosTechnique.technique_id == tech.id,
                )
                link_res = await db.execute(link_stmt)
                if not link_res.scalar_one_or_none():
                    db.add(
                        QuestionDesmosTechnique(
                            question_id=q.id,
                            technique_id=tech.id,
                            technique_type=tt,
                            is_primary=(idx == 0),
                        )
                    )
                    linked_count += 1
                
                # Set example question on technique if unset
                if not tech.example_question_id and q.desmos_recommended:
                    tech.example_question_id = q.id

    if seeded > 0 or linked_count > 0:
        await db.commit()

    return seeded

