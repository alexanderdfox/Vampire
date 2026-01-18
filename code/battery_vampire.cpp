/*
 * Infinite loop to calculate binary representation of 1/101
 */

#include <iostream>
#include <cstdio>

void binary_fraction(int numerator, int denominator) {
    int rem = numerator;  // Start with numerator 1
    int i = 0;
    
    std::cout << "Binary representation of " << numerator << "/" << denominator << ": 0.";
    std::cout.flush();
    
    while (true) {
        rem = rem * 2;
        if (rem >= denominator) {
            std::cout << "1";
            rem = rem - denominator;
        } else {
            std::cout << "0";
        }
        
        // Optional: add some spacing for readability
        i++;
        if (i % 4 == 0) {
            std::cout << " ";
        }
        if (i % 80 == 0) {
            std::cout << "\n";
        }
        
        std::cout.flush();
    }
}

int main() {
    binary_fraction(1, 101);
    return 0;
}
