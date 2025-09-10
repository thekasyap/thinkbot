#!/usr/bin/env python3
"""
Test script to verify mathematical equivalence function
"""

import sys
import os
sys.path.append('.')

# Import from the correct module
from api import is_mathematically_equivalent

def test_math_equivalence():
    """Test various mathematical equivalence cases"""
    print("🧮 Testing Mathematical Equivalence Function")
    print("=" * 50)
    
    test_cases = [
        # (student_answer, correct_answer, expected_result)
        ("0.5", "1/2", True),
        ("1/2", "0.5", True),
        ("0.5", "0.5", True),
        ("1/2", "1/2", True),
        ("0.333", "1/3", True),
        ("1/3", "0.333", True),
        ("2", "2", True),
        ("2.0", "2", True),
        ("4/2", "2", True),
        ("2", "4/2", True),
        ("0.25", "1/4", True),
        ("1/4", "0.25", True),
        ("0.75", "3/4", True),
        ("3/4", "0.75", True),
        ("1", "1.0", True),
        ("1.0", "1", True),
        ("0", "0.0", True),
        ("0.0", "0", True),
        # Negative cases
        ("0.5", "1/3", False),
        ("1/2", "1/3", False),
        ("2", "3", False),
        ("0.5", "0.6", False),
    ]
    
    all_passed = True
    for student_answer, correct_answer, expected in test_cases:
        result = is_mathematically_equivalent(student_answer, correct_answer)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"'{student_answer}' == '{correct_answer}': {result} {status}")
        if result != expected:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 All mathematical equivalence tests PASSED!")
    else:
        print("❌ Some tests FAILED!")
    
    return all_passed

if __name__ == "__main__":
    test_math_equivalence()
