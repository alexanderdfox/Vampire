// Infinite loop to calculate binary representation of 1/101
U0 BinaryFraction(U64 n, U64 d)
{
    U64 rem, i;
    
    // Calculate 1/101 in binary
    rem = 1; // Start with numerator 1
    Print("Binary representation of 1/101: 0.");
    
    i = 0;
    while (TRUE) {
        rem = rem * 2;
        if (rem >= d) {
            Print("1");
            rem = rem - d;
        } else {
            Print("0");
        }
        
        // Optional: add some spacing for readability
        i++;
        if (i % 4 == 0)
            Print(" ");
        if (i % 80 == 0)
            Print("\n");
        
        // Small delay to make it visible (optional)
        // Sleep(1);
    }
}

// Main entry point
BinaryFraction(1, 101);
