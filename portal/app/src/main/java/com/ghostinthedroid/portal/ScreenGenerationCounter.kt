package com.ghostinthedroid.portal

import java.util.concurrent.atomic.AtomicLong

/**
 * Monotonic screen-change generation counter incremented on relevant
 * AccessibilityEvents (window state / content / scroll). Throttled to avoid
 * scroll storms. Exposed via HTTP /generation endpoint so the Python host
 * can wait for UI updates instead of fixed sleep delays.
 */
object ScreenGenerationCounter {
    private val generation = AtomicLong(0L)
    private var lastIncrementTime = 0L
    
    // Throttle: min 300ms between increments (similar to overlay refresh delay)
    private const val MIN_INCREMENT_GAP_MS = 300L

    /**
     * Increment the generation counter if enough time has passed since the last increment.
     * Returns true if incremented, false if throttled.
     */
    fun incrementIfThrottled(): Boolean {
        val now = System.currentTimeMillis()
        synchronized(this) {
            if (now - lastIncrementTime < MIN_INCREMENT_GAP_MS) {
                return false
            }
            lastIncrementTime = now
        }
        generation.incrementAndGet()
        return true
    }

    /**
     * Get current generation and timestamp.
     */
    fun getCurrent(): Pair<Long, Long> {
        return Pair(generation.get(), System.currentTimeMillis())
    }

    /**
     * Get current generation value only.
     */
    fun get(): Long = generation.get()
}
