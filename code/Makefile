# Makefile for battery_vampire programs
# Infinite loop binary representation of 1/101

CC = gcc
CXX = g++
SWIFT = swift
PYTHON = python3

# Executable names
C_EXE = battery_vampire_c
CPP_EXE = battery_vampire_cpp
SWIFT_EXE = battery_vampire_swift

# Source files
C_SRC = battery_vampire.c
CPP_SRC = battery_vampire.cpp
SWIFT_SRC = battery_vampire.swift
PYTHON_SRC = battery_vampire.py
HC_SRC = battery_vampire.HC

# Compiler flags
CFLAGS = -Wall -Wextra -std=c11
CXXFLAGS = -Wall -Wextra -std=c++11
SWIFTFLAGS = -O

.PHONY: all clean run-c run-cpp run-swift run-python run-hc run-all

# Default target: build all compilable programs
all: $(C_EXE) $(CPP_EXE) $(SWIFT_EXE)
	@echo "All battery_vampire programs built successfully!"

# Build C version
$(C_EXE): $(C_SRC)
	$(CC) $(CFLAGS) -o $(C_EXE) $(C_SRC)
	@echo "Built C version: $(C_EXE)"

# Build C++ version
$(CPP_EXE): $(CPP_SRC)
	$(CXX) $(CXXFLAGS) -o $(CPP_EXE) $(CPP_SRC)
	@echo "Built C++ version: $(CPP_EXE)"

# Build Swift version
$(SWIFT_EXE): $(SWIFT_SRC)
	$(SWIFT) $(SWIFTFLAGS) -o $(SWIFT_EXE) $(SWIFT_SRC)
	@echo "Built Swift version: $(SWIFT_EXE)"

# Run targets (use Ctrl+C to stop)
run-c: $(C_EXE)
	@echo "Running C version..."
	./$(C_EXE)

run-cpp: $(CPP_EXE)
	@echo "Running C++ version..."
	./$(CPP_EXE)

run-swift: $(SWIFT_EXE)
	@echo "Running Swift version..."
	./$(SWIFT_EXE)

run-python: $(PYTHON_SRC)
	@echo "Running Python version..."
	$(PYTHON) $(PYTHON_SRC)

run-hc: $(HC_SRC)
	@echo "HolyC version needs to be run in TempleOS:"
	@echo "  Type: battery_vampire.HC"
	@echo "  Or: Load(\"battery_vampire.HC\");"

# Run all versions (not recommended - they're infinite loops!)
run-all:
	@echo "Warning: This will try to run all versions simultaneously!"
	@echo "Use Ctrl+C to stop. Running in background..."
	@echo "Building all first..."
	@make all
	@echo "Starting all programs..."
	@./$(C_EXE) & ./$(CPP_EXE) & ./$(SWIFT_EXE) & $(PYTHON) $(PYTHON_SRC) &

# Clean compiled binaries
clean:
	rm -f $(C_EXE) $(CPP_EXE) $(SWIFT_EXE)
	rm -f *.o *.dSYM
	@echo "Cleaned compiled binaries"

# Help target
help:
	@echo "battery_vampire Makefile"
	@echo "========================"
	@echo "Available targets:"
	@echo "  all         - Build all compilable versions (C, C++, Swift)"
	@echo "  run-c       - Build and run C version"
	@echo "  run-cpp     - Build and run C++ version"
	@echo "  run-swift   - Build and run Swift version"
	@echo "  run-python  - Run Python version"
	@echo "  run-hc      - Show instructions for HolyC version"
	@echo "  clean       - Remove compiled binaries"
	@echo "  help        - Show this help message"
