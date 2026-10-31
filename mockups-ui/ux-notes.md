# Pocket Gains: workout-logging UX notes (for the Flutter build)

The mockups are in this folder (01–07). The design goal is to log a set in **one tap**, with each tap paying off in a way you can see and feel on Zeek.

## Key interaction ideas

1. **One-tap repeat set ("Same as last time").**
   - Open the Log Set screen with the steppers already filled from the last set of this exercise (or from last session's same set index).
   - In the common case, logging is a single tap on **Log set**.
   - The chips (`Same as last time`, `+2.5 kg`, `+1 rep`) apply instantly. There's no confirm dialog.
   - Flutter: `ExerciseLog.lastFor(exerciseId, setIndex)` and a prefilled `ValueNotifier<SetDraft>`.

2. **Big, thumb-zone steppers with press-and-hold acceleration.**
   - +/− buttons step by 2.5 kg (configurable) or 1 rep.
   - Holding a button repeats with acceleration: 400 ms, then 120 ms, then 60 ms.
   - Swiping vertically on the big number scrubs the value, like a dial.
   - Tapping the number opens a numeric keypad for edge cases.
   - Flutter: `GestureDetector` with `onLongPressStart` plus a `Timer.periodic` ramp, and `onVerticalDragUpdate` for scrubbing.

3. **Haptics as a reward vocabulary.**
   - `selectionClick` on each stepper tick.
   - `mediumImpact` on Log set.
   - `heavyImpact` plus a double-pulse on a PR or level-up.
   - A light tick each second for the last 3 s of rest.
   - Keep the pattern consistent so users "feel" progress without looking. Flutter: `HapticFeedback.*`; the `vibration` package handles custom patterns.

4. **Muscle XP pops on Zeek.**
   - When you log a set, floating "+12 Chest XP" (amber, 100% main muscle) and "+6 Triceps XP" (teal, 50% helpers) rise from that muscle on Zeek's body and fade out.
   - The muscle region glows briefly.
   - The XP formula stays visible, so the 100%/50% rule teaches itself.
   - Flutter: an `Overlay` with `AnimatedPositioned`/`FadeTransition` anchored to muscle hotspots in Zeek's render (bone sockets if using flutter_scene, a hotspot map if using sprites).

5. **Tap-a-muscle to filter exercises.**
   - The holographic body map on Pick Exercise is the main filter. Tapping a muscle filters the list, and the matching chip lights up; the chips are an accessible fallback.
   - The Front/Back toggle flips the hologram with a 3D Y-rotation.
   - Each exercise card shows the muscles it grows as tags (`Chest 100%`, `Triceps 50%`), so the choice is about growth, not just names.
   - Flutter: a `CustomPainter` hit-test on muscle `Path`s (from SVG) over the hologram image.

6. **Rest timer that auto-starts and stays out of the way.**
   - Logging a set starts the ring timer automatically. The default rest is per exercise and learned from your history.
   - Use `-15s`/`+15s` to adjust, `Skip rest` to move on, and swipe down to minimize it to a pill that floats over other screens.
   - When rest ends, fire a local notification and haptic, and Zeek says a quip.
   - Quips rotate from a short list and reflect context: a PR, the last set, or leg day.
   - Flutter: `flutter_local_notifications` plus wall-clock timestamps for the timer (not tick counting), so it survives backgrounding.

7. **Live Activity / Dynamic Island for rest.**
   - On iOS, show the countdown and the "Up next: Set 4 • 62.5 kg x 8" line on the lock screen, so you never have to unlock the phone mid-workout.
   - Flutter: the `live_activities` package.

8. **PR detection and the loot-reveal summary.**
   - Detect PRs immediately at log time: best e1RM, best weight × reps, and volume. Show a small badge on the set chip; the full ceremony waits for the summary.
   - The summary reveals rewards in sequence:
     1. The before/after glow on Zeek.
     2. The per-muscle XP bars filling.
     3. Coins counting up.
     4. Loot tiles flipping.
   - Each step is tap-to-skip so impatient users aren't held hostage.
   - Flutter: staggered `AnimationController`s plus Rive or Lottie for chest/coin bursts.

9. **"Legs are lagging" nudges, not nags.**
   - Muscle balance = each muscle's XP relative to its expected share.
   - If a group drops below a threshold, Home shows the warning chip and Zeek's legs visibly thin out (the skinny-legs body state).
   - The `Train legs` CTA deep-links to Pick Exercise already filtered to Legs.
   - Keep the tone playful ("Skip leg day, get noodle legs.") and cap it at one nudge per session.

10. **Undo instead of confirm, and resilient state.**
    - Every log shows a 4-second "Undo" snackbar; there are no "Are you sure?" dialogs.
    - Write the workout to local storage (Drift/Isar) after every set, so a crash or app kill never loses a session. On relaunch, offer "Resume Push Day?".
    - Sync is a background concern.

## Design system tokens (from the mockups)
- Background `#14281F` → `#1E3A2C`; cards are slightly lighter with a 1px cyan-teal inner glow and 24 px radius.
- Text cream `#F3E9D2`; muted text at 60% cream.
- Primary amber `#F2A33A`, with a glowing pill button and a dark label; secondary teal `#2FA59A`; hologram cyan `#5EF2E6`; warning terracotta `#C8643B`; coin gold.
- Display font: a chunky rounded serif (e.g. Fraunces/Recoleta-style). UI font: a geometric sans (e.g. Inter/Outfit). Big numbers use the serif.
- Rank pill and coin pill are always top-right; the tab bar is Home / Muscles / Shop / Profile. In-workout screens hide the tab bar to stay focused.

## Model note
- I compared two models on screen 1: `openai/gpt-image-2.5/flare/edit` (01-home_flare.png) vs `fal-ai/nano-banana-pro/edit` (01-home_nbp.png).
- **Flare won:**
  - It renders native 9:19.5 at 1184×2560; NBP only goes up to 9:16.
  - The game scene is richer, and the muscle heatmap reads better.
  - All text was exact.
- NBP's Zeek was slightly closer to the sheet (a fuller beanie) and its UI was a little plainer.
- I generated screens 2–7 with Flare, using zeek-sheet.png and 01-home.png as references.
