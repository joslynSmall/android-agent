# Portal APK Build Report

## Build Status: ✅ SUCCESS

The Portal debug APK with screen generation counter feature has been successfully built on the cloud VM.

## Build Details

### Environment Setup
- **Android SDK Location**: `~/android-sdk`
- **SDK Platform**: android-35 (API Level 35)
- **Build Tools**: 35.0.0
- **Command Line Tools**: 11076708_latest

### Build Command
```bash
cd /workspace/portal
export ANDROID_HOME=~/android-sdk
./gradlew assembleDebug
```

### Build Output
- **Status**: BUILD SUCCESSFUL in 29s
- **Tasks Executed**: 35 actionable tasks
- **Warnings**: 14 deprecation warnings (non-critical, existing code)
- **Errors**: None

## APK Details

### File Information
- **Artifact Path**: `/opt/cursor/artifacts/ghost-portal-screen-gen-debug.apk`
- **File Size**: 53 MB
- **SHA-256**: `78b042a6d8523b8eefaf85d14f8379fe3da0efd80b873443b71991bad21b28ef`
- **Package Name**: `com.ghostinthedroid.portal`
- **Version Code**: 1
- **Version Name**: 1.0.0

### SDK Configuration
- **Compile SDK**: 35
- **Target SDK**: 35
- **Min SDK**: 30
- **Platform Build**: 15 (Android 15)

### APK Contents
- **DEX Files**: 3 (classes.dex, classes2.dex, classes3.dex)
- **Native Libraries**: libjingle_peerconnection_so.so (WebRTC)
- **Application Label**: Ghost Portal

## Feature Verification

### ✅ Screen Generation Counter Included

The new `ScreenGenerationCounter` class is confirmed to be included in the compiled APK:

```
Found in classes.dex:
- Lcom/ghostinthedroid/portal/ScreenGenerationCounter;
- ScreenGenerationCounter.kt
- incrementIfThrottled method
```

All feature code changes are present in the built artifact.

## Installation Instructions

### Method 1: ADB Install
```bash
adb install -r /opt/cursor/artifacts/ghost-portal-screen-gen-debug.apk
```

### Method 2: Download from Artifacts
The APK is available at:
```
/opt/cursor/artifacts/ghost-portal-screen-gen-debug.apk
```

### Post-Installation Setup

1. **Grant Overlay Permission**:
   ```bash
   adb shell pm grant com.ghostinthedroid.portal android.permission.SYSTEM_ALERT_WINDOW
   ```

2. **Enable Accessibility Service** (manual on device):
   - Open Settings → Accessibility
   - Find "Ghost Portal"
   - Toggle ON

3. **Verify Installation**:
   ```bash
   adb forward tcp:18080 tcp:8080
   curl http://localhost:18080/generation
   ```

   Expected output:
   ```json
   {"status":"success","result":"{\"generation\":1,\"timestamp\":...}"}
   ```

## Build Warnings (Non-Critical)

The following deprecation warnings were reported but do not affect functionality:

1. **AccessibilityNodeInfo.recycle()** - Deprecated in API 35
   - Locations: GhostAccessibilityService.kt (7 occurrences)
   - Note: Still functional, but may need updating in future Android versions

2. **NanoHTTPD.parms** - Deprecated getter
   - Location: GhostHttpServer.kt:140
   - Note: Used in screenshot endpoint parameter handling

3. **Window.statusBarColor/navigationBarColor** - Deprecated setters
   - Location: MainActivity.kt:58-59
   - Note: UI styling only, no functional impact

These warnings are from existing code and are not related to the new generation counter feature.

## Build Timeline

1. **00:00** - Initial build attempt (failed - SDK not found)
2. **00:01** - Downloaded Android command line tools (1s)
3. **00:02** - Extracted and set up SDK structure (1s)
4. **00:03** - Accepted SDK licenses (1s)
5. **00:04** - Installed SDK platform-35 and build-tools (4s)
6. **00:05** - Re-ran assembleDebug build (29s)
7. **00:34** - Build completed successfully
8. **00:38** - APK copied to artifacts folder (4s)

**Total Setup + Build Time**: ~38 seconds

## File Locations

### Source Files
- Portal Project: `/workspace/portal/`
- Build Output: `/workspace/portal/app/build/outputs/apk/debug/app-debug.apk`

### Artifact Location
- **Primary Artifact**: `/opt/cursor/artifacts/ghost-portal-screen-gen-debug.apk`
- Size: 53 MB (55,742,464 bytes)
- Permissions: -rw-rw-rw-

## Verification Checklist

- [x] APK built successfully without errors
- [x] File size reasonable (53 MB, includes WebRTC libs)
- [x] Package name correct (com.ghostinthedroid.portal)
- [x] Version information correct (1.0.0)
- [x] ScreenGenerationCounter class included in DEX
- [x] APK structure valid (verified with aapt)
- [x] SHA-256 checksum generated
- [x] Artifact copied to standard location

## Next Steps

1. **Install on Test Device**:
   ```bash
   adb install -r /opt/cursor/artifacts/ghost-portal-screen-gen-debug.apk
   ```

2. **Enable Accessibility Service** (manual step on device)

3. **Test Generation Endpoint**:
   ```bash
   adb forward tcp:18080 tcp:8080
   curl http://localhost:18080/generation
   ```

4. **Run Python Integration Test**:
   ```python
   from gitd.bots.common.adb import Device, wait_for_generation_change
   dev = Device("YOUR_SERIAL")
   dev.tap(540, 1200, delay=0)
   if wait_for_generation_change(dev, timeout=2.0):
       print("✅ Generation counter working!")
   ```

5. **Measure Performance**:
   - Compare wait times: generation vs fixed sleep
   - Verify 60-85% improvement in typical scenarios

## Troubleshooting

### If APK install fails
```bash
# Uninstall old version first
adb uninstall com.ghostinthedroid.portal

# Then reinstall
adb install /opt/cursor/artifacts/ghost-portal-screen-gen-debug.apk
```

### If generation endpoint not found
- Ensure accessibility service is enabled
- Restart Portal app: `adb shell am force-stop com.ghostinthedroid.portal`
- Check logs: `adb logcat | grep Ghost`

### If build needs to be repeated
```bash
cd /workspace/portal
export ANDROID_HOME=~/android-sdk
./gradlew clean assembleDebug
```

## Summary

✅ **Build Successful**  
✅ **All Features Included**  
✅ **APK Ready for Testing**

**Artifact Path**: `/opt/cursor/artifacts/ghost-portal-screen-gen-debug.apk`

The Portal APK with screen generation counter is ready for deployment and testing.
