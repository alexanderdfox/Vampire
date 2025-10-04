#!/usr/bin/env python3
"""
Vampire Process Movie Generator

This script creates a movie that visually represents the behavior of the vampire.cpp program:
- Processes spawn children and immediately die
- Each child becomes the new parent
- Creates a continuous chain of process creation and destruction
- Visualized as a vampire that consumes itself and regenerates

The script now embeds the actual vampire process logic using multiprocessing.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle
import random
import time
import multiprocessing
import os
import signal
import sys
import threading
import queue

def vampire_process_logic(shared_dict, process_counter, stop_flag, depth=0):
    """
    The actual vampire process logic - embedded from vampire.cpp
    Creates child processes and immediately kills itself
    """
    try:
        # Prevent infinite recursion by limiting depth
        if depth > 20:  # Limit to prevent system overload
            return
            
        while not stop_flag.value:
            # Small delay to prevent overwhelming the system
            time.sleep(0.01)
            
            # Create a child process
            child_process = multiprocessing.Process(
                target=vampire_process_logic, 
                args=(shared_dict, process_counter, stop_flag, depth + 1)
            )
            child_process.start()
            
            # Store process info in shared dictionary
            event_id = process_counter.value
            process_counter.value += 1
            
            shared_dict[event_id] = {
                'action': 'spawn',
                'parent_pid': os.getpid(),
                'child_pid': child_process.pid,
                'timestamp': time.time(),
                'depth': depth
            }
            
            # Immediately kill this process (like the C++ version)
            os.kill(os.getpid(), signal.SIGKILL)
            
    except Exception as e:
        event_id = process_counter.value
        process_counter.value += 1
        shared_dict[event_id] = {
            'action': 'error',
            'pid': os.getpid(),
            'error': str(e),
            'timestamp': time.time(),
            'depth': depth
        }

class VampireProcessMovie:
    def __init__(self, duration=10, fps=30):
        self.duration = duration
        self.fps = fps
        self.total_frames = duration * fps
        
        # Real process tracking using shared memory
        self.manager = multiprocessing.Manager()
        self.shared_dict = self.manager.dict()
        self.process_counter = multiprocessing.Value('i', 0)
        self.stop_flag = multiprocessing.Value('b', False)
        self.vampire_process = None
        self.process_events = []
        self.frame_count = 0
        
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
        self.ax.set_title('Vampire Process: Real Process Logic Embedded', fontsize=16, fontweight='bold')
        self.ax.set_xlabel('Time →', fontsize=12)
        self.ax.set_ylabel('Process Space', fontsize=12)
        
        # Add background grid
        self.ax.grid(True, alpha=0.3)
        
        # Add explanatory text
        self.ax.text(0.5, 7.5, 'Each red circle represents a REAL process', fontsize=10, 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
        self.ax.text(0.5, 7.0, 'Processes spawn children and immediately die', fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
        self.ax.text(0.5, 6.5, 'Real vampire.cpp logic embedded in Python', fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
    
    def start_vampire_process(self):
        """Start the vampire process logic"""
        if self.vampire_process is None:
            self.vampire_process = multiprocessing.Process(
                target=vampire_process_logic, 
                args=(self.shared_dict, self.process_counter, self.stop_flag, 0)
            )
            self.vampire_process.start()
            print(f"Started vampire process with PID: {self.vampire_process.pid}")
    
    def stop_vampire_process(self):
        """Stop the vampire process logic"""
        if self.vampire_process:
            self.stop_flag.value = True
            self.vampire_process.terminate()
            self.vampire_process.join(timeout=1)
            if self.vampire_process.is_alive():
                self.vampire_process.kill()
            self.vampire_process = None
            print("Stopped vampire process")
    
    def update_process_events(self):
        """Update process events from shared memory"""
        try:
            # Get all new events from shared dictionary
            for event_id, event in self.shared_dict.items():
                if event_id not in [e.get('event_id') for e in self.process_events]:
                    event['event_id'] = event_id
                    self.process_events.append(event)
                    
                    # Assign position to new processes
                    if event['action'] == 'spawn':
                        child_pid = event['child_pid']
                        if child_pid not in self.process_positions:
                            self.process_positions[child_pid] = (
                                random.uniform(1, 9),
                                random.uniform(1, 6)
                            )
        except Exception as e:
            print(f"Error updating process events: {e}")
        
        # Keep only recent events (last 100)
        if len(self.process_events) > 100:
            self.process_events = self.process_events[-100:]
    
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
        active_pids = set()
        
        # Process recent events to determine which processes are active
        for event in self.process_events[-50:]:  # Look at last 50 events
            if event['action'] == 'spawn':
                child_pid = event['child_pid']
                active_pids.add(child_pid)
                
                # Draw the spawned process
                if child_pid in self.process_positions:
                    x, y = self.process_positions[child_pid]
                    circle = Circle((x, y), 0.4, 
                                  color=self.colors['spawned'], alpha=0.8, zorder=10)
                    self.ax.add_patch(circle)
                    
                    # Add process ID and depth
                    depth = event.get('depth', 0)
                    self.ax.text(x, y, f"{child_pid}\n(d:{depth})", 
                                ha='center', va='center', fontsize=7, fontweight='bold',
                                color='white')
        
        # Draw process connections (parent-child relationships)
        for event in self.process_events[-20:]:  # Last 20 events for connections
            if event['action'] == 'spawn':
                parent_pid = event['parent_pid']
                child_pid = event['child_pid']
                
                if (parent_pid in self.process_positions and 
                    child_pid in self.process_positions):
                    px, py = self.process_positions[parent_pid]
                    cx, cy = self.process_positions[child_pid]
                    
                    # Draw arrow from parent to child
                    self.ax.annotate('', xy=(cx, cy), xytext=(px, py),
                                   arrowprops=dict(arrowstyle='->', color='red', alpha=0.6, lw=1))
        
        # Add frame info
        self.ax.text(9.5, 7.5, f'Frame: {self.frame_count}', fontsize=10,
                    ha='right', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        self.ax.text(9.5, 7.0, f'Active Processes: {len(active_pids)}', fontsize=10,
                    ha='right', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        self.ax.text(9.5, 6.5, f'Total Events: {len(self.process_events)}', fontsize=10,
                    ha='right', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        # Add title
        self.ax.set_title('Vampire Process: Real Process Logic Embedded', fontsize=16, fontweight='bold')
        self.ax.set_xlabel('Time →', fontsize=12)
        self.ax.set_ylabel('Process Space', fontsize=12)
    
    def animate(self, frame):
        """Animation function called for each frame"""
        self.frame_count = frame
        
        # Start vampire process on first frame
        if frame == 0:
            self.start_vampire_process()
        
        # Update process events from the queue
        self.update_process_events()
        
        # Draw everything
        self.draw_processes()
        
        return []
    
    def generate_movie(self, filename='vampire_process_movie.mp4'):
        """Generate the movie"""
        print(f"Generating vampire process movie with embedded logic...")
        print(f"Duration: {self.duration} seconds")
        print(f"FPS: {self.fps}")
        print(f"Total frames: {self.total_frames}")
        
        try:
            # Create animation
            anim = animation.FuncAnimation(
                self.fig, 
                self.animate, 
                frames=self.total_frames,
                interval=1000/self.fps,  # milliseconds per frame
                blit=False,
                repeat=False
            )
            
            # Save as MP4
            print(f"Saving movie as {filename}...")
            Writer = animation.writers['ffmpeg']
            writer = Writer(fps=self.fps, metadata=dict(artist='Vampire Process Simulator'), bitrate=1800)
            
            anim.save(filename, writer=writer)
            print(f"Movie saved as {filename}")
            
        finally:
            # Always clean up processes
            self.stop_vampire_process()
            # Clean up manager
            if hasattr(self, 'manager'):
                self.manager.shutdown()
        
        return filename

def main():
    """Main function to generate the vampire process movie"""
    print("Vampire Process Movie Generator with Embedded Logic")
    print("=" * 50)
    print("This script creates a movie showing REAL vampire process behavior:")
    print("- Uses actual multiprocessing to spawn child processes")
    print("- Each process immediately kills itself after spawning")
    print("- Creates a continuous cycle of real process death and rebirth")
    print("- Visualizes actual process IDs and relationships")
    print()
    
    # Create movie generator
    movie_gen = VampireProcessMovie(duration=10, fps=24)
    
    # Generate the movie
    filename = movie_gen.generate_movie('vampire_process_movie.mp4')
    
    print(f"\nMovie generation complete!")
    print(f"File saved as: {filename}")
    print("\nTo view the movie, you can use:")
    print(f"  - VLC: vlc {filename}")
    print(f"  - QuickTime: open {filename}")
    print(f"  - Or any other video player")
    print("\nNote: This movie shows REAL process spawning and death!")

if __name__ == "__main__":
    main()

