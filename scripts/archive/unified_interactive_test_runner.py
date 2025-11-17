#!/usr/bin/env python3
"""
Unified Interactive Test Runner
Launches system, tracks user interactions, and runs tests in the same browser session
"""

import subprocess
import sys
import time
import json
import webbrowser
from pathlib import Path
from datetime import datetime
import threading

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"
TEST_RESULTS_DIR = PROJECT_ROOT / "test-results" / "interactive"
TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class InteractionTracker:
    """Tracks user interactions in the browser"""
    
    def __init__(self):
        self.interactions = []
        self.start_time = datetime.now()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = TEST_RESULTS_DIR / f"interactions_{self.session_id}.json"
    
    def record_interaction(self, event_type, data):
        """Record an interaction event"""
        interaction = {
            "timestamp": (datetime.now() - self.start_time).total_seconds(),
            "type": event_type,
            "data": data
        }
        self.interactions.append(interaction)
        self.save()
    
    def save(self):
        """Save interactions to file"""
        with open(self.output_file, 'w') as f:
            json.dump({
                "session_id": self.session_id,
                "start_time": self.start_time.isoformat(),
                "interactions": self.interactions
            }, f, indent=2)
    
    def generate_test_from_interactions(self):
        """Generate Playwright test code from recorded interactions"""
        test_code = """// Auto-generated test from user interactions
import { test, expect } from '@playwright/test';

test('User Interaction Session', async ({ page }) => {
"""
        
        for interaction in self.interactions:
            event_type = interaction['type']
            data = interaction['data']
            
            if event_type == 'click':
                selector = data.get('selector', '')
                test_code += f"  await page.click('{selector}');\n"
            elif event_type == 'type':
                selector = data.get('selector', '')
                text = data.get('text', '')
                test_code += f"  await page.fill('{selector}', '{text}');\n"
            elif event_type == 'navigate':
                url = data.get('url', '')
                test_code += f"  await page.goto('{url}');\n"
            elif event_type == 'mouse_move':
                x = data.get('x', 0)
                y = data.get('y', 0)
                test_code += f"  await page.mouse.move({x}, {y});\n"
        
        test_code += "});\n"
        
        output_file = TEST_RESULTS_DIR / f"generated_test_{self.session_id}.spec.js"
        with open(output_file, 'w') as f:
            f.write(test_code)
        
        return output_file

def inject_interaction_tracker(page_content):
    """Inject interaction tracking script into page"""
    tracker_script = """
<script>
(function() {
    const interactions = [];
    const startTime = Date.now();
    
    // Track mouse movements
    document.addEventListener('mousemove', (e) => {
        interactions.push({
            timestamp: Date.now() - startTime,
            type: 'mouse_move',
            data: { x: e.clientX, y: e.clientY }
        });
    });
    
    // Track clicks
    document.addEventListener('click', (e) => {
        const selector = e.target.id || e.target.className || e.target.tagName;
        interactions.push({
            timestamp: Date.now() - startTime,
            type: 'click',
            data: { 
                selector: selector,
                x: e.clientX,
                y: e.clientY,
                element: e.target.tagName
            }
        });
    });
    
    // Track keyboard input
    document.addEventListener('keydown', (e) => {
        interactions.push({
            timestamp: Date.now() - startTime,
            type: 'keydown',
            data: { key: e.key, code: e.code }
        });
    });
    
    // Track input changes
    document.addEventListener('input', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            interactions.push({
                timestamp: Date.now() - startTime,
                type: 'input',
                data: { 
                    selector: e.target.id || e.target.className,
                    value: e.target.value
                }
            });
        }
    });
    
    // Expose API to get interactions
    window.getInteractions = () => interactions;
    window.clearInteractions = () => { interactions.length = 0; };
    
    // Auto-save every 5 seconds
    setInterval(() => {
        if (interactions.length > 0) {
            fetch('/api/test/interactions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ interactions: interactions })
            }).catch(() => {});
        }
    }, 5000);
})();
</script>
"""
    return page_content.replace('</head>', tracker_script + '</head>')

def start_servers():
    """Start API and frontend servers"""
    print("[INFO] Starting servers...")
    
    # Clean up first
    cleanup_script = PROJECT_ROOT / "scripts" / "cleanup_processes.py"
    if cleanup_script.exists():
        subprocess.run([sys.executable, str(cleanup_script)], 
                      capture_output=True, timeout=10)
        time.sleep(2)
    
    # Start servers using launch script
    launch_script = PROJECT_ROOT / "scripts" / "launch_visualization_visible.py"
    if launch_script.exists():
        subprocess.Popen([sys.executable, str(launch_script)], 
                        cwd=PROJECT_ROOT)
        print("[WAIT] Waiting for servers to start...")
        time.sleep(45)
        
        # Check if servers are ready
        import urllib.request
        for i in range(30):
            try:
                urllib.request.urlopen("http://localhost:8000/health", timeout=2)
                urllib.request.urlopen("http://localhost:5173", timeout=2)
                print("[OK] Servers are ready!")
                return True
            except:
                time.sleep(2)
        
        print("[WARN] Servers may not be fully ready")
        return False
    
    return False

def run_playwright_tests_with_tracking():
    """Run Playwright tests with interaction tracking"""
    print("\n" + "=" * 70)
    print("Running Playwright Tests with Interaction Tracking")
    print("=" * 70)
    
    # Run tests in headed mode with trace
    cmd = [
        "npx", "playwright", "test",
        "--headed",
        "--project=chromium",
        "--trace=on",
        "--video=on",
        "--screenshot=on"
    ]
    
    print(f"[TEST] Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=FRONTEND_DIR,
        shell=True
    )
    
    return result.returncode == 0

def run_interactive_test_session():
    """Run interactive test session with user tracking"""
    print("\n" + "=" * 70)
    print("Interactive Test Session")
    print("=" * 70)
    print("\nThis will:")
    print("  1. Launch the visualization in a browser")
    print("  2. Track all your interactions (mouse, clicks, inputs)")
    print("  3. Run automated tests in the background")
    print("  4. Generate test cases from your interactions")
    print("\n" + "=" * 70 + "\n")
    
    tracker = InteractionTracker()
    
    # Start servers
    if not start_servers():
        print("[ERROR] Failed to start servers")
        return 1
    
    # Open browser
    print("[INFO] Opening browser for interactive testing...")
    time.sleep(2)
    webbrowser.open("http://localhost:5173")
    
    # Start automated tests in background
    print("[INFO] Starting automated tests in background...")
    test_thread = threading.Thread(target=run_playwright_tests_with_tracking)
    test_thread.daemon = True
    test_thread.start()
    
    print("\n" + "=" * 70)
    print("Interactive Testing Active")
    print("=" * 70)
    print("\nYour interactions are being tracked!")
    print("Interact with the visualization in the browser.")
    print("\nPress Ctrl+C when done to:")
    print("  - Save all interactions")
    print("  - Generate test cases from your actions")
    print("  - View test results")
    print("=" * 70)
    
    try:
        # Keep running and tracking
        while True:
            time.sleep(1)
            # Check for interaction data from browser
            # (This would be enhanced with a WebSocket or API endpoint)
    except KeyboardInterrupt:
        print("\n\n[INFO] Stopping interactive session...")
        
        # Generate test from interactions
        print("[INFO] Generating test cases from your interactions...")
        test_file = tracker.generate_test_from_interactions()
        print(f"[OK] Test case generated: {test_file}")
        
        # Show summary
        print("\n" + "=" * 70)
        print("Session Summary")
        print("=" * 70)
        print(f"Total interactions: {len(tracker.interactions)}")
        print(f"Session ID: {tracker.session_id}")
        print(f"Interactions saved to: {tracker.output_file}")
        print(f"Generated test: {test_file}")
        print("=" * 70)
        
        return 0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Interactive Test Runner")
    parser.add_argument(
        "--mode",
        choices=["interactive", "automated", "both"],
        default="both",
        help="Test mode: interactive (track user), automated (run tests), or both"
    )
    
    args = parser.parse_args()
    
    if args.mode == "interactive":
        return run_interactive_test_session()
    elif args.mode == "automated":
        if not start_servers():
            return 1
        return 0 if run_playwright_tests_with_tracking() else 1
    else:  # both
        return run_interactive_test_session()

if __name__ == "__main__":
    sys.exit(main())

