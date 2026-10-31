# Pocket Gains (working name, v2 cozy direction; v1 was "SWOLEMON"): Gamified Workout Tracker. Feasibility & Architecture

**Verdict: Feasible.** One developer can build an MVP in about 8–12 weeks. The hard part is the art pipeline for the avatar (it has to be modular per muscle group). The code is a standard CRUD app plus a stat engine.

Mockups (GPT Image 2.5 Flare on fal):
- **v2 cozy (current direction):** `mockups-v2/1-starter-select.png`, `2-home-gym.png`, `3-log-workout.png`, `4-customize-shop.png`, `5-growth.png`. Style reference is in `ref/reference.png`.
- v1 (dark/premium, superseded): `mockups/a-home.png`, `b-log-workout.png`, `c-avatar-evolution.png`, `d-stats-gear.png`

## 1. Recommended stack
- **Plain Flutter + Rive** (recommended). This is a UI-heavy app and the avatar is one animated widget. Flame adds a game loop you mostly don't need. Rive state machines take numeric inputs, so each muscle stat can drive the body shape continuously.
  - Add **Flame** (`flame`, `flame_rive`) only if you later want mini-games (boss fights, rep-timing challenges). It can be embedded as a widget on one screen.
- State: Riverpod. Navigation: go_router.
- Local DB: **Drift** (SQLite, typed, migrations, actively maintained). Isar's main repo hasn't been pushed since June 2025, and Hive has moved to the `hive_ce` fork, so Drift is the safer pick. The app is offline-first, and you can add sync later (Supabase or Firebase) for backup and leaderboards.
- Health: `health` package (Apple HealthKit and Google Health Connect). Use it to write workouts and optionally read steps or active energy for bonus XP.
- Juice: `lottie` for one-shot celebrations (confetti, level-up burst), Rive for the persistent avatar, plus `flutter_animate` and haptics.
- In-app purchases (later): RevenueCat (`purchases_flutter`) or `in_app_purchase`.

## 2. Data model
```
Exercise(id, name, primaryMuscle, secondaryMuscles[], mechanic: compound|isolation)
Workout(id, startedAt, endedAt, notes)
SetEntry(id, workoutId, exerciseId, setIndex, weightKg, reps, rpe?, isPR)
MuscleStat(muscle, xp, level, lastTrainedAt, decayedXp)    // one row per MuscleGroup
Profile(totalXp, level, rank, streakDays, lastWorkoutDate)
GearItem(id, slot: head|wrist|waist|back|hand|feet, rarity, unlockRule JSON)
OwnedGear(gearId, unlockedAt, equipped)
Achievement(id, rule JSON, unlockedAt?)
```
MuscleGroups (keep to about 8 for art cost): chest, back, shoulders, arms, core, quads, hamstrings/glutes, calves. These map to about 6 visual regions: chest, back/lats, shoulders, arms, core, legs.

## 3. XP and per-muscle stats (with decay and imbalance)
- **Set XP** = `base(10) × volumeFactor × intensityFactor`, where volumeFactor = `log2(1 + weight×reps / bodyweight)` and intensityFactor rewards RPE or PRs. Cap XP per muscle per day so 40 sets of curls can't be farmed.
- Split XP: 100% to the primary muscle and 50% to each secondary muscle. Profile XP is the sum of all of it.
- **Muscle level** follows a curve: `xpToNext(L) = 100 × L^1.5`. Profile level uses the same idea.
- **Decay (atrophy):** if `now − lastTrainedAt > 7 days`, the *displayed size* stat drops by about 1–2% of the muscle's XP per day, floored at 70% of its peak. Never reduce level or total XP (losing earned progress feels punitive). Decay only affects the body shape and adds a "overdue" badge.
- **Imbalance:** `imbalance = max(upperAvg, lowerAvg) / min(...)`. When it is above 2.0, trigger the comedic state: "SKIPPED LEG DAY" card, wobbling toothpick legs, quest "Log a leg workout to fix". Same idea for "all mirror muscles" (chest/arms ≫ back).
- **Streak:** consecutive days with at least 1 workout, or *weekly* targets (e.g. 3×/week) to be kinder to rest days. Recommend weekly streaks plus a rest-day freeze token.

## 4. Avatar rendering
- **Rive state machine** with one numeric input per region: `chest`, `arms`, `shoulders`, `back`, `core`, `legs` (0–100), plus `bodyFat`, `mood`, and boolean/number inputs for each gear slot (`head`, `waist`, `back`, `hand`).
  - Each region is a separate mesh/bone group with blend states (skinny → toned → buff → huge), interpolated by its input. That is how a huge chest on noodle legs falls out naturally from the data.
  - Gear is a separate layer on each slot, switched by input. Each item is art drawn once per slot and bone-attached, so it follows body size.
  - Triggers: `flex`, `levelUp`, `wobble` (imbalance idle), `sad` (streak broken).
- **Fallback/cheaper option:** layered 2D PNG sprites per body part at 4 sizes each (6 regions × 4 = 24 parts), composited in a `Stack` (or Flame `SpriteComponent`s). Less smooth but quick to produce with AI-assisted art. Use fal for concepts and a human or careful pipeline to make the parts consistent and cut out.
- Mapping: `regionSize = clamp(muscleLevel × k − decayPenalty)`, and visual stage tier = profile level (1/10/25/50) as in mockup C.

## 5. Ranks and gear unlocks
- Ranks by profile level: Noodle → Bronze Lifter → Silver → Gold → Platinum → Legend.
- Gear unlock rules are data-driven JSON, evaluated after every workout:
  - Rank-based: Champion Belt at Bronze, Hero Cape at Silver.
  - Muscle-based: Squat Crown at Legs Lv 10, Iron Pec Plate at Chest Lv 20.
  - Behavior or funny ones: Rubber Chicken after 3 skipped leg days in a row, Sweatband of Consistency for a 4-week streak, Toothpick Trophy for max imbalance.
  - Rarity tiers: common, rare, epic, legendary.
- Gear Locker screen (mockup D) to equip one item per slot. Reward toast on unlock (mockup B).
- Monetization option: purely cosmetic gear packs. Never sell XP or stats.

## 6. MVP feature list
1. Onboarding: name, bodyweight, goal, starter avatar.
2. Exercise library (about 80 exercises, muscle-tagged; you can seed from wger's open exercise DB, but check its license/attribution).
3. Workout logging: sets, reps, weight, rest timer, PR detection.
4. XP engine, per-muscle levels, decay, imbalance detection.
5. Rive avatar on Home with 6 muscle inputs and 3–4 gear slots. Level-up and unlock celebrations.
6. Evolution screen, stats/skill-tree screen, Gear Locker with about 15 items.
7. Streaks plus local notifications ("your legs miss you").
8. HealthKit / Health Connect write.
9. Local backup/export.

Later: cloud sync, friends and leaderboards, Flame mini-games, cosmetic IAP, Apple Watch logging.

## 7. App Store requirements (rough)
- Apple Developer Program ($99/yr) and a Mac with Xcode for builds (or Codemagic / GitHub Actions macOS runners).
- Privacy: Privacy Nutrition Labels, `PrivacyInfo.xcprivacy` manifest, and a privacy policy URL. Health data must not be used for ads, and you need the HealthKit entitlement plus usage strings (`NSHealthShareUsageDescription` / `NSHealthUpdateUsageDescription`).
- If you have accounts: Sign in with Apple (when other social logins exist) and in-app account deletion.
- IAP must go through StoreKit for digital goods (cosmetics).
- Guideline 1.4.1: avoid medical claims. Add a "consult a professional" disclaimer.
- Screenshots for 6.7"/6.9" iPhone, plus an age rating questionnaire. Expect 1–3 days of review.
- Google Play (cross-platform): Health Connect permissions declaration form, data safety form, and a 12-tester / 14-day closed test for new personal accounts.

## 8. Risks
- **Art consistency and cost** (biggest risk). The modular, rigged avatar needs a real Rive artist, or many careful iterations. AI images are good for concepts, not production rigs.
- **Logging friction:** if logging is slower than Strong/Hevy, users churn regardless of the avatar. Prioritize fast set entry, templates, and "repeat last workout."
- **Cheating/farming:** irrelevant solo, but it matters if you add leaderboards (need caps and sanity checks).
- **Decay feeling punitive:** keep it cosmetic and comedic, with floors.
- **Body-image sensitivity:** keep the art cartoonish and the tone playful. Consider a body-type selector and inclusive defaults.
- **Isar/Hive maintenance risk:** avoid by using Drift.
- **Rive runtime changes:** `rive` 0.14 is a new major runtime. Pin versions.

## 9. Useful repos and packages
- awesome-gamedev-agent-skills (Apache-2.0): https://github.com/gamedev-skills/awesome-gamedev-agent-skills. Engine-specific skills don't apply. Use `game-feel`, `save-systems`, `game-ui-ux`, `create-game-assets`, `genres/rpg`, and `roblox-simulator-economy` (for curve and pacing ideas) as design references. Install into Cursor with `npx skills add gamedev-skills/awesome-gamedev-agent-skills -a cursor`. The router won't detect a Flutter engine, so invoke those skills by name.
- Flame: https://github.com/flame-engine/flame (MIT). Rive: https://github.com/rive-app/rive-flutter (MIT). Lottie: https://github.com/xvrh/lottie-flutter (MIT)
- Drift: https://github.com/simolus3/drift (MIT). Health: https://github.com/carp-dk/carp-health-flutter (MIT, pub `health`)
- Reference trackers: https://github.com/brandonp2412/Flex (MIT, Flutter, offline-first) and https://github.com/wger-project/flutter (AGPL-3.0: learn from it, don't copy code into a closed-source app).

---
# v2 additions: cozy direction, starters, coins, decoratable home gym

## 10. Art direction (v2)
Cozy hand-painted look: cream paper UI cards, a terracotta primary color, warm wood and orange equipment, pastel lavender-peach swirl rugs, plants, serif headings with small-caps subtitles, and rounded buttons. Characters are small, cute and unisex, with chunky "buff" growth played for charm, not realism. This also reduces body-image risk (see §8).

## 11. Starter characters
- At onboarding, players choose 1 of 3 free starters. A 4th starter is unlockable for coins. Mockup 1 shows:
  - **Sprout:** bean-sprite with a leaf on its head. Balanced.
  - **Pip:** fox critter. Cardio-flavored.
  - **Mochi:** unisex kid with a bob haircut and a hoodie. Strength-flavored.
  - **Morel:** mushroom. Locked at 500 coins.
- **Traits are flavor plus tiny cosmetic bonuses only** (e.g. Pip gets +10% *coins* on cardio sessions). Never stat or XP multipliers that make one starter "correct."
- **Same rig, different skin.** All starters share one skeleton and the same muscle-region inputs (chest, arms, shoulders, back, core, legs) and the same gear sockets (head, wrist, waist, back, feet). A new starter is then mostly an art cost (a new skin set), not engineering.
  - In Rive: one artboard per starter with identical input names, or skin swapping via nested artboards.
  - In PNG-layer mode: one sprite set per starter per region-size tier.
- Players can switch their active buddy later. Muscle stats belong to the *player*, so any buddy shows the same body balance.
- Each starter evolves through stages: Lv 1 Seedling → 10 Sprig → 25 Sapling → 50 Mighty Oak (names per starter). Stage changes the base silhouette and idle animation; the muscle inputs still drive the per-region size within each stage (mockup 5).

## 12. Currency economy ("coins")
**Coins are soft currency, earned only by training.** All of it is cosmetic, with no pay-to-win: coins never buy XP, levels, stats, or streak repairs beyond the free freeze token.

**Sources** (starting numbers to tune; aim for about 150–250 coins per active week):

| Source | Coins |
|---|---|
| Finish a workout (at least 3 working sets) | +20 |
| Per completed exercise (cap 6) | +5 |
| New PR (cap 3 per workout) | +10 |
| Weekly goal hit (e.g. 3–4 workouts) | +50 |
| Streak milestones (2/4/8/12 weeks) | +100/200/400/800 |
| Fixing an imbalance (train the weakest group when imbalance > 2) | +30 "Leg day hero" bonus |
| Level-up | +25 × level band |
| Rank-up | +250 |

- **Anti-farm rules:**
  - A daily coin cap of about 120 from workouts. Milestones don't count toward it.
  - The minimum valid set requires reps > 0 and a plausible weight.
  - Workouts backdated more than 48h give XP but no coins.
- **Sinks:**
  - Outfit/gear: 50–600.
  - Gym decor: 80–1,500. Big items like a squat rack skin or room themes cost the most.
  - Extra starters: 500–1,500.
  - Rug/wallpaper themes: 300–800.
  - Optional seasonal rotating shop: 4–6 items per week, to keep the sink alive.
- **Rank gating (unchanged from §5):** some items need *both* coins and a rank (Wizard Robe at Silver, Tiny Crown at Gold, Peach Punching Bag at Silver). There are also achievement-only items that coins can't buy: Squat Crown at Legs Lv 10, Leg Warmers as a "leg day special."
- **Pacing target:** a regular user (3×/week) can afford something nice every 1–2 weeks and a big decor piece every month or so. Model this with a small pacing script, like the `roblox-simulator-economy` skill's calculator idea.
- **Optional real-money (post-MVP):** premium *cosmetic* packs or a supporter subscription through StoreKit/RevenueCat. Never sell coins in a way that skips training, or keep paid items in a separate "premium" shelf. Never use loot boxes; if random items are ever added, disclose the odds.
- **Data model additions:**
```
Wallet(coins, lifetimeEarned)
CoinLedger(id, ts, delta, reason: workout|pr|streak|levelup|rankup|purchase, refId)   // append-only, auditable
ShopItem(id, category: outfit|gear|decor|starter|theme, slot?, price, rankRequired?, achievementRequired?, season?)
Owned(itemId, acquiredAt) ; Loadout(starterId, slotItems map) ; RoomLayout(json)
```
  The wallet balance is the sum of the ledger. Recompute it on launch so it self-heals after a crash (see `save-systems` skill: atomic writes).

## 13. Decoratable home gym (isometric room)
**MVP: a fixed-camera, single-room diorama with slot-based placement** (like Animal Crossing or Neko Atsume, not a free-form builder):
- The room is one illustrated isometric background (walls and floor) per room theme.
- About 12 predefined **anchor slots**: rack area, bench area, wall-poster ×2, window sill, corner plant ×2, ceiling-hang (punching bag/lights), rug, side table, floor-mat, and an "equipment" slot.
- Each decor item is a transparent PNG (or small Rive file for animated pieces, like flickering string lights or a swinging bag) drawn for a specific slot type, with a z-order.
- Render with a Flutter `Stack` of `Positioned` layers sorted by z-order, using the same art scale as the room. The character is its own Rive widget placed on the rug anchor with idle, flex, and wobble animations. It's simple, fast, and needs no game engine.

**V2 option: free placement on an isometric grid with Flame.**
- Use Flame's `IsometricTileMapComponent` for the floor, plus `SpriteComponent`s for furniture.
- Sort by depth (`priority = x + y`), snap to grid on drag, and check collisions with an occupancy grid. Embed the room with `GameWidget` in the home screen, and the character via `flame_rive`.
- Persist layout as `RoomLayout` JSON (itemId, gridX, gridY, rotation).

**Interactions that add charm:**
- Tap equipment to make the buddy use it (a mini animation).
- Unlocked decor reacts to progress: a trophy shelf fills with real PR trophies, a calendar on the wall shows the week's workouts, and plants grow with your streak.

**Art budget:** about 1 room base + 40 decor items + 3 themes for launch. Use fal (Flare edit with `ref/reference.png` + mockups as references) for concepts and first-pass item sprites. Then normalize the size, angle, palette and cut-outs by hand or with a pipeline, as in the `create-game-assets` skill.

## 14. Updated MVP delta
Add to the §6 MVP:
- Starter select (3 free plus 1 coin-unlock)
- Coin wallet, ledger and reward screen
- Shop with Outfit/Gear and Gym Decor tabs (about 15 + 15 items, some rank-locked)
- Slot-based cozy room
- Growth screen with the per-muscle bars and the cute "skipped leg day" state

Defer: Flame free-placement room, seasonal shop, extra rooms, social room visits, paid cosmetics.

## 15. Updated risks
- Art volume roughly doubles: starters × stages × muscle-size tiers × gear sockets, plus decor. Mitigate with one shared rig, gear authored per socket (not per starter) where possible, and a launch set of 3 starters.
- Economy inflation or boredom: keep a sink pipeline (seasonal items) and tune with telemetry.
- App Review: if you sell coins or cosmetics, use IAP and keep everything cosmetic. Loot-box odds disclosure applies if randomness is ever added.
