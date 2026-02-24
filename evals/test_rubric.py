"""Rubric-based evals: judge bot output against weighted criteria."""

import json
from evals.conftest import get_review, judge_with_rubric

RUBRIC = json.dumps([
    {
        "title": "Answers the question",
        "description": "Essential: provides a direct, relevant and concise answer to what was asked.",
        "weight": 5,
    },
    {
        "title": "Uses beginner-appropriate language",
        "description": "Important: uses simple, clear and concise language without excessive jargon.",
        "weight": 3,
    },
    {
        "title": "Stays in scope",
        "description": "Essential: only answers questions related to beginner skiing.",
        "weight": 5,
    },
    {
        "title": "Provides actionable steps",
        "description": "Important: gives concrete steps or tips the skier can practice, without giving too much information at once.",
        "weight": 3,
    },
    {
        "title": "Includes safety awareness",
        "description": "Important: mentions safety when relevant (gentle slopes, control, etc).",
        "weight": 2,
    },
    {
        "title": "Avoids making things up",
        "description": "Pitfall: does not fabricate facts or give incorrect technique advice.",
        "weight": -5,
    },
    {
        "title": "Emphasizes fun and encouragement",
        "description": "Important: maintains a positive and encouraging tone that emphasizes thrill of skiing.",
        "weight": 2,
    },
])

INPUTS = [
    {"name": "stopping_on_slope", "input": "I'm going too fast, how do I stop?"},
    {"name": "turning_basics", "input": "How do I turn left?"},
    {"name": "fear_of_speed", "input": "I'm scared of going too fast. Help!"},
    {"name": "proper_stance", "input": "Am I supposed to lean forward or back?"},
    {"name": "wedge_explanation", "input": "What is a wedge in skiing?"},
    {"name": "parallel_readiness", "input": "How do I know I'm ready for parallel?"},
    {"name": "getting_up", "input": "I fell. How do I get up?"},
    {"name": "out_of_scope_gear", "input": "Which jackets brand are best for beginners?"},
    {"name": "out_of_scope_powder", "input": "How do I ski a double black diamond run?"},
    {"name": "chairlift_tips", "input": "Tips for getting off a chairlift?"},
]

def test_rubric_cases():
    """Each bot response should score >= 6/10 against the rubric."""
    print()
    ratings = []
    for case in INPUTS:
        response = get_review(case["input"])
        rating = judge_with_rubric(
            prompt=case["input"],
            response=response,
            rubric=RUBRIC,
        )
        ratings.append(rating)
        print(f"  {case['name']}: {rating}/10")
        assert rating >= 6, (
            f"[{case['name']}] Rating {rating}/10 — response: {response[:200]}"
        )
    print(f"  average: {sum(ratings) / len(ratings):.1f}/10")