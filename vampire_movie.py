#!/usr/bin/env python3
"""
Vampire Process Single Image Generator

This script creates a single image that visually represents the behavior of the vampire.cpp program:
- Processes spawn children and immediately die
- Each child becomes the new parent
- Creates a continuous chain of process creation and destruction
- Visualized as a vampire that consumes itself and regenerates

Uses threading for better compatibility and generates a single static image.
Shows vampire process behavior captured in one comprehensive visualization.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import random
import time
import threading
import os
import signal
import sys
import queue
from collections import deque

def vampire_thread_logic(event_queue, stop_event):
    """
    Simulated vampire process logic using threading
    Creates child threads and immediately terminates itself
    """
    try:
        while not stop_event.is_set():
            # Small delay to prevent overwhelming the system
            time.sleep(0.01)
            
            # Create a child thread
            child_thread = threading.Thread(
                target=vampire_thread_logic, 
                args=(event_queue, stop_event)
            )
            child_thread.start()
            
            # Send process info to the queue
            event_queue.put({
                'action': 'spawn',
                'parent_id': threading.get_ident(),
                'child_id': child_thread.ident,
                'timestamp': time.time()
            })
            
            # Immediately terminate this thread (simulating the kill signal)
            return  # Exit the thread
            
    except Exception as e:
        event_queue.put({
            'action': 'error',
            'thread_id': threading.get_ident(),
            'error': str(e),
            'timestamp': time.time()
        })

class VampireProcessImageGenerator:
    def __init__(self, capture_duration=3.0):
        self.capture_duration = capture_duration
        
        # Thread-based process tracking
        self.event_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.vampire_thread = None
        self.process_events = deque(maxlen=100)  # Keep last 100 events
        self.thread_counter = 0
        
        # Visual parameters
        self.max_processes = 50
        self.process_positions = {}  # pid -> (x, y)
        
        # Colors for different process states
        self.colors = {
            'spawned': '#FF0000',      # Red for newly spawned processes
            'dying': '#FF6666',        # Light red for dying processes
            'active': '#CC0000'        # Dark red for active processes
        }
        
        # Setup the figure
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 8)
        self.ax.set_aspect('equal')
        self.ax.set_title('Vampire Process: Single Image Capture', fontsize=16, fontweight='bold')
        self.ax.set_xlabel('Process Space', fontsize=12)
        self.ax.set_ylabel('Process Space', fontsize=12)
        
        # Add background grid
        self.ax.grid(True, alpha=0.3)
        
        # Add explanatory text
        self.ax.text(0.5, 7.5, 'Each red circle represents a REAL thread', fontsize=10, 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
        self.ax.text(0.5, 7.0, 'Threads spawn children and immediately die', fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
        self.ax.text(0.5, 6.5, 'Vampire.cpp logic captured in single image', fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
    
    def start_vampire_thread(self):
        """Start the vampire thread logic"""
        if self.vampire_thread is None:
            self.vampire_thread = threading.Thread(
                target=vampire_thread_logic, 
                args=(self.event_queue, self.stop_event)
            )
            self.vampire_thread.start()
            print(f"Started vampire thread with ID: {self.vampire_thread.ident}")
    
    def stop_vampire_thread(self):
        """Stop the vampire thread logic"""
        if self.vampire_thread:
            self.stop_event.set()
            self.vampire_thread.join(timeout=1)
            self.vampire_thread = None
            print("Stopped vampire thread")
    
    def update_process_events(self):
        """Update process events from the queue"""
        try:
            # Get all new events from queue
            while True:
                try:
                    event = self.event_queue.get_nowait()
                    self.process_events.append(event)
                    
                    # Assign position to new processes
                    if event['action'] == 'spawn':
                        child_id = event['child_id']
                        if child_id not in self.process_positions:
                            self.process_positions[child_id] = (
                                random.uniform(1, 9),
                                random.uniform(1, 6)
                            )
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error updating process events: {e}")
    
    def draw_processes(self):
        """Draw all processes on the canvas"""
        self.ax.clear()
        
        # Redraw background
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 8)
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        
        # Draw processes based on real events
        current_time = time.time()
        active_ids = set()
        
        # Process recent events to determine which processes are active
        for event in list(self.process_events)[-50:]:  # Look at last 50 events
            if event['action'] == 'spawn':
                child_id = event['child_id']
                active_ids.add(child_id)
                
                # Draw the spawned process
                if child_id in self.process_positions:
                    x, y = self.process_positions[child_id]
                    circle = Circle((x, y), 0.4, 
                                  color=self.colors['spawned'], alpha=0.8, zorder=10)
                    self.ax.add_patch(circle)
                    
                    # Add thread ID
                    self.ax.text(x, y, str(child_id), 
                                ha='center', va='center', fontsize=8, fontweight='bold',
                                color='white')
        
        # Draw process connections (parent-child relationships)
        for event in list(self.process_events)[-20:]:  # Last 20 events for connections
            if event['action'] == 'spawn':
                parent_id = event['parent_id']
                child_id = event['child_id']
                
                if (parent_id in self.process_positions and 
                    child_id in self.process_positions):
                    px, py = self.process_positions[parent_id]
                    cx, cy = self.process_positions[child_id]
                    
                    # Draw arrow from parent to child
                    self.ax.annotate('', xy=(cx, cy), xytext=(px, py),
                                   arrowprops=dict(arrowstyle='->', color='red', alpha=0.6, lw=1))
        
        # Add frame info
        self.ax.text(9.5, 7.5, f'Active Threads: {len(active_ids)}', fontsize=10,
                    ha='right', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        self.ax.text(9.5, 7.0, f'Total Events: {len(self.process_events)}', fontsize=10,
                    ha='right', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        # Add title
        self.ax.set_title('Vampire Process: Single Image Capture', fontsize=16, fontweight='bold')
        self.ax.set_xlabel('Process Space', fontsize=12)
        self.ax.set_ylabel('Process Space', fontsize=12)
    
    def generate_image(self):
        """Generate a single image showing current process state"""
        # Update process events from the queue
        self.update_process_events()
        
        # Draw everything
        self.draw_processes()
        
        return self.fig
    
    def generate_single_image(self, filename='vampire_process.png'):
        """Generate a single image showing vampire process behavior"""
        print(f"Generating vampire process image with embedded logic...")
        print(f"Capture duration: {self.capture_duration} seconds")
        
        try:
            # Start vampire thread
            self.start_vampire_thread()
            
            # Let the process run for the capture duration
            print("Capturing process activity...")
            time.sleep(self.capture_duration)
            
            # Generate the final image
            print("Generating image...")
            fig = self.generate_image()
            
            # Save the image
            fig.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)  # Close to free memory
            
            print(f"Image saved as: {filename}")
            
        finally:
            # Always clean up threads
            self.stop_vampire_thread()
        
        return filename

def main():
    """Main function to generate the vampire process image"""
    print("Vampire Process Single Image Generator")
    print("=" * 45)
    print("This script creates a single image showing vampire process behavior:")
    print("- Uses threading to simulate child process spawning")
    print("- Each thread immediately terminates after spawning")
    print("- Creates a continuous cycle of thread death and rebirth")
    print("- Visualizes actual thread IDs and relationships")
    print("- Generates a single static image for easy viewing and sharing")
    print()
    
    # Create image generator
    image_gen = VampireProcessImageGenerator(capture_duration=3.0)
    
    # Generate the single image
    filename = image_gen.generate_single_image('vampire_process.png')
    
    print(f"\nImage generation complete!")
    print(f"Image saved as: {filename}")
    print(f"\nTo view the image, you can:")
    print(f"  - Open with Preview: open {filename}")
    print(f"  - Open with any image viewer")
    print(f"  - Share the image file")
    print("\nNote: This image shows REAL thread spawning and death!")

if __name__ == "__main__":
    main()

