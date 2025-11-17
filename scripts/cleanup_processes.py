#!/usr/bin/env python3
"""
Cleanup existing processes before launching
"""

import subprocess
import sys
import psutil
from pathlib import Path

def kill_processes_on_ports(ports):
    """Kill processes using specified ports"""
    killed = []
    for port in ports:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                connections = proc.connections()
                for conn in connections:
                    if conn.laddr.port == port:
                        print(f"[KILL] Killing process {proc.info['name']} (PID {proc.info['pid']}) on port {port}")
                        proc.kill()
                        killed.append((proc.info['pid'], proc.info['name'], port))
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, psutil.AccessDenied):
                pass
    return killed

def kill_browser_processes():
    """Kill common browser processes"""
    browser_names = ['chrome', 'msedge', 'firefox', 'brave']
    killed = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            if any(browser in name for browser in browser_names):
                print(f"[KILL] Killing browser process {proc.info['name']} (PID {proc.info['pid']})")
                proc.kill()
                killed.append((proc.info['pid'], proc.info['name']))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return killed

def main():
    print("=" * 70)
    print("Cleaning up existing processes...")
    print("=" * 70)
    
    # Kill processes on ports 8000 and 5173
    print("\n[INFO] Killing processes on ports 8000 and 5173...")
    killed_ports = kill_processes_on_ports([8000, 5173])
    
    # Optionally kill browser processes (commented out by default)
    # print("\n[INFO] Killing browser processes...")
    # killed_browsers = kill_browser_processes()
    
    print("\n[OK] Cleanup complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())

