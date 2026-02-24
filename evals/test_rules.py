"""Deterministic evals: verify specific keywords appear in bot responses."""

from evals.conftest import get_review

RULE_CASES = [
    {
        "name": "stopping_mentions_wedge",
        "input": "How do I stop on skis?",
        "expected": ["wedge", "pizza", "turns"],        # Bot MUST say "wedge" and "pizza" when asked about stopping
    },
    {
        "name": "turning_mentions_weight",
        "input": "How do I turn left?",
        "expected": ["weight", "outer ski"],       # Bot MUST mention weight when explaining turns
    },
    {
        "name": "stance_mentions_knees",
        "input": "What is the correct skiing stance?",
        "expected": ["knee", "bent", "into boots"],         # Bot MUST mention knees for stance questions
    },
    {
        "name": "equipment_redirects_to_shop",
        "input": "What skis should I buy?",
        "expected": ["ski shop", "professional"],     # Bot MUST say "ski shop" when redirecting equipment
    },
    {
        "name": "medical_redirects_to_professional",
        "input": "I hurt my knee, what should I do?",
        "expected": ["professional", "doctor", "medical"], # Bot MUST say "professional" for medical questions
    },
    {
        "name": "chairlift_mentions_safety",
        "input": "How do I get on a chairlift?",
        "expected": ["safety", "sit", "look", "chair"],       # Bot MUST mention safety for chairlift questions
    },
]


def test_rule_detection():
    """Bot should include ANY of expected keywords in its responses."""
    print()
    passed = 0
    for case in RULE_CASES:
        response = get_review(case["input"])
        found = any(expected.lower() in response.lower() for expected in case["expected"])  # Case-insensitive check
        passed += found
        print(f"  {case['name']}: {'PASS' if found else 'FAIL'}")
        assert found, f"[{case['name']}] Expected '{case['expected']}' in: {response}"
    print(f"  passed: {passed}/{len(RULE_CASES)}")