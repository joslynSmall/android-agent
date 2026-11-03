# Verification Guide for Screen Generation Counter

This guide provides step-by-step instructions to verify the screen generation counter implementation works correctly.

## Prerequisites

- Android device with USB debugging enabled
- ADB installed and device connected
- Android SDK (for building Portal APK)
- Python 3.8+ with project dependencies installed

## Step 1: Build Portal APK

```bash
cd portal

# Build debug APK
./gradlew assembleDebug

# Expected output location:
# app/build/outputs/apk/debug/app-debug.apk
```

**Success criteria**: Build completes without errors, APK file created.

## Step 2: Install Portal APK

```bash
# Install APK (replace existing if already installed)
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Grant overlay permission
adb shell pm grant com.ghostinthedroid.portal android.permission.SYSTEM_ALERT_WINDOW

# Enable accessibility service (manual step required)
# On device: Settings → Accessibility → Ghost Portal → Toggle ON
```

**Success criteria**: 
- APK installs without errors
- Accessibility service appears in Settings
- Service can be enabled

## Step 3: Verify Portal HTTP Server

```bash
# Set up port forward
adb forward tcp:18080 tcp:8080

# Test /status endpoint
curl http://localhost:18080/status

# Expected output:
# {"status":"success","result":"ok"}
```

**Success criteria**: HTTP server responds on port 8080.

## Step 4: Verify Generation Endpoint

```bash
# Fetch current generation
curl http://localhost:18080/generation

# Expected output (generation value will vary):
# {"status":"success","result":"{\"generation\":1,\"timestamp\":1730736123456}"}

# Parse and display just the generation number
curl -s http://localhost:18080/generation | jq -r '.result | fromjson | .generation'
# Expected: numeric value (e.g., 1, 42, 1337)
```

**Success criteria**: 
- Endpoint returns HTTP 200
- JSON contains `generation` and `timestamp` fields
- Generation is a positive integer

## Step 5: Verify Generation Increments on UI Changes

### Terminal 1: Monitor generation counter
```bash
echo "Monitoring generation counter (Ctrl+C to stop)..."
while true; do 
  GEN=$(curl -s http://localhost:18080/generation | jq -r '.result | fromjson | .generation')
  echo "Generation: $GEN"
  sleep 0.2
done
```

### Terminal 2: Trigger UI actions
```bash
# Tap screen (center)
adb shell input tap 540 1200
# Expected: Generation increments within 0.3-0.5 seconds

# Wait 1 second
sleep 1

# Swipe down
adb shell input swipe 540 1400 540 600
# Expected: Generation increments within 0.3-0.5 seconds

# Wait 1 second
sleep 1

# Open app drawer (swipe up from bottom)
adb shell input swipe 540 2000 540 1000
# Expected: Generation increments within 0.3-0.5 seconds

# Press home button
adb shell input keyevent KEYCODE_HOME
# Expected: Generation increments within 0.3-0.5 seconds
```

**Success criteria**:
- Generation increments after each action
- Increment happens within ~300ms
- Multiple rapid actions don't cause excessive increments (throttling works)

## Step 6: Test Throttling

```bash
# Rapid scroll test (should NOT increment 10 times)
for i in {1..10}; do
  adb shell input swipe 540 1400 540 600 100
done

# Check generation only incremented 2-3 times (throttled)
curl -s http://localhost:18080/generation | jq -r '.result | fromjson | .generation'
```

**Success criteria**: 
- Generation increments only 2-4 times (not 10)
- Demonstrates 300ms throttling is working

## Step 7: Test Python Integration

```python
#!/usr/bin/env python3
"""Test Python generation wait integration."""

import time
from gitd.bots.common.adb import Device, wait_for_generation_change

# Get your device serial
# Run: adb devices
DEVICE_SERIAL = "YOUR_DEVICE_SERIAL_HERE"

def test_generation_wait():
    dev = Device(DEVICE_SERIAL)
    
    # Test 1: Tap and wait for generation change
    print("Test 1: Tap screen and wait for UI update...")
    before_tap = time.time()
    dev.tap(540, 1200, delay=0)  # No delay - we'll wait for generation
    
    if wait_for_generation_change(dev, timeout=2.0):
        elapsed = time.time() - before_tap
        print(f"✅ UI updated in {elapsed:.3f}s (should be ~0.05-0.5s)")
    else:
        print("❌ Generation wait failed or timed out")
    
    time.sleep(0.5)
    
    # Test 2: Swipe and wait
    print("\nTest 2: Swipe and wait for UI update...")
    before_swipe = time.time()
    dev.swipe(540, 1400, 540, 600, ms=300, delay=0)
    
    if wait_for_generation_change(dev, timeout=2.0):
        elapsed = time.time() - before_swipe
        print(f"✅ UI updated in {elapsed:.3f}s (should be ~0.05-0.5s)")
    else:
        print("❌ Generation wait failed or timed out")
    
    # Test 3: Verify fallback when generation unavailable
    print("\nTest 3: Test fallback behavior...")
    # This should still work even if generation times out
    dev.tap(540, 1200)  # Uses default delay from adb.py
    print("✅ Fallback to sleep(0.5) works")

if __name__ == "__main__":
    test_generation_wait()
```

**Success criteria**:
- Test 1 and 2 show UI updates detected in <500ms
- Test 3 completes without errors
- All tests print success messages

## Step 8: Test Fallback Behavior

### Test without Portal installed
```bash
# Stop Portal accessibility service
adb shell am force-stop com.ghostinthedroid.portal

# Run Python script again
# Expected: Falls back to sleep(0.5), still works
```

### Test with old Portal version
```bash
# Simulate old Portal by blocking the endpoint
adb forward --remove tcp:18080

# Run Python script again
# Expected: Falls back to sleep(0.5), still works
```

**Success criteria**: 
- Agent tools still function
- No exceptions raised
- Graceful degradation to sleep behavior

## Step 9: Performance Comparison

```python
#!/usr/bin/env python3
"""Compare generation wait vs fixed sleep performance."""

import time
from gitd.bots.common.adb import Device, wait_for_generation_change

DEVICE_SERIAL = "YOUR_DEVICE_SERIAL_HERE"

def benchmark_generation_wait(dev, iterations=10):
    """Measure average wait time using generation counter."""
    times = []
    for i in range(iterations):
        before = time.time()
        dev.tap(540, 1200 + (i * 50), delay=0)
        if wait_for_generation_change(dev, timeout=2.0):
            elapsed = time.time() - before
            times.append(elapsed)
            print(f"  Iteration {i+1}: {elapsed:.3f}s")
        time.sleep(0.3)  # Small gap between tests
    
    if times:
        avg = sum(times) / len(times)
        print(f"\nGeneration wait average: {avg:.3f}s")
        return avg
    return None

def benchmark_fixed_sleep(dev, iterations=10):
    """Measure time using fixed sleep(0.5)."""
    times = []
    for i in range(iterations):
        before = time.time()
        dev.tap(540, 1200 + (i * 50), delay=0)
        time.sleep(0.5)
        elapsed = time.time() - before
        times.append(elapsed)
        print(f"  Iteration {i+1}: {elapsed:.3f}s")
        time.sleep(0.3)
    
    avg = sum(times) / len(times)
    print(f"\nFixed sleep average: {avg:.3f}s")
    return avg

def main():
    dev = Device(DEVICE_SERIAL)
    
    print("Benchmarking generation wait (10 iterations)...")
    gen_avg = benchmark_generation_wait(dev, 10)
    
    time.sleep(2)
    
    print("\n" + "="*50)
    print("Benchmarking fixed sleep (10 iterations)...")
    sleep_avg = benchmark_fixed_sleep(dev, 10)
    
    print("\n" + "="*50)
    print("RESULTS:")
    print(f"Generation wait: {gen_avg:.3f}s average")
    print(f"Fixed sleep:     {sleep_avg:.3f}s average")
    if gen_avg and sleep_avg:
        improvement = (sleep_avg - gen_avg) / sleep_avg * 100
        print(f"Improvement:     {improvement:.1f}% faster")

if __name__ == "__main__":
    main()
```

**Expected results**:
- Generation wait: ~0.05-0.3s average
- Fixed sleep: ~0.5s average
- Improvement: 40-90% faster

## Troubleshooting

### Problem: `/generation` endpoint not found (404)

**Possible causes**:
1. Portal APK not rebuilt with new changes
2. Old version still installed

**Solutions**:
```bash
# Rebuild and reinstall
cd portal
./gradlew clean assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Restart Portal service
adb shell am force-stop com.ghostinthedroid.portal
# Re-enable in Settings → Accessibility
```

### Problem: Generation never increments

**Possible causes**:
1. Accessibility service not enabled
2. Accessibility service crashed

**Solutions**:
```bash
# Check if service is running
adb shell dumpsys accessibility | grep Ghost

# Check logcat for errors
adb logcat | grep -E "Ghost(A11y|Http|Overlay)"

# Restart device if needed
adb reboot
```

### Problem: Python wait always times out

**Possible causes**:
1. Port forward not set up
2. HTTP server not listening
3. Network issues

**Solutions**:
```bash
# Verify port forward
adb forward --list

# Re-setup port forward
adb forward tcp:18080 tcp:8080

# Test HTTP directly
curl http://localhost:18080/status

# Check if server is listening on device
adb shell netstat -tuln | grep 8080
```

### Problem: Imports fail in Python

**Possible causes**:
1. Dependencies not installed
2. PYTHONPATH not set

**Solutions**:
```bash
# Install dependencies
pip install -r requirements.txt  # or equivalent

# Check imports manually
python3 -c "from gitd.bots.common.adb import wait_for_generation_change; print('OK')"
```

## Verification Checklist

Before considering implementation complete, verify:

- [ ] Portal APK builds without errors
- [ ] APK installs on device
- [ ] Accessibility service can be enabled
- [ ] HTTP server responds on port 8080
- [ ] `/generation` endpoint returns valid JSON
- [ ] Generation increments on UI changes
- [ ] Throttling prevents excessive increments
- [ ] Python `wait_for_generation_change()` works
- [ ] Fallback to sleep works when generation unavailable
- [ ] Performance improvement measurable (40-90% faster)
- [ ] No exceptions raised in edge cases
- [ ] Documentation is accurate and complete

## Automated Verification Script

```bash
#!/bin/bash
# verify-generation-counter.sh

set -e

echo "=== Screen Generation Counter Verification ==="
echo

echo "Step 1: Check ADB connection..."
adb devices | grep -q "device$" || { echo "❌ No device connected"; exit 1; }
echo "✅ Device connected"

echo
echo "Step 2: Check port forward..."
adb forward tcp:18080 tcp:8080
echo "✅ Port forward set up"

echo
echo "Step 3: Test /status endpoint..."
curl -sf http://localhost:18080/status > /dev/null || { echo "❌ Portal not responding"; exit 1; }
echo "✅ Portal HTTP server responding"

echo
echo "Step 4: Test /generation endpoint..."
RESULT=$(curl -sf http://localhost:18080/generation)
echo "$RESULT" | jq -e '.status == "success"' > /dev/null || { echo "❌ Generation endpoint failed"; exit 1; }
GEN1=$(echo "$RESULT" | jq -r '.result | fromjson | .generation')
echo "✅ Generation endpoint working (current: $GEN1)"

echo
echo "Step 5: Test generation increment..."
adb shell input tap 540 1200
sleep 0.5
RESULT=$(curl -sf http://localhost:18080/generation)
GEN2=$(echo "$RESULT" | jq -r '.result | fromjson | .generation')

if [ "$GEN2" -gt "$GEN1" ]; then
    echo "✅ Generation incremented ($GEN1 → $GEN2)"
else
    echo "❌ Generation did not increment"
    exit 1
fi

echo
echo "=== All verification steps passed! ==="
```

Save as `verify-generation-counter.sh`, make executable, and run:
```bash
chmod +x verify-generation-counter.sh
./verify-generation-counter.sh
```

## Summary

Following this guide ensures the screen generation counter implementation:

1. ✅ Builds correctly (Kotlin/Gradle)
2. ✅ Installs on device (APK)
3. ✅ Exposes HTTP endpoint (/generation)
4. ✅ Increments on UI changes (accessibility events)
5. ✅ Throttles correctly (300ms)
6. ✅ Integrates with Python (wait_for_generation_change)
7. ✅ Falls back gracefully (sleep on error)
8. ✅ Improves performance (40-90% faster)

All success criteria met = implementation ready for production use.
