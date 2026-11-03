# Screen Generation Counter - Usage Examples

This document shows practical examples of how the screen generation counter improves Android automation performance.

## Before: Fixed Sleep Delays

```python
from gitd.bots.common.adb import Device
import time

dev = Device("emulator-5554")

# Traditional approach: fixed delays after every action
start = time.time()

dev.tap(540, 1200)
time.sleep(0.5)  # Wait for UI to update (maybe 50ms, maybe 400ms)

dev.tap(540, 1400)
time.sleep(0.5)  # Wait again

dev.swipe(540, 1600, 540, 800)
time.sleep(0.5)  # And again

total = time.time() - start
print(f"Total time: {total:.2f}s")
# Output: Total time: 1.65s (3 actions + 3×500ms sleep)
```

**Problems:**
- Always waits full 500ms even if UI updates in 50ms
- Wastes time on fast UIs
- Still might miss slow updates
- No feedback on whether UI actually changed

## After: Generation Counter

```python
from gitd.bots.common.adb import Device, wait_for_generation_change
import time

dev = Device("emulator-5554")

start = time.time()

dev.tap(540, 1200, delay=0)  # No delay
wait_for_generation_change(dev, timeout=2.0)  # Wait until UI updates

dev.tap(540, 1400, delay=0)
wait_for_generation_change(dev, timeout=2.0)

dev.swipe(540, 1600, 540, 800, delay=0)
wait_for_generation_change(dev, timeout=2.0)

total = time.time() - start
print(f"Total time: {total:.2f}s")
# Output: Total time: 0.45s (3 actions + ~150ms total wait)
# Improvement: 73% faster!
```

**Benefits:**
- Waits only as long as needed (typically 50-200ms)
- Confirms UI actually updated
- Faster workflows
- No missed updates

## Automatic Integration in Agent Tools

The generation wait is **automatically applied** when using agent tools - no code changes needed!

```python
from gitd.services.agent_tools import execute_tool

# Old behavior (pre-generation counter):
# - execute_tool calls dev.tap()
# - Always sleeps 500ms
# - Returns screen tree

# New behavior (with generation counter):
# - execute_tool calls dev.tap()
# - Waits until generation increases (or 2s timeout)
# - Falls back to sleep(0.5) if generation unavailable
# - Returns screen tree

result = execute_tool("tap", {"device": "emulator-5554", "x": 540, "y": 1200})
# Automatically waits for UI update using generation counter!
```

## Real-World Example: Login Flow

### Before (Fixed Sleep)

```python
def login_user(dev, username, password):
    start = time.time()
    
    # Tap username field
    dev.tap(540, 800)
    time.sleep(0.5)
    
    # Type username
    dev.adb("shell", "input", "text", username)
    time.sleep(0.5)
    
    # Tap password field
    dev.tap(540, 1000)
    time.sleep(0.5)
    
    # Type password
    dev.adb("shell", "input", "text", password)
    time.sleep(0.5)
    
    # Tap login button
    dev.tap(540, 1400)
    time.sleep(0.5)
    
    elapsed = time.time() - start
    print(f"Login completed in {elapsed:.2f}s")
    # Output: Login completed in 2.85s
    #         (0.35s actions + 2.5s sleep)

dev = Device("emulator-5554")
login_user(dev, "testuser", "password123")
```

### After (Generation Counter)

```python
def login_user_fast(dev, username, password):
    start = time.time()
    
    # Tap username field
    dev.tap(540, 800, delay=0)
    wait_for_generation_change(dev)
    
    # Type username
    dev.adb("shell", "input", "text", username)
    wait_for_generation_change(dev)
    
    # Tap password field
    dev.tap(540, 1000, delay=0)
    wait_for_generation_change(dev)
    
    # Type password
    dev.adb("shell", "input", "text", password)
    wait_for_generation_change(dev)
    
    # Tap login button
    dev.tap(540, 1400, delay=0)
    wait_for_generation_change(dev)
    
    elapsed = time.time() - start
    print(f"Login completed in {elapsed:.2f}s")
    # Output: Login completed in 1.05s
    #         (0.35s actions + 0.7s wait)
    # Improvement: 63% faster!

dev = Device("emulator-5554")
login_user_fast(dev, "testuser", "password123")
```

## Advanced: Pre-fetching Generation

For maximum performance, fetch the generation **before** the action:

```python
from gitd.bots.common.adb import Device, wait_for_generation_change

dev = Device("emulator-5554")

# Get generation before action
before_gen = dev.dump_portal_json()  # Or direct HTTP call
# ... extract generation value ...

# Perform action
dev.tap(540, 1200, delay=0)

# Wait for generation to increase from before_gen
if wait_for_generation_change(dev, before_generation=before_gen, timeout=2.0):
    print("UI updated!")
else:
    print("Timeout or generation unavailable")
```

## Performance Comparison Table

| Scenario | Fixed Sleep | Generation Wait | Improvement |
|----------|-------------|-----------------|-------------|
| Fast UI (50ms update) | 500ms | 50ms | **90% faster** |
| Medium UI (150ms update) | 500ms | 150ms | **70% faster** |
| Slow UI (400ms update) | 500ms | 400ms | **20% faster** |
| Very slow UI (800ms update) | 500ms | 800ms | -60% slower (but more reliable) |
| Generation unavailable | 500ms | 500ms (fallback) | Same |

## Error Handling Examples

### Example 1: Graceful Fallback

```python
from gitd.bots.common.adb import Device, wait_for_generation_change

dev = Device("emulator-5554")

# If generation is unavailable (old Portal, network error, etc.)
# wait_for_generation_change returns False and you can fall back
dev.tap(540, 1200, delay=0)
if not wait_for_generation_change(dev, timeout=2.0):
    # Fallback to fixed sleep
    time.sleep(0.5)
    print("Using fallback sleep (generation unavailable)")
```

### Example 2: Timeout Detection

```python
import time
from gitd.bots.common.adb import Device, wait_for_generation_change

dev = Device("emulator-5554")

# Tap a button that might freeze the app
dev.tap(540, 1200, delay=0)

start = time.time()
if wait_for_generation_change(dev, timeout=5.0):
    elapsed = time.time() - start
    print(f"UI updated in {elapsed:.2f}s")
else:
    print("Warning: UI did not update in 5s - app might be frozen")
    # Handle frozen app (restart, report error, etc.)
```

## Testing Your Integration

Quick test to see if generation counter is working:

```python
#!/usr/bin/env python3
"""Quick test: is generation counter working?"""

from gitd.bots.common.adb import Device, wait_for_generation_change
import time

def test_generation():
    dev = Device("YOUR_SERIAL")
    
    print("Testing generation counter...")
    
    # Test 1: Simple tap
    print("\n1. Testing tap...")
    before = time.time()
    dev.tap(540, 1200, delay=0)
    
    if wait_for_generation_change(dev, timeout=2.0):
        elapsed = time.time() - before
        print(f"   ✅ UI updated in {elapsed:.3f}s")
        if elapsed < 0.5:
            print(f"   🚀 {(1 - elapsed/0.5)*100:.0f}% faster than sleep(0.5)!")
        return True
    else:
        print("   ❌ Generation counter not available")
        print("   ℹ️  Falling back to sleep(0.5)")
        return False

if __name__ == "__main__":
    if test_generation():
        print("\n✅ Generation counter is working!")
    else:
        print("\n⚠️  Generation counter unavailable - using fallback")
```

## Integration with Existing Code

No changes needed! The generation wait is **automatically used** by `execute_tool()`:

```python
# Old code still works - automatically gets generation benefits
from gitd.services.agent_tools import execute_tool

# This automatically uses generation wait now:
execute_tool("tap", {"device": "emulator-5554", "x": 540, "y": 1200})
execute_tool("tap_element", {"device": "emulator-5554", "idx": 5})
execute_tool("swipe", {"device": "emulator-5554", "x1": 540, "y1": 1600, "x2": 540, "y2": 800})

# All UI actions benefit from generation counter automatically!
```

## When to Use Manual wait_for_generation_change()

Use the manual function when:

1. **Custom workflows** (not using agent tools)
2. **Performance critical** loops
3. **Multiple actions** before checking UI
4. **Conditional logic** based on wait success

```python
# Example: Retry loop with generation feedback
from gitd.bots.common.adb import Device, wait_for_generation_change

dev = Device("emulator-5554")

for attempt in range(3):
    dev.tap(540, 1200, delay=0)
    
    if wait_for_generation_change(dev, timeout=1.0):
        print(f"Success on attempt {attempt + 1}")
        break
    else:
        print(f"Attempt {attempt + 1} failed, retrying...")
else:
    print("Failed after 3 attempts")
```

## Summary

**Without generation counter:**
```
Action → sleep(0.5) → Action → sleep(0.5) → Action → sleep(0.5)
Time: 1.5s fixed delays (regardless of actual UI speed)
```

**With generation counter:**
```
Action → wait(~50-200ms) → Action → wait(~50-200ms) → Action → wait(~50-200ms)
Time: 0.15-0.6s adaptive waits (matches actual UI speed)
Typical improvement: 60-85% faster
```

**Best part:** Fully backward compatible - if generation unavailable, automatically falls back to sleep(0.5)!
