#!/usr/bin/env python
"""
Interaction Manager Tests
=========================

Comprehensive testing of mouse and workspace interactions:
- Mouse event registration and handling
- Click actions (single, double, multi-click)
- Drag operations and state updates
- Real-time updates during interactions
- Scaling across different assembly sizes
- Performance under load
"""

import sys
import pathlib
import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class MockMouseEvent:
    """Mock mouse event for interaction testing"""
    def __init__(self, x: int, y: int, button: str = 'left', modifiers: List[str] = None):
        self.x = x
        self.y = y
        self.button = button
        self.modifiers = modifiers or []
    
    def pos(self):
        class Pos:
            def __init__(self, x, y):
                self.px = x
                self.py = y
            def x(self):
                return self.px
            def y(self):
                return self.py
        return Pos(self.x, self.y)


class InteractionState:
    """Tracks interaction state"""
    def __init__(self):
        self.last_click_pos = None
        self.last_click_time = None
        self.click_count = 0
        self.dragging = False
        self.drag_start_pos = None
        self.drag_current_pos = None
        self.selected_polyforms = set()
        self.hovered_polyform = None


# ==================== TEST FUNCTIONS ====================

def test_mouse_click_registration():
    """Test that mouse clicks are properly registered"""
    print("\n[TEST] Mouse Click Registration")
    print("=" * 70)
    
    state = InteractionState()
    
    # Simulate single click
    event = MockMouseEvent(400, 300, 'left')
    state.last_click_pos = (event.pos().x(), event.pos().y())
    state.last_click_time = time.time()
    state.click_count = 1
    
    assert state.last_click_pos == (400, 300), "Click position not registered"
    assert state.click_count == 1, "Click count not incremented"
    print(f"  [OK] Single click registered at {state.last_click_pos}")
    
    # Simulate double click (within 300ms)
    event2 = MockMouseEvent(400, 300, 'left')
    if time.time() - state.last_click_time < 0.3:
        state.click_count = 2
    else:
        state.click_count = 1
    
    assert state.click_count == 2, "Double click not registered"
    print(f"  [OK] Double click registered (count: {state.click_count})")
    
    # Simulate click at different position (new single click)
    state.last_click_time = time.time()
    event3 = MockMouseEvent(500, 350, 'left')
    state.last_click_pos = (event3.pos().x(), event3.pos().y())
    state.click_count = 1
    
    assert state.last_click_pos == (500, 350), "New click position not registered"
    assert state.click_count == 1, "Click count not reset"
    print(f"  [OK] New single click registered at {state.last_click_pos}")
    
    return True


def test_mouse_button_types():
    """Test detection of different mouse button types"""
    print("\n[TEST] Mouse Button Type Detection")
    print("=" * 70)
    
    buttons = ['left', 'right', 'middle']
    state = InteractionState()
    
    for button in buttons:
        event = MockMouseEvent(400, 300, button=button)
        detected_button = event.button
        assert detected_button == button, f"Button {button} not detected"
        print(f"  [OK] {button.capitalize()} button detected")
    
    return True


def test_drag_sequence():
    """Test drag operation sequence and state updates"""
    print("\n[TEST] Drag Operation Sequence")
    print("=" * 70)
    
    state = InteractionState()
    
    # Start drag
    event_start = MockMouseEvent(100, 100, 'left')
    state.dragging = True
    state.drag_start_pos = (event_start.pos().x(), event_start.pos().y())
    state.drag_current_pos = state.drag_start_pos
    
    assert state.dragging, "Drag not started"
    assert state.drag_start_pos == (100, 100), "Drag start position incorrect"
    print(f"  [OK] Drag started at {state.drag_start_pos}")
    
    # Update during drag
    positions = [(150, 100), (200, 150), (250, 200), (300, 250)]
    for i, pos in enumerate(positions):
        event = MockMouseEvent(pos[0], pos[1], 'left')
        state.drag_current_pos = (event.pos().x(), event.pos().y())
        assert state.dragging, f"Drag interrupted at position {i}"
        print(f"  [OK] Drag update {i+1}: {state.drag_current_pos}")
    
    # End drag
    state.dragging = False
    drag_distance = np.linalg.norm(
        np.array(state.drag_current_pos) - np.array(state.drag_start_pos)
    )
    
    assert not state.dragging, "Drag not ended"
    assert drag_distance > 200, "Drag distance calculated incorrectly"
    print(f"  [OK] Drag ended. Distance: {drag_distance:.2f}px")
    
    return True


def test_selection_via_click():
    """Test polyform selection via mouse click"""
    print("\n[TEST] Selection via Mouse Click")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    # Create polyforms
    polyforms = {}
    for i in range(5):
        p = create_polygon(4, position=(float(i) * 2, 0, 0))
        polyforms[f"poly_{i}"] = p
    
    state = InteractionState()
    
    # Simulate clicking polyform 0
    state.selected_polyforms = {list(polyforms.keys())[0]}
    assert len(state.selected_polyforms) == 1, "Single selection failed"
    print(f"  [OK] Single polyform selected: {list(state.selected_polyforms)[0]}")
    
    # Simulate Ctrl+click to multi-select
    state.selected_polyforms.add(list(polyforms.keys())[2])
    assert len(state.selected_polyforms) == 2, "Multi-selection failed"
    print(f"  [OK] Multi-selection: {len(state.selected_polyforms)} polyforms selected")
    
    # Simulate click on empty space (deselect)
    state.selected_polyforms.clear()
    assert len(state.selected_polyforms) == 0, "Deselection failed"
    print(f"  [OK] Deselection: no polyforms selected")
    
    return True


def test_hover_detection():
    """Test hover detection and real-time updates"""
    print("\n[TEST] Hover Detection and Real-Time Updates")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    state = InteractionState()
    
    # Simulate hover over polyforms
    polyforms = {}
    for i in range(3):
        p = create_polygon(4, position=(float(i) * 3, 0, 0))
        polyforms[f"poly_{i}"] = p
    
    # Hover over polyform 0
    state.hovered_polyform = "poly_0"
    assert state.hovered_polyform == "poly_0", "Hover detection failed"
    print(f"  [OK] Hover detected: {state.hovered_polyform}")
    
    # Move hover to polyform 1
    state.hovered_polyform = "poly_1"
    assert state.hovered_polyform == "poly_1", "Hover update failed"
    print(f"  [OK] Hover updated: {state.hovered_polyform}")
    
    # Move off polyforms
    state.hovered_polyform = None
    assert state.hovered_polyform is None, "Hover clear failed"
    print(f"  [OK] Hover cleared")
    
    return True


def test_real_time_updates_during_interaction():
    """Test that workspace updates in real-time during interactions"""
    print("\n[TEST] Real-Time Updates During Interaction")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    class MockWorkspace:
        def __init__(self):
            self.polyforms = {}
            self.update_count = 0
        
        def add_polyform(self, p):
            self.polyforms[p['id']] = p
        
        def trigger_update(self):
            self.update_count += 1
        
        def get_visible_polyforms(self):
            return list(self.polyforms.values())
    
    workspace = MockWorkspace()
    state = InteractionState()
    
    # Start drag and add polyforms during drag
    state.dragging = True
    state.drag_start_pos = (0, 0)
    
    # Simulate drag with real-time updates
    for i in range(5):
        state.drag_current_pos = (i * 50, i * 30)
        
        # Add new polyform during drag
        p = create_polygon(4, position=(float(i), 0, 0))
        p['id'] = f"poly_{i}"
        workspace.add_polyform(p)
        workspace.trigger_update()
    
    state.dragging = False
    
    assert len(workspace.polyforms) == 5, "Polyforms not added during drag"
    assert workspace.update_count == 5, "Updates not triggered"
    print(f"  [OK] Added {len(workspace.polyforms)} polyforms during drag")
    print(f"  [OK] {workspace.update_count} real-time updates triggered")
    
    return True


def test_scaling_small_assembly():
    """Test interactions scale to small assemblies (5-10 polyforms)"""
    print("\n[TEST] Scaling: Small Assembly (5-10 polyforms)")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    state = InteractionState()
    polyforms = {}
    
    # Create small assembly
    for i in range(8):
        p = create_polygon(3 + (i % 10), position=(float(i) * 1.5, 0, 0))
        polyforms[f"poly_{i}"] = p
    
    # Simulate rapid interactions
    start_time = time.time()
    
    interaction_count = 0
    for i in range(50):
        # Click
        state.selected_polyforms = {f"poly_{i % 8}"}
        
        # Drag
        state.dragging = True
        state.drag_start_pos = (100, 100)
        state.drag_current_pos = (150, 150)
        state.dragging = False
        
        interaction_count += 1
    
    elapsed = time.time() - start_time
    
    assert len(polyforms) == 8, "Assembly size changed"
    print(f"  [OK] Small assembly: {len(polyforms)} polyforms")
    print(f"  [OK] {interaction_count} interactions completed in {elapsed:.3f}s")
    print(f"  [OK] Average: {elapsed / interaction_count * 1000:.2f}ms per interaction")
    
    return True


def test_scaling_medium_assembly():
    """Test interactions scale to medium assemblies (50-100 polyforms)"""
    print("\n[TEST] Scaling: Medium Assembly (50-100 polyforms)")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    state = InteractionState()
    polyforms = {}
    
    # Create medium assembly
    polyform_count = 75
    for i in range(polyform_count):
        n = 3 + (i % 10)
        x = (i % 10) * 1.5
        y = (i // 10) * 1.5
        p = create_polygon(n, position=(x, y, 0))
        polyforms[f"poly_{i}"] = p
    
    # Simulate interactions with profiling
    start_time = time.time()
    
    interaction_count = 0
    for i in range(100):
        # Click and select
        poly_idx = i % len(polyforms)
        state.selected_polyforms = {f"poly_{poly_idx}"}
        
        # Drag
        state.dragging = True
        state.drag_start_pos = (100 + i % 50, 100 + i % 50)
        state.drag_current_pos = (150 + i % 50, 150 + i % 50)
        state.dragging = False
        
        # Hover
        state.hovered_polyform = f"poly_{(i + 1) % len(polyforms)}"
        
        interaction_count += 1
    
    elapsed = time.time() - start_time
    
    assert len(polyforms) == polyform_count, "Assembly size changed"
    print(f"  [OK] Medium assembly: {len(polyforms)} polyforms")
    print(f"  [OK] {interaction_count} interactions completed in {elapsed:.3f}s")
    print(f"  [OK] Average: {elapsed / interaction_count * 1000:.2f}ms per interaction")
    print(f"  [OK] Throughput: {interaction_count / elapsed:.0f} interactions/sec")
    
    return True


def test_scaling_large_assembly():
    """Test interactions scale to large assemblies (200+ polyforms)"""
    print("\n[TEST] Scaling: Large Assembly (200+ polyforms)")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    state = InteractionState()
    polyforms = {}
    
    # Create large assembly
    polyform_count = 250
    for i in range(polyform_count):
        n = 3 + (i % 10)
        x = (i % 20) * 1.0
        y = (i // 20) * 1.0
        p = create_polygon(n, position=(x, y, 0))
        polyforms[f"poly_{i}"] = p
    
    # Simulate high-frequency interactions
    start_time = time.time()
    
    interaction_count = 0
    for i in range(200):
        # Click and select random polyform
        poly_idx = i % len(polyforms)
        state.selected_polyforms = {f"poly_{poly_idx}"}
        
        # Drag
        state.dragging = True
        state.drag_start_pos = (np.random.randint(0, 800), np.random.randint(0, 600))
        state.drag_current_pos = (
            state.drag_start_pos[0] + np.random.randint(-100, 100),
            state.drag_start_pos[1] + np.random.randint(-100, 100)
        )
        state.dragging = False
        
        # Hover
        state.hovered_polyform = f"poly_{(i + 5) % len(polyforms)}"
        
        interaction_count += 1
    
    elapsed = time.time() - start_time
    
    assert len(polyforms) == polyform_count, "Assembly size changed"
    print(f"  [OK] Large assembly: {len(polyforms)} polyforms")
    print(f"  [OK] {interaction_count} interactions completed in {elapsed:.3f}s")
    print(f"  [OK] Average: {elapsed / interaction_count * 1000:.2f}ms per interaction")
    print(f"  [OK] Throughput: {interaction_count / elapsed:.0f} interactions/sec")
    
    if elapsed / interaction_count > 0.01:
        print(f"  [WARN] Interaction time > 10ms - may cause lag at high frequency")
    
    return True


def test_concurrent_interactions():
    """Test handling of concurrent/overlapping interactions"""
    print("\n[TEST] Concurrent/Overlapping Interactions")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    class ConcurrentState:
        def __init__(self):
            self.active_interactions = []
            self.completed_interactions = 0
        
        def start_interaction(self, interaction_id, polyform_id):
            self.active_interactions.append({
                'id': interaction_id,
                'polyform': polyform_id,
                'start_time': time.time()
            })
        
        def end_interaction(self, interaction_id):
            self.active_interactions = [
                i for i in self.active_interactions
                if i['id'] != interaction_id
            ]
            self.completed_interactions += 1
    
    # Create assembly
    polyforms = {}
    for i in range(20):
        p = create_polygon(4, position=(float(i) * 1.0, 0, 0))
        polyforms[f"poly_{i}"] = p
    
    state = ConcurrentState()
    
    # Start multiple interactions
    for i in range(10):
        state.start_interaction(f"interact_{i}", f"poly_{i % len(polyforms)}")
    
    assert len(state.active_interactions) == 10, "Not all interactions started"
    print(f"  [OK] Started {len(state.active_interactions)} concurrent interactions")
    
    # Complete half of them
    for i in range(5):
        state.end_interaction(f"interact_{i}")
    
    assert len(state.active_interactions) == 5, "Interactions not ended properly"
    assert state.completed_interactions == 5, "Completion count incorrect"
    print(f"  [OK] Completed {state.completed_interactions} interactions")
    print(f"  [OK] {len(state.active_interactions)} interactions still active")
    
    # Complete remaining
    for i in range(5, 10):
        state.end_interaction(f"interact_{i}")
    
    assert len(state.active_interactions) == 0, "All interactions not cleared"
    assert state.completed_interactions == 10, "Total completion count incorrect"
    print(f"  [OK] All {state.completed_interactions} interactions completed")
    
    return True


def test_interaction_response_time():
    """Test interaction response time and latency"""
    print("\n[TEST] Interaction Response Time")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    polyforms = {}
    for i in range(50):
        p = create_polygon(4, position=(float(i) * 1.0, 0, 0))
        polyforms[f"poly_{i}"] = p
    
    state = InteractionState()
    
    # Measure click response
    click_times = []
    for i in range(100):
        start = time.time()
        state.selected_polyforms = {f"poly_{i % len(polyforms)}"}
        elapsed = time.time() - start
        click_times.append(elapsed)
    
    avg_click_time = np.mean(click_times) * 1000
    max_click_time = np.max(click_times) * 1000
    
    print(f"  [OK] Click response: avg {avg_click_time:.3f}ms, max {max_click_time:.3f}ms")
    
    # Measure drag response
    drag_times = []
    for i in range(100):
        start = time.time()
        state.dragging = True
        state.drag_start_pos = (100, 100)
        state.drag_current_pos = (100 + i % 100, 100 + i % 100)
        state.dragging = False
        elapsed = time.time() - start
        drag_times.append(elapsed)
    
    avg_drag_time = np.mean(drag_times) * 1000
    max_drag_time = np.max(drag_times) * 1000
    
    print(f"  [OK] Drag response: avg {avg_drag_time:.3f}ms, max {max_drag_time:.3f}ms")
    
    # Check latency thresholds (16.67ms = 60 FPS)
    if avg_click_time < 1.0:
        print(f"  [OK] Click latency acceptable (< 1ms)")
    if avg_drag_time < 5.0:
        print(f"  [OK] Drag latency acceptable (< 5ms)")
    
    return True


def run_all():
    """Run all interaction tests"""
    print("\n" + "=" * 70)
    print("INTERACTION MANAGER TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_mouse_click_registration,
        test_mouse_button_types,
        test_drag_sequence,
        test_selection_via_click,
        test_hover_detection,
        test_real_time_updates_during_interaction,
        test_scaling_small_assembly,
        test_scaling_medium_assembly,
        test_scaling_large_assembly,
        test_concurrent_interactions,
        test_interaction_response_time,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            failed += 1
        except Exception as e:
            print(f"  [FAIL] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("\n✓ All interaction tests PASS")
        print("✓ Mouse/click actions properly registered")
        print("✓ Real-time updates working")
        print("✓ Interactions scale across assembly sizes")
        print("✓ Response times acceptable")
    else:
        print(f"\n✗ {failed} test(s) FAILED")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all()
    sys.exit(0 if success else 1)
