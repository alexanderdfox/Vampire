# Vampire

## Belt-Driven Circuit Simulator - Standalone HTML Version

This is a complete standalone version of the Belt-Driven Self-Referential Circuit Simulator that runs entirely in your web browser without requiring any Python backend.

## Features

### 🎛️ **Complete Circuit Simulation**
- **Power Sources**: DC voltage (0-24V), AC voltage (0-12V), AC frequency (1-1000Hz)
- **Motors**: Top and bottom motor RPM settings (0-10000) with real-time feedback
- **Belt Systems**: Three belt systems (TOP_BELT, BOTTOM_BELT, CROSS_BELT) with efficiency and ratio controls
- **Transistors**: Q1, Q2, Q3 with gain settings (1-500) and enable/disable controls
- **Noise System**: Comprehensive noise modeling with thermal, mechanical, and belt vibration effects

### 🔄 **Real-Time Dynamics**
- **Regenerative Feedback**: Motors drive each other through mechanical belt coupling
- **Self-Referential Behavior**: TOP_BELT and BOTTOM_BELT create self-coupling effects
- **Cross-Stage Coupling**: CROSS_BELT enables power sharing between top and bottom stages
- **Belt Dynamics**: Automatic slip, tension, and efficiency calculations

### 🔊 **Advanced Noise Modeling**
- **Thermal Noise**: Johnson-Nyquist noise simulation
- **Mechanical Noise**: Motor vibration and belt slip effects
- **Quantization Noise**: Digital system noise simulation
- **Real-Time Adjustable**: All noise parameters can be controlled in real-time

## How to Use

### Option 1: Direct File Access
1. Simply open `vampire.html` in any modern web browser
2. The simulation starts automatically
3. All controls work in real-time

### Option 2: Local Web Server (Recommended)
```bash
# Navigate to the directory containing the HTML file
cd /path/to/vampire.html

# Start a simple HTTP server
python3 -m http.server 8080

# Open in browser: http://localhost:8080/vampire.html
```

## Interface Overview

### 📊 **Dashboard Sections**

1. **Noise Status & Voltages**: Real-time display of noise settings and voltage levels
2. **Motor Status**: Live RPM, torque, and current readings for both motors
3. **Power Sources**: Controls for DC/AC voltage and frequency settings
4. **Noise Controls**: Fine-tune all noise parameters and enable/disable noise
5. **Belt Systems**: Efficiency sliders and gear ratio controls for all belt systems
6. **Transistors**: Gain controls and enable/disable toggles for each transistor
7. **System Control**: Master enable/disable controls for components and belt systems
8. **Live Data Tables**: Real-time belt and transistor status tables

### 🎮 **Control Types**

- **Range Sliders**: For efficiency and noise level adjustments
- **Number Inputs**: For precise voltage, frequency, and gain settings
- **Checkboxes**: For enable/disable toggles
- **Real-Time Updates**: All changes apply immediately

## Technical Implementation

### 🧠 **Circuit Simulation Engine**
- **Component-Based Architecture**: Each circuit element is modeled as an object
- **Real-Time Calculations**: Voltage, current, and mechanical calculations update continuously
- **Belt Coupling Physics**: Mechanical coupling between motors through belt systems
- **Noise Injection**: Multiple noise sources applied to different component types

### 🔧 **Key Algorithms**

1. **Voltage Distribution**: DC and AC voltage calculations with noise injection
2. **Motor Dynamics**: RPM and torque calculations based on electrical input and mechanical coupling
3. **Belt System Physics**: Efficiency, slip, and tension calculations based on load
4. **Noise Generation**: Gaussian random noise with component-specific characteristics

### 📈 **Real-Time Performance**
- **60 FPS Updates**: Smooth real-time display updates
- **Efficient Algorithms**: Optimized for browser performance
- **Responsive Controls**: Immediate parameter updates without lag

## Circuit Topology

The simulator implements a belt-driven self-referential circuit with:

- **Power Stage**: DC and AC voltage sources with transformer coupling
- **Motor Stage**: Top and bottom motors with electrical connections to transistors
- **Control Stage**: NPN and PNP transistors controlling motor operation
- **Feedback Stage**: Three belt systems creating regenerative feedback loops

### Belt System Architecture
- **TOP_BELT**: Self-coupling for top motor (regenerative feedback)
- **BOTTOM_BELT**: Self-coupling for bottom motor (regenerative feedback)  
- **CROSS_BELT**: Cross-stage coupling between top and bottom motors

## Browser Compatibility

- ✅ **Chrome/Chromium**: Full support
- ✅ **Firefox**: Full support
- ✅ **Safari**: Full support
- ✅ **Edge**: Full support
- ✅ **Mobile Browsers**: Responsive design works on mobile devices

## No Dependencies

This standalone version requires:
- ❌ No Python installation
- ❌ No external libraries
- ❌ No server setup
- ❌ No network connection (after initial load)
- ✅ Just a modern web browser

## Educational Value

Perfect for:
- **Circuit Analysis**: Understanding regenerative feedback systems
- **Control Systems**: Learning about mechanical-electrical coupling
- **Signal Processing**: Exploring noise effects in electronic systems
- **Physics Education**: Demonstrating belt dynamics and mechanical coupling
- **Engineering Simulation**: Real-time parameter adjustment and analysis

The simulator provides a comprehensive platform for exploring the fascinating behavior of self-referential mechanical-electrical systems with realistic noise modeling and real-time interactive controls.

