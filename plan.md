# Pocket Gains (working name; hero: Zeek the green alien, v6 grown-up cozy direction; v1 was "SWOLEMON"): Gamified Workout Tracker. Feasibility & Architecture

**Verdict: Feasible.** One developer can build an MVP in about 8–12 weeks. The hard part is the art pipeline for the avatar (it has to be modular per muscle group). The code is a standard CRUD app plus a stat engine.

Mockups (GPT Image 2.5 Flare on fal):
- **v6 hero (current direction): Zeek, green alien.** `mockups-v6/zeek-sheet.png` (turnaround, body states, expressions) and `mockups-v6/zeek-home.png`. See §17.
- v5 species exploration: `mockups-v5/lineup-1.png`, `lineup-2.png`, `lineup.png`, `alien.png`, `alien-home.png`.
- v4 "less childish" style directions: `mockups-v4/A-streetwear-home.png`, `B-lofi-night-home.png`, `C-retro-pixel-home.png`, `comparison.png`.
- v3 ghost exploration: `mockups-v3/` (see §16).
- **v2 cozy (superseded layout/palette base):** `mockups-v2/1-starter-select.png`, `2-home-gym.png`, `3-log-workout.png`, `4-customize-shop.png`, `5-growth.png`. Style reference is in `ref/reference.png`.
- v1 (dark/premium, superseded): `mockups/a-home.png`, `b-log-workout.png`, `c-avatar-evolution.png`, `d-stats-gear.png`

## 1. Recommended stack
- **Flutter app shell + Flame for the "game" surfaces.** Rive is dropped for the character: Fernando tried it before, and it handled this kind of character poorly.
  - Menus, workout logger, weekly tracker, shop lists, settings and stats stay **normal Flutter widgets**.
  - The **home-gym room and the character render in Flame** (`flame`), embedded with `GameWidget` on the Home, Customize and Growth screens. The Flutter UI overlays it (Flame `overlays` or a plain `Stack`).
  - Flutter and Flame communicate through Riverpod. The game reads the player's stats, loadout and room layout from providers, and the UI sends events like `playFlex()` and `levelUp()` through a small `GameController`.
- **Character: a paper doll of layered 2D sprites** (see §4), animated with Flame effects. **Optional later upgrade: Spine** for skeletal animation and skin swapping (see §4).
- State: Riverpod. Navigation: go_router.
- Local DB: **Drift** (SQLite, typed, migrations, actively maintained). Isar's main repo hasn't been pushed since June 2025, and Hive has moved to the `hive_ce` fork, so Drift is the safer pick. The app is offline-first, and you can add sync later (Supabase or Firebase) for backup and leaderboards.
- Health: `health` package (Apple HealthKit and Google Health Connect). Use it to write workouts and optionally read steps or active energy for bonus XP.
- Juice:
  - Character and room: Flame effects (`ScaleEffect`, `MoveEffect`, `SequenceEffect`) and `ParticleSystemComponent` for sparkles and coins.
  - UI: `flutter_animate` and haptics.
  - `lottie` is **optional, for UI celebrations only** (a confetti overlay or level-up burst on a Flutter screen), never for the character.
- In-app purchases (later): RevenueCat (`purchases_flutter`) or `in_app_purchase`.
- **Design guides from the gamedev skills repo** (`repo-gamedev/skills/...`):
  - `disciplines/create-game-assets`: the art pipeline.
  - `disciplines/game-feel`: juice, squash/stretch and reward timing.
  - `genres/rpg`: XP, levels, gear slots and progression.
  - `disciplines/save-systems`: atomic, versioned saves for the ledger, loadout and room JSON.

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

## 4. Avatar rendering (Flame paper doll)
**Approach: a 2D paper doll of layered sprites per body part, assembled and animated in Flame.** No Rive.

**Body parts and size tiers:**
- Parts: `head`, `torso` (chest, back and core read as one torso sprite), `armL`/`armR` (mirrored), `legL`/`legR` (mirrored). Shoulders can be folded into the torso or arm tiers.
- Each part has **3–4 size tiers**: noodle, toned, buff, and an optional huge.
- The tier is chosen from that region's per-muscle stat: `tier = thresholds(regionSize)`, where `regionSize = clamp(muscleLevel × k − decayPenalty)`.
- Separate stats per part mean a buff torso on noodle legs falls out of the data naturally. That is the skipped-leg-day gag (mockup 5).
- Growth stage (Seedling, Sprig, Sapling, Mighty Oak at levels 1/10/25/50) swaps the head and torso base set.

**Assembly in Flame:**
- A `CharacterComponent` (`PositionComponent`) owns child `SpriteComponent`s.
- Each part sprite has fixed **anchor points**: neck, shoulderL/R, hipL/R, plus gear sockets. They are stored in a per-starter `rig.json` next to the sprite sheet.
- Children are attached at those anchors with a set `priority` (z-order): back gear, legs, torso, arms, front gear, head, head gear.
- Changing a tier just swaps a sprite. The anchors stay put, so the rig never breaks.
- Smooth growth transitions: cross-fade the old and new tier sprites with `OpacityEffect`, plus a "poof" particle.

**Gear:**
- Gear items are also layered sprites on **anchor slots**: `head`, `wrist`, `waist`, `back`, `feet`, `hand`.
- Each gear item has a variant per relevant size tier, or a scale/offset per tier in `rig.json`, so a belt fits a buff waist.
- Gear is drawn once per slot and shared across starters where the silhouettes allow it. Otherwise, per starter.

**Animation (procedural, cheap):**
- **Idle:** a gentle breathing loop with squash/stretch on the torso (`ScaleEffect` ±3% with `EffectController(alternate: true, infinite: true)`), plus a slight bob on the head and arms.
- **Flex:** rotate the arms up, a squash-then-stretch pop, a sparkle particle and a haptic.
- **Level-up:** a jump with `SequenceEffect` (squash, stretch, land squash), a coin burst and a growth swap.
- **Wobble:** when imbalance is above 2, the legs jitter and the torso sways (the comedic state).
- **Sad:** a droop when the streak breaks. **Tap reactions** play speech bubbles.
- Follow `game-feel` for timing: about 80–150 ms anticipation, an overshoot, then settle.

**Sprite sheets:** pack each starter into one atlas (`flame_texturepacker`, or Flame's `Images` cache).
- Budget per starter: about 4 tiers × 4 parts (mirrored limbs) × 4 stages ≈ 64 part sprites, plus expressions.

**Optional later upgrade: Spine.**
- If procedural tweens feel too stiff, move the rig to **Spine** (Esoteric Software) using the official `spine_flutter` runtime, which can also render inside Flame.
- What it adds:
  - Real skeletal animation and mesh deformation.
  - **Skins** for starters and gear.
  - Attachment swapping per size tier.
- Cost: a **paid Spine Editor license** (Essential or Professional tier; the runtime license requires one).
- Keep the same part, tier and slot naming now, so the art and data migrate cleanly later.

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
5. Flame paper-doll avatar on Home (in `GameWidget`): per-part size tiers driven by muscle stats, 3–4 gear slots, and idle, flex and level-up tweens. Level-up and unlock celebrations (optional Lottie overlay for UI only).
6. Evolution screen, stats/skill-tree screen, Gear Locker with about 15 items.
7. Streaks plus local notifications ("your legs miss you").
8. HealthKit / Health Connect write.
9. Local backup/export.

Later: cloud sync, friends and leaderboards, Flame mini-games (same engine already in the app), Spine upgrade, cosmetic IAP, Apple Watch logging.

## 7. App Store requirements (rough)
- Apple Developer Program ($99/yr) and a Mac with Xcode for builds (or Codemagic / GitHub Actions macOS runners).
- Privacy: Privacy Nutrition Labels, `PrivacyInfo.xcprivacy` manifest, and a privacy policy URL. Health data must not be used for ads, and you need the HealthKit entitlement plus usage strings (`NSHealthShareUsageDescription` / `NSHealthUpdateUsageDescription`).
- If you have accounts: Sign in with Apple (when other social logins exist) and in-app account deletion.
- IAP must go through StoreKit for digital goods (cosmetics).
- Guideline 1.4.1: avoid medical claims. Add a "consult a professional" disclaimer.
- Screenshots for 6.7"/6.9" iPhone, plus an age rating questionnaire. Expect 1–3 days of review.
- Google Play (cross-platform): Health Connect permissions declaration form, data safety form, and a 12-tester / 14-day closed test for new personal accounts.

## 8. Risks
- **Art consistency and cost** (biggest risk). The paper doll needs every part, tier and gear sprite drawn to the same scale, angle, line weight and palette, with consistent anchors.
  - Generate them with fal Flare edit and a **locked style reference** (`ref/reference.png` plus the approved Sprout sheet), following `create-game-assets`.
  - Then normalize by hand or with a script: cut-out and trim, fixed canvas, palette clamp, and anchors marked in `rig.json`.
  - Budget for a human touch-up pass. AI output is good enough for first-pass parts but not guaranteed pixel-consistent.
- **Logging friction:** if logging is slower than Strong/Hevy, users churn regardless of the avatar. Prioritize fast set entry, templates, and "repeat last workout."
- **Cheating/farming:** irrelevant solo, but it matters if you add leaderboards (need caps and sanity checks).
- **Decay feeling punitive:** keep it cosmetic and comedic, with floors.
- **Body-image sensitivity:** keep the art cartoonish and the tone playful. Consider a body-type selector and inclusive defaults.
- **Isar/Hive maintenance risk:** avoid by using Drift.
- **Flame/Flutter version drift:** pin `flame` and its bridge packages. Keep game logic in plain Dart (stats → tiers), so it can be unit-tested outside Flame.
- **Procedural animation looking stiff:** mitigate with good squash/stretch timing (`game-feel`). The Spine upgrade path is the escape hatch, at the cost of a license.

## 9. Useful repos and packages
- awesome-gamedev-agent-skills (Apache-2.0): https://github.com/gamedev-skills/awesome-gamedev-agent-skills. Engine-specific skills don't apply. Use `game-feel`, `save-systems`, `game-ui-ux`, `create-game-assets`, `genres/rpg`, and `roblox-simulator-economy` (for curve and pacing ideas) as design references. Install into Cursor with `npx skills add gamedev-skills/awesome-gamedev-agent-skills -a cursor`. The router won't detect a Flutter engine, so invoke those skills by name.
- Flame: https://github.com/flame-engine/flame (MIT; includes `IsometricTileMapComponent`, effects, particles and `GameWidget`). Lottie (optional, UI only): https://github.com/xvrh/lottie-flutter (MIT)
- Spine (optional later): https://github.com/EsotericSoftware/spine-runtimes (`spine-flutter`; requires a paid Spine Editor license)
- Drift: https://github.com/simolus3/drift (MIT). Health: https://github.com/carp-dk/carp-health-flutter (MIT, pub `health`)
- Reference trackers: https://github.com/brandonp2412/Flex (MIT, Flutter, offline-first) and https://github.com/wger-project/flutter (AGPL-3.0: learn from it, don't copy code into a closed-source app).

---
# v2 additions: cozy direction, starters, coins, decoratable home gym

## 10. Art direction (v2)
> **Superseded by §17** (v4/v5 grown-up hybrid style). Kept for history.

Cozy hand-painted look: cream paper UI cards, a terracotta primary color, warm wood and orange equipment, pastel lavender-peach swirl rugs, plants, serif headings with small-caps subtitles, and rounded buttons. Characters are small, cute and unisex, with chunky "buff" growth played for charm, not realism. This also reduces body-image risk (see §8).

## 11. Starter characters
> **Starter roster superseded by §17** (Zeek, Glorp, Hops, Puff). The mechanics below (3 free + 1 coin-unlock, flavor-only traits, shared paper-doll template, stages) still apply.

- At onboarding, players choose 1 of 3 free starters. A 4th starter is unlockable for coins. Mockup 1 shows:
  - **Sprout:** bean-sprite with a leaf on its head. Balanced.
  - **Pip:** fox critter. Cardio-flavored.
  - **Mochi:** unisex kid with a bob haircut and a hoodie. Strength-flavored.
  - **Morel:** mushroom. Locked at 500 coins.
- **Traits are flavor plus tiny cosmetic bonuses only** (e.g. Pip gets +10% *coins* on cardio sessions). Never stat or XP multipliers that make one starter "correct."
- **Same paper-doll template, different art.** All starters share the same part list (head, torso, arms, legs), the same 3–4 size tiers per part, and the same gear anchor slots (head, wrist, waist, back, feet, hand). A new starter is then mostly an art cost (a new sprite atlas plus `rig.json` anchors), not engineering.
  - In Flame: `CharacterComponent(starter: 'sprout')` loads `sprout_atlas.png` and `sprout_rig.json`. Code is identical for every starter.
  - Later with Spine: each starter becomes a Spine **skin** on a shared skeleton.
- Players can switch their active buddy later. Muscle stats belong to the *player*, so any buddy shows the same body balance.
- Each starter evolves through stages: Lv 1 Seedling → 10 Sprig → 25 Sapling → 50 Mighty Oak (names per starter). Stage swaps the base head and torso sprite set and tweaks the idle tween. The per-muscle stats still pick each part's size tier within the stage (mockup 5).

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
**Engine: Flame, embedded via `GameWidget`** on Home and Customize. The Flutter UI (header, coin chip, Start Workout/Customize buttons, weekly tracker, shop tabs) stays normal widgets around or over it.

**v1: an isometric grid with fixed slots.**
- The room is a Flame scene: walls are a background sprite, and the floor is an `IsometricTileMapComponent` (one tile set per room theme). The rug is a floor decal.
- About 12 predefined **slots** sit at fixed grid cells: rack area, bench area, wall-poster ×2, window sill, corner plant ×2, ceiling-hang (punching bag/lights), rug, side table, floor mat, and an equipment slot.
- Each decor item is a sprite (or a short sprite-sheet animation, like flickering string lights or a swinging bag) drawn for one slot type, with an anchor/foot point.
- **Depth sorting:** `priority = gridX + gridY` (with a tiebreak by layer), so the character can walk behind the bench and in front of the rack.
- The character is the same `CharacterComponent` from §4. It idles on the rug cell and can walk between cells with `MoveEffect`. Tapping equipment makes it play a "use" tween there.

**Later: free placement.**
- Drag decor in Customize, with snap-to-grid, an occupancy grid for collisions, rotation (2–4 facings per item), and a green/red placement ghost.
- Same components, just no fixed slots.

**Saved as JSON:**
```
RoomLayout { version, theme, items: [ { itemId, gridX, gridY, facing, slotId? } ] }
```
- Store it in Drift as a JSON column.
- Save atomically and with a version number, per `save-systems`: write to a temp row, swap, and keep the previous layout for undo and corruption recovery. Migrate on version bump.
- Items that are no longer owned get dropped on load.

**Interactions that add charm:**
- Tap equipment to make the buddy use it (a mini animation).
- Unlocked decor reacts to progress: a trophy shelf fills with real PR trophies, a calendar on the wall shows the week's workouts, and plants grow with your streak.

**Art pipeline (character parts, gear and decor):** follow the `create-game-assets` skill.
1. **Lock the style:** `ref/reference.png` plus the approved Sprout sheet go in every fal `openai/gpt-image-2.5/flare/edit` call as `image_urls`, with a fixed prompt preamble (palette, line weight, lighting, isometric 2:1 angle for decor, front 3/4 for the character).
2. Generate parts on a flat background in a fixed canvas size, one tier or item per call. Batch variants.
3. Post-process with a script: background removal and trim, scale to the grid unit, palette clamp, pad to power-of-two, and pack into atlases.
4. Mark anchors (neck, shoulders, hips, gear sockets, decor foot point) in `rig.json` and `decor.json`. A tiny Flame debug scene previews every tier × gear combo, to catch misfits.
5. Do a human touch-up pass on hero assets.

Launch budget: 3 starters × about 64 part sprites, about 30 gear items, about 40 decor items, and 3 room themes.

## 14. Updated MVP delta
Add to the §6 MVP:
- Starter select (3 free plus 1 coin-unlock)
- Coin wallet, ledger and reward screen
- Shop with Outfit/Gear and Gym Decor tabs (about 15 + 15 items, some rank-locked)
- Flame isometric cozy room with fixed slots and the paper-doll character (`GameWidget`)
- Growth screen with the per-muscle bars and the cute "skipped leg day" state

Defer: free-placement room (Flame grid already in place), Spine upgrade, seasonal shop, extra rooms, social room visits, paid cosmetics.

## 15. Updated risks
- Art volume roughly doubles: starters × stages × part tiers × gear slots, plus decor. Mitigate with one shared paper-doll template and anchor naming, gear authored per slot (not per starter) where possible, a locked fal style reference, and a launch set of 3 starters.
- Economy inflation or boredom: keep a sink pipeline (seasonal items) and tune with telemetry.
- App Review: if you sell coins or cosmetics, use IAP and keep everything cosmetic. Loot-box odds disclosure applies if randomness is ever added.

---
## 16. Ghost character variant (exploration, v3)
> **Status:** exploration. Puff is no longer the hero (Zeek is, see §17) but stays in the roster as a starter. The tail → legs mapping below still applies to Puff. Wisp, Dumpling and Snooze are parked.

Mockups: `mockups-v3/puff-character-sheet.png`, `ghost-starters.png`, `ghost-growth.png`, `ghost-home.png`, `ghost-workout-sprites.png`.

**Concept:** players pick a cute baby ghost buddy that gets stronger as they train.
- **Mood reference only:** the Baby Ghosts NFT collection (https://babyghosts.com, https://opensea.io/collection/babyghosts). It's third-party IP. Samples are in `ref/babyghosts/`, and none were fed to the image model.
- **How ours differ:** they keep their cozy-painted identity. Gumdrop bodies (no separate big head, no top curl), thin warm-brown linework instead of thick black outlines, pastel gouache colors, small bean eyes, no PFP-style clothing traits.

**Starters** (same template, different art):

| Starter | Look | Trait |
|---|---|---|
| **Puff** (hero) | mint-cream, terracotta knit sweatband | balanced |
| **Wisp** | lavender, ribbon tail, headphones | cardio: +coins on runs |
| **Dumpling** | round peach, lifting belt | strength |
| **Snooze** | sky-blue cloud puff, nightcap | recovery/yoga, locked at 500 coins |

Growth stages: Wisplet (Lv 1) → Spook (10) → Haunter (25) → Mighty Boo (50).

**Ghost anatomy → muscle groups** (paper-doll parts from §4, renamed):

| Ghost part | Muscle groups | What changes per tier |
|---|---|---|
| Arms (nub → beefy) | arms, shoulders | nub, little bumps, round biceps, chunky flex arms |
| Body upper / "chest" | chest, back | body widens and gets a puffed-out chest; back shows as a broader silhouette |
| Belly / core | core | soft belly, then a firm "belt line"; belt gear sits here |
| **Tail** | legs (quads, hamstrings/glutes, calves) | thin noodle wisp, scalloped lobes, a full sturdy swirl tail |
| Head top / face | (none: level and stage) | sweatband, crowns and expressions sit here |

- **Skipped leg day:** a buff upper body on a droopy, ultra-thin fading tail (mockup `ghost-growth.png`).
- **Tail-specific juice:** the tail also drives the float bob. A weak tail gives a wobbly, low hover; a strong tail gives a stable, high float.
- **Gear anchors:** `head` (sweatband/crown), `ears/head-side` (headphones), `belly` (belt), `hand` (dumbbell), `tail` (tail ribbon/leg warmers → "tail warmers").

**Animation approach:**
1. **v1: sprite sheets in Flame.**
   - Per starter, each loop is about 6–8 frames: idle float, wave, flex, curl, squat-bob, bench, celebrate, and sad.
   - Play them with `SpriteAnimationComponent` (`SpriteAnimation.fromFrameData`, ~10–12 fps), layered on top of the procedural float bob and squash/stretch tween.
   - Frames are drawn at the size tier of the *dominant* part. Arms and tail tiers are composited as separate layers where the pose allows. Otherwise, use a per-tier sheet for the hero loops only.
2. **Drafting frames.**
   - Option A: Flare edit with the locked character sheet → a 6-frame grid (as in `ghost-workout-sprites.png`).
   - Option B: generate a short AI image-to-video clip of the pose loop (e.g. a fal image-to-video model from the character sheet on a flat background), then extract frames with `ffmpeg -vf fps=12`.
   - Then pick key frames, remove backgrounds, align to the baseline/anchor and pack into an atlas (`create-game-assets`).
   - These are drafts. A human cleanup pass fixes arcs, timing and on-model details (`game-feel`: anticipation, overshoot, settle).
3. **Later: Spine** (`spine_flutter`, paid license).
   - One shared ghost skeleton (body, arms, tail chain bones). It gives a naturally swishy tail with mesh deform.
   - Starters and size tiers become skins and attachments.
   - It replaces most per-tier sprite sheets once the art set grows.

**Concept-test findings from `ghost-workout-sprites.png`:**
- Character consistency across 18 frames is good.
- Motion arcs are uneven: several frames are near duplicates, the curl arm swaps sides, and the bench "lying" pose reads as sitting.
- So AI frame grids are fine for previz, but production loops need a cleanup pass or the Spine route.

---
## 17. Hero character and style lock (v4 → v6)
**Decision (Oct 30, 2026): the hero is Zeek, a green alien.** Mockups: `mockups-v6/zeek-sheet.png` (front + 3/4 turnaround, Standard / Buff Lv50 / Skipped leg day, expressions Chill / Smirk / Hyped / Tired) and `mockups-v6/zeek-home.png` (spaceship-garage home gym). Zeek's design comes from `mockups-v5/alien.png` (row 7), recolored from lavender to green at Fernando's request.

**Style decisions that led here:**
- **v4:** v3 Puff read as "too childish". Three grown-up directions were tested: A Streetwear, B Lo-fi Night, C Retro Pixel (`mockups-v4/`).
- **v5 picked a hybrid:** A's face and attitude (half-lidded eyes, slight smirk, **no blush**, grown-up proportions, no giant baby head) plus B's palette and light (deep teal, dusty plum, warm lamp amber; soft painterly rendering; thin brown linework; cream serif headings). Target: cute but adult-appealing (18–35), unisex. Retro Pixel (C) is parked as a possible cheap alt-skin/event style.
- **v5 species lineup:** frog, cat, bear, mushroom, robot, ghost, then two aliens (`mockups-v5/`). Fernando picked the alien Zeek.
- **Originality:** keep Zeek clearly away from E.T., grey-alien tropes, Stitch, Toy Story aliens and Among Us.

**Zeek model notes** (lock these in every fal prompt; pass `zeek-sheet.png` as the first `image_urls` entry):
- Skin: fresh minty-lime / pistachio green, with darker forest-green accents (freckle spots on head top and shoulders, antenna stalks, elbow/knee shading). Never gray or lavender.
- Large dark almond eyes drawn half-lidded; slight smirk; no blush.
- Two short antennae with glowing amber tips (a natural emote channel: glow on PR, droop when tired).
- Slim, humanoid, grown-up proportions; three-toed feet.
- Default outfit: terracotta knit sweatband, teal tank with a small cream leaf logo, black gym shorts with a white stripe.

**Why Zeek works for the paper doll (§4):** a humanoid build slices cleanly into head / torso / arms / legs, every tier is visible (tank and shorts show arms, chest and legs), and stick legs make the clearest "skipped leg day" read of any species tested.

**Starter roster** (replaces §11's Sprout/Pip/Mochi/Morel and §16's ghost set; same mechanics):

| Starter | Look | Legs part | Availability (proposal) |
|---|---|---|---|
| **Zeek** (hero) | green alien, sweatband, teal tank | stick → muscular legs | free, default |
| **Hops** | sage frog, backwards cap, terracotta tank | frog legs | free |
| **Puff** | mint ghost, hoodie, sweatband | tail (see §16) | free |
| **Glorp** | mint jelly alien, plum towel | 4 tentacles | coin-unlock (~500) |

- Glorp is proposed as the coin-unlock because its translucent jelly rendering is the costliest to keep on-model across tiers and animation frames. Revisit if Fernando wants a different split.
- Puff and Glorp need non-leg "legs" parts (tail, tentacles), so `rig.json` names the slot `legs` generically and each starter maps its own art to it.
- Lineups for Mochi (cat), Bruno (bear), Spore (mushroom) and Bolt (robot) are kept in `mockups-v5/` as future unlockables.

**Home-gym theme:** the v6 default room is a cozy spaceship garage: a riveted hull, a porthole with a ringed planet, a "ZERO-G GAINS" neon sign, plants, a record player and tea. The UI and layout stay the same as v2–v5.

**Art-pipeline update (§13):** the style lock is now `mockups-v6/zeek-sheet.png` plus `mockups-v6/zeek-home.png` (replacing `ref/reference.png` and the Sprout sheet).

