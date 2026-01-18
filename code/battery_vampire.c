/*
 * Infinite loop to calculate binary representation of 1/101
 */

#include <stdio.h>
#include <stdbool.h>

void binary_fraction(int numerator, int denominator) {
    int rem = numerator;  // Start with numerator 1
    int i = 0;
    
    printf("Binary representation of %d/%d: 0.", numerator, denominator);
    fflush(stdout);
    
    while (true) {
        rem = rem * 2;
        if (rem >= denominator) {
            printf("1");
            rem = rem - denominator;
        } else {
            printf("0");
        }
        
        // Optional: add some spacing for readability
        i++;
        if (i % 4 == 0) {
            printf(" ");
        }
        if (i % 80 == 0) {
            printf("\n");
        }
        
        fflush(stdout);
    }
}

int main() {
    binary_fraction(1, 101);
    return 0;
}
