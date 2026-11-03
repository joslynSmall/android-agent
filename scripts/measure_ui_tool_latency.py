#!/usr/bin/env python3
"""Measure UI tool action latency with instrumentation.

Usage:
    python scripts/measure_ui_tool_latency.py <device_serial> [--tool press_home] [--iterations 5]

Example:
    python scripts/measure_ui_tool_latency.py emulator-5554
    python scripts/measure_ui_tool_latency.py 192.168.1.100:5555 --tool swipe --iterations 10

This script instruments execute_tool to measure the time spent in:
- The actual action execution (_execute_tool_inner)
- XML dumps (via dump_xml calls)
- get_screen_tree processing
- get_interactive_elements processing

Use this to verify the optimization that shares one XML dump between
get_screen_tree and _a11y_diff_suffix.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def measure_tool_execution(device: str, tool: str = "press_home", iterations: int = 5):
    """Measure latency of a UI tool with detailed timing breakdowns."""
    from gitd.services import agent_tools
    from gitd.bots.common.device import get_device

    # Patch dump_xml to measure its duration
    original_dump_xml = None
    dump_xml_times = []

    def instrumented_dump_xml(self):
        t0 = time.time()
        result = original_dump_xml(self)
        duration = (time.time() - t0) * 1000
        dump_xml_times.append(duration)
        print(f"  [dump_xml] {duration:.1f}ms")
        return result

    # Get device and patch
    try:
        dev = get_device(device)
        original_dump_xml = dev.dump_xml
        dev.dump_xml = lambda: instrumented_dump_xml(dev)
    except Exception as e:
        print(f"Failed to get device {device}: {e}")
        return

    # Prepare tool args
    tool_args = {"device": device}
    if tool == "swipe":
        tool_args.update({"x1": 540, "y1": 1400, "x2": 540, "y2": 600})
    elif tool == "tap":
        tool_args.update({"x": 540, "y": 1000})

    print(f"\n=== Measuring {tool} on {device} ({iterations} iterations) ===\n")

    total_times = []
    for i in range(iterations):
        dump_xml_times.clear()
        print(f"Iteration {i + 1}/{iterations}:")

        t_start = time.time()
        try:
            result = agent_tools.execute_tool(tool, tool_args)
            duration_ms = (time.time() - t_start) * 1000

            print(f"  [total] {duration_ms:.1f}ms")
            print(f"  [dump_xml calls] {len(dump_xml_times)}")
            if dump_xml_times:
                print(f"  [dump_xml avg] {sum(dump_xml_times) / len(dump_xml_times):.1f}ms")
            print(f"  [result preview] {result[:100]}...")
            total_times.append(duration_ms)
        except Exception as e:
            print(f"  [ERROR] {e}")
            continue

        if i < iterations - 1:
            time.sleep(1.0)  # Brief pause between iterations

    # Summary
    if total_times:
        avg_total = sum(total_times) / len(total_times)
        min_total = min(total_times)
        max_total = max(total_times)

        print(f"\n=== Summary ===")
        print(f"Tool: {tool}")
        print(f"Device: {device}")
        print(f"Iterations: {len(total_times)}")
        print(f"Average total: {avg_total:.1f}ms")
        print(f"Min total: {min_total:.1f}ms")
        print(f"Max total: {max_total:.1f}ms")
        print(f"\nExpected improvement from optimization:")
        print(f"  Before: 2 dump_xml calls per action = ~2 × (60-450ms) = ~120-900ms overhead")
        print(f"  After: 1 dump_xml call per action = ~60-450ms overhead")
        print(f"  Savings: ~60-450ms per UI action (depending on Portal HTTP health)")


def main():
    parser = argparse.ArgumentParser(description="Measure UI tool latency")
    parser.add_argument("device", help="Device serial (e.g., emulator-5554, 192.168.1.100:5555)")
    parser.add_argument("--tool", default="press_home", choices=["press_home", "press_back", "swipe", "tap"],
                        help="UI tool to test (default: press_home)")
    parser.add_argument("--iterations", type=int, default=5, help="Number of test iterations (default: 5)")
    args = parser.parse_args()

    measure_tool_execution(args.device, args.tool, args.iterations)


if __name__ == "__main__":
    main()
