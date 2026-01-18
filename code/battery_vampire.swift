#!/usr/bin/env swift
/*
 * Infinite loop to calculate binary representation of 1/101
 */

import Darwin

func binaryFraction(numerator: Int = 1, denominator: Int = 101) {
    var rem = numerator  // Start with numerator 1
    print("Binary representation of \(numerator)/\(denominator): 0.", terminator: "")
    
    var i = 0
    while true {
        rem = rem * 2
        if rem >= denominator {
            print("1", terminator: "")
            rem = rem - denominator
        } else {
            print("0", terminator: "")
        }
        
        // Optional: add some spacing for readability
        i += 1
        if i % 4 == 0 {
            print(" ", terminator: "")
        }
        if i % 80 == 0 {
            print("\n", terminator: "")
        }
        
        // Force output flush
        fflush(stdout)
    }
}

// Main entry point
binaryFraction(numerator: 1, denominator: 101)
