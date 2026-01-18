#!/usr/bin/env python3
"""
Infinite loop to calculate binary representation of 1/101
"""

def binary_fraction(numerator=1, denominator=101):
    """
    Calculate and print binary representation of numerator/denominator
    This will run infinitely, outputting binary digits
    """
    import sys
    
    rem = numerator  # Start with numerator 1
    sys.stdout.write(f"Binary representation of {numerator}/{denominator}: 0.")
    sys.stdout.flush()
    
    i = 0
    while True:
        rem = rem * 2
        if rem >= denominator:
            sys.stdout.write("1")
            rem = rem - denominator
        else:
            sys.stdout.write("0")
        
        # Optional: add some spacing for readability
        i += 1
        if i % 4 == 0:
            sys.stdout.write(" ")
        if i % 80 == 0:
            sys.stdout.write("\n")
        
        sys.stdout.flush()
        
        # Optional: add a small delay to make output visible
        # import time
        # time.sleep(0.01)


if __name__ == "__main__":
    binary_fraction(1, 101)
