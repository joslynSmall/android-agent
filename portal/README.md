# Ghost Portal — Android APK

Ghost Portal (`com.ghostinthedroid.portal`) is an Android accessibility service that provides:
- Fast UI tree access via HTTP endpoints and content provider
- Screen capture and WebRTC streaming
- Numbered element overlay for visual debugging
- **Screen generation counter** for efficient UI update detection

## Building

### Prerequisites
- Android SDK (API 30+)
- JDK 17+
- Gradle (wrapper included)

### Build Debug APK

```bash
cd portal
./gradlew assembleDebug
```

Output: `app/build/outputs/apk/debug/app-debug.apk`

### Install to Device

```bash
# Install APK
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Grant required permissions
adb shell pm grant com.ghostinthedroid.portal android.permission.SYSTEM_ALERT_WINDOW

# Enable accessibility service (manual step required on device)
# Settings → Accessibility → Ghost Portal → Turn on
```

## Screen Generation Counter

The generation counter is a monotonic value that increments on relevant accessibility events (window state change, content change, scroll). This allows the Python host to wait for UI updates instead of using fixed `sleep(0.5)` delays.

### How it works

1. **Portal APK**: `ScreenGenerationCounter` increments on accessibility events with 300ms throttling
2. **HTTP endpoint**: `GET /generation` returns `{"generation": <long>, "timestamp": <millis>}`
3. **Python host**: `wait_for_generation_change()` polls until generation increases (or timeout)

### Verification Steps

#### 1. Check generation endpoint is available

```bash
# Set up port forward
adb forward tcp:18080 tcp:8080

# Fetch current generation
curl http://localhost:18080/generation
```

Expected output:
```json
{
  "status": "success",
  "result": "{\"generation\":42,\"timestamp\":1730736123456}"
}
```

#### 2. Verify generation increments on UI changes

```bash
# Terminal 1: Monitor generation counter
while true; do 
  curl -s http://localhost:18080/generation | jq -r '.result | fromjson | .generation'
  sleep 0.2
done

# Terminal 2: Trigger UI changes
adb shell input tap 540 1200   # Generation should increment within 300ms
adb shell input swipe 540 1400 540 600   # Generation should increment
```

You should see the generation value increase after each action.

#### 3. Test Python integration

```python
from gitd.bots.common.adb import Device, wait_for_generation_change

dev = Device("YOUR_SERIAL")

# Perform an action and wait for UI to update
dev.tap(540, 1200)
if wait_for_generation_change(dev, timeout=2.0):
    print("UI updated!")
else:
    print("Timeout or generation unavailable (fallback to sleep)")
```

### Troubleshooting

**Generation endpoint returns error:**
- Ensure Portal accessibility service is enabled
- Check `adb logcat | grep Ghost` for errors
- Verify port forward: `adb forward --list`

**Generation never increments:**
- Check accessibility service is running: `adb shell dumpsys accessibility`
- Test manual UI changes trigger events
- Look for throttling: generation won't increment faster than 300ms

**Python wait always times out:**
- Verify endpoint is accessible: `curl http://localhost:18080/generation`
- Check device serial matches
- Try with fixed sleep as fallback

## Content Provider Fallback

If HTTP endpoint is unavailable, the Python code falls back to the content provider:

```bash
adb shell content query --uri content://com.ghostinthedroid.portal/state_full
```

The generation counter is HTTP-only (content provider would require frequent polling).

## API Endpoints

- `GET /generation` — Screen generation counter (new)
- `GET /state` — Full accessibility tree (33ms)
- `GET /elements` — Flat element list with bounds
- `GET /phone_state` — Current app/activity/keyboard state
- `GET /screenshot?hideOverlay=true` — PNG screenshot (base64)
- `GET /packages` — Installed package list
- `POST /overlay` — Toggle numbered element overlay
- `POST /speak` — Text-to-speech
- `POST /clipboard` — Set clipboard text
- `POST /stream/start` — Start WebRTC stream
- `POST /stream/stop` — Stop WebRTC stream

## Development

### Running Tests

```bash
./gradlew test
```

### Logging

```bash
adb logcat | grep -E "Ghost(A11y|Http|Overlay|WebRtc|ScreenCapture)"
```

### Code Structure

- `GhostAccessibilityService.kt` — Core accessibility service
- `GhostHttpServer.kt` — HTTP API endpoints
- `GhostOverlayManager.kt` — Numbered element overlay
- `ScreenGenerationCounter.kt` — Generation counter singleton (new)
- `GhostWebRtcManager.kt` — WebRTC streaming
- `GhostScreenCapture.kt` — Screen capture via MediaProjection
