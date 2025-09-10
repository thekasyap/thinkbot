#!/usr/bin/env python3
"""
Test fraction equivalence directly
"""

from fractions import Fraction
from decimal import Decimal, InvalidOperation

def is_mathematically_equivalent(answer1: str, answer2: str) -> bool:
    """Check if two answers are mathematically equivalent."""
    # First try exact string match (case insensitive)
    if answer1.strip().lower() == answer2.strip().lower():
        return True
    
    # Try to convert both to numbers and compare
    try:
        # Handle fractions like "1/2", "1/3", etc.
        if '/' in answer1 and '/' in answer2:
            frac1 = Fraction(answer1)
            frac2 = Fraction(answer2)
            return frac1 == frac2
        
        # Handle decimal numbers
        try:
            dec1 = Decimal(answer1)
            dec2 = Decimal(answer2)
            return dec1 == dec2
        except (InvalidOperation, ValueError):
            pass
        
        # Try converting one to fraction and one to decimal
        if '/' in answer1:
            frac1 = Fraction(answer1)
            try:
                dec2 = Decimal(answer2)
                return float(frac1) == float(dec2)
            except (InvalidOperation, ValueError):
                pass
        elif '/' in answer2:
            frac2 = Fraction(answer2)
            try:
                dec1 = Decimal(answer1)
                return float(dec1) == float(frac2)
            except (InvalidOperation, ValueError):
                pass
        
        # Try converting both to float for comparison
        try:
            float1 = float(answer1)
            float2 = float(answer2)
            return abs(float1 - float2) < 1e-10  # Use small epsilon for floating point comparison
        except (ValueError, TypeError):
            pass
            
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    
    return False

# Test cases
test_cases = [
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

print("🧮 Testing Mathematical Equivalence Function")
print("=" * 50)

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
