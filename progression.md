# Pocket Gains: Progression, Levels, Prestige, Buddy & Themes (v1 design)

**v1.1 (Oct 30):** adds the **strength factor** (§9): relative strength speeds up rank (up to 1.5×) and muscle growth (up to 1.2×), heavy low-rep sets are now fully credited, and there's a new "Strength" visual tier.

Builds on `plan.md` §3/§5/§12 (per-muscle XP split 100% primary / 50% helpers, 70% shrink floor, leg-day ratio > 2, ~120 coins/day cap, ranks Noodle→Legend). Every number here is a **starting value** in the tuning table (§8) and in `progression_sim.py`, which re-checks the targets.

**Design goals (from Fernando):**
- One session is *visibly* good, and a PR is a little better.
- The drama is temporary (pump, veins, aura); permanent growth is small and earned.
- Nobody is maxed after 5 sessions. A full max takes about 12 months of consistent 3–4×/week training.

Muscles and shape keys (0–1):

| Muscle | Shape key |
|---|---|
| chest | `chest` |
| shoulders | `shoulders` |
| biceps | `arms_biceps` |
| triceps | `arms_triceps` |
| back/lats | `back_lats` |
| core | `abs_core` |
| quads | `legs_quads` |
| glutes | `legs_glutes` |
| calves | `legs_calves` |
| (imbalance) | `noodle` |

Material layers: `vascularity`, `definition`, `pump_flush` (0–1 per region). FX layer: `aura`.

---

## 1. Session → per-muscle XP

**Step 1, set stimulus (sets × reps × relative intensity).** Each logged working set gets a stimulus `s`:
```
setE1RM   = weight × (1 + reps/30)                 # Epley; bodyweight moves use bw × coef (+ added load)
effort    = clamp(setE1RM / best90dE1RM, 0, 1)     # how close to your current best (optional RIR input overrides:
                                                   #   RIR 0 = 1.0, 1 = 0.95, 2 = 0.9, 3 = 0.85, 4+ = 0.8)
load      = weight / best90dE1RM                   # how heavy the bar is relative to your current max
heavy     = 1.10 × clamp((load − 0.70) / 0.15, 0, 1)   # 0 below 70% e1RM, full 1.10 at ≥ 85% e1RM
repFactor = max(clamp(reps, 0, 15) / 8, heavy)     # 8 reps = 1.0; a near-max single/triple/five = 1.10
s         = min(1.25, effort² × repFactor)         # a hard set of ~8 ≈ 1.0; a warm-up at 60% ≈ 0.25
```
**v1.1 fix: heavy low-rep sets.** Before, a triple only got `3/8` of a set (with a 0.6 floor), so powerlifters were punished. Now any set at ≥ 85% of your e1RM is worth at least a hard 8 (`sim: set_stimulus()`):

| Set | s |
|---|---|
| 8 reps, 1–2 RIR, 75% e1RM | 0.90 |
| **3 reps, 1–2 RIR, 90% e1RM** | **0.99** (≥ the hard 8 ✅) |
| 1 rep, 0 RIR, 100% (a true max) | 1.10 |
| 5 reps, 1–2 RIR, 85% | 0.99 |
| 5×5 @ 80%, 2–3 RIR (per set) | 0.59 |
| 12 reps to failure | 1.25 |
| 3 easy reps at 60% | 0.24 |

Heavy singles can't be farmed for volume: the per-day diminishing curve (Step 3) and the weekly budget (Step 4) still apply, and singles above 95% count at most 5 per exercise per day.
- On the first-ever log of an exercise, working sets count as `s = 1.0` and seed `best90dE1RM`.
- Sets marked as warm-ups count 0.

**Step 2, effective sets per muscle.** `n[m] = Σ s (primary) + 0.5 × Σ s (helpers)`. This sum accumulates over the **whole calendar day**, so splitting a workout into three sessions can't farm XP.

**Step 3, session XP with diminishing returns:** `XP = 160 × (1 − e^(−n/5)) × recovery`.

| effective sets n | 1 | 2 | 3 | 4 | 6 | 8 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|---|---|---|
| XP | 29 | 53 | 72 | **88** | 112 | 128 | 138 | 152 | 157 |

- Recovery multiplier for the same muscle: trained less than 20 h ago ×0.4, less than 44 h ago ×0.7, otherwise ×1.0.

**Step 4, weekly budget per muscle.** The budget is per calendar week and resets Monday, so it can be shown as a meter.
- The first **200 raw XP** are credited at 100%. That's about 2 solid sessions, which is the **2×/week sweet spot**.
- Raw XP above 200 is credited at 10%.
- Hard cap: **230 credited XP per muscle per week**.
- UI: each muscle shows a little "weekly fuel" ring. When it's full, Zeek says "chest is cooked this week, hit something else."

**PR bonus:**
- **What counts as a PR:** a new best e1RM for an exercise (reps ≤ 12), or a rep PR at ≥ 80% of your best.
- **Bonus:** +25% of that muscle's session XP, capped at 40 XP.
- **Limits:** at most 1 PR bonus per muscle per session and at most 3 per session.

**Two XP tracks per muscle:**
- `lifetimeXP` only goes up. It drives the muscle **level** and account XP, so levels never drop.
- `sizeXP` drives the **shape keys** and can decay (below).

**Decay and maintenance:**
- **Maintenance:** any session with ≥ 3 effective sets on a muscle within 7 days stops that muscle's decay.
- **Decay:** after 7 untrained days, `sizeXP` loses 1% per day, floored at **70% of that muscle's peak sizeXP**.
- **Muscle memory:** while `sizeXP` is below its peak, gains on the size track are ×2 until it's back at peak.
- **Sim result:** a 4-week break at month 5 takes average size from 0.85 to about 0.72, and it's fully back about 6 weeks later.
- **UI:** a decayed muscle shows "Lv 42 · rusty" with a soft dust FX, never a red error.

**Anti-cheese** (soft, since this is a solo app):
- **Implausible loads:**
  - Trigger when e1RM jumps more than 12% over your 90-day best, or on a first log above bodyweight ratios (bench 2.0×, squat 2.8×, deadlift 3.2×, curl 0.9×, OHP 1.4×).
  - You get a "Whoa, new PR?" confirm sheet.
  - Until you confirm, the set is computed at effort 1.0 against the old best, and no PR bonus is given.
- **Caps:**
  - Reps above 30 count as 30.
  - More than 12 sets of one exercise in a day are ignored.
  - At most 40 credited sets per day.
  - Plus the daily diminishing curve and the weekly 230 cap.
- **Backdating:** entries more than 48 h old give XP but no coins and no PR FX.
- **Farming check (sim):** 40 sets of curls every day for 5 days gives only 230 XP, which is 8.6% biceps size.
- **Strength bonus anti-cheese:** see §9.5 (bodyweight gate, confirmed e1RMs only, 3-lift minimum, jump flags).

---

## 2. XP → level (1–50) → shape key

```
size  = min(1, (1 − e^(−sizeXP / 2600)) / 0.985)     # 0–1 visual size; reaches 1.0 at about 10.9k XP
level = 1 + floor(49 × size(lifetimeXP))              # 1–50; level ≈ size% / 2
shapeKey[m] = min(1, size(sizeXP) + pump[m])          # what the rig receives
noodle = upperAvg < 0.15 ? 0 : clamp((upperAvg / max(lowerAvg, 0.02) − 1.5) / 1.5, 0, 1)
```
- `upperAvg` covers chest, shoulders, arms and back.
- The "Skipped leg day" state turns on when the ratio is above 2 (noodle ≥ 0.33). The ratio at 3 gives full noodle.
- **Beyond Lv 50:** lifetime XP keeps flowing into **Mastery stars**, one per 2,000 XP per muscle. They unlock cosmetic skin variants (more "shredded" definition maps, vein patterns), so there's a long-term per-muscle goal after the body is maxed.

**Milestones** from the sim: regular is 4×/week upper/lower; casual is 2×/week full body. Values are the average size of all 9 muscles.

| Milestone (avg size) | Regular: sessions / time | Casual: sessions / time | Target |
|---|---|---|---|
| 10% ("Toned") | 5 / 1.5 wk | 4 / 2 wk | — |
| **30%** | **18 / 1.0 mo** | 14 / 1.6 mo | ~1 mo ✅ |
| **60%** | **46 / 2.8 mo** | 38 / 4.6 mo | ~3 mo ✅ |
| **90%** | **114 / 6.9 mo** | not reached (89% at 12 mo) | 6–9 mo ✅ |
| **99–100% (max)** | **193 / 11.6 mo** | not reached | ~12 mo ✅ |
| Largest single muscle after 5 sessions | 12.8% | 17.0% | "not maxed" ✅ |

(v1.1 numbers include the regular's small strength bonus, ×1.02–1.08 on account XP and ×1.01–1.03 on muscle XP; v1.0 was 47 / 115 / 197 sessions. Powerlifter numbers are in §9.6.)

**What one session and one PR do** (a 4-hard-set chest session, n = 4):

| When | Permanent | Temporary |
|---|---|---|
| New user (size 0) | +88 XP → chest **0 → 3.4%**, Lv 1 → 2 | pump **+0.08** for ~3 h (visibly beefier) |
| …plus a PR | +22 XP → **4.2%** total | pump **+0.11**, vascularity **+0.25** for 24 h, "PR Spark" aura for 24 h, antenna glow |
| Mid-journey (size 0.61) | **+1.3%** (+1.7% with PR) | same pump/FX |
| Late (size 0.91) | **+0.3%** (+0.4% with PR) | pump mostly shows as veins, definition and flush (little shape headroom left) |

**This is where the drama lives.** The permanent bump is small but real. The pump is big and immediate: it plays on the summary screen as a "pump meter" filling, then fades over 3 hours, which gives users a reason to open the app after the gym.

---

## 3. Visual rewards ladder

**Per-muscle size tiers** (UI labels, plus the extra layers per region):

| Size | Tier | `definition` | `vascularity` (base) | Notes |
|---|---|---|---|---|
| 0–0.10 | Noodle | 0 | 0 | default body |
| 0.10–0.30 | Toned | 0–0.2 | 0 | first visible change, about week 2 |
| 0.30–0.60 | Fit | 0.2–0.5 | 0–0.15 (arms only) | ab lines start at core ≥ 0.45 |
| 0.60–0.90 | Buff | 0.5–0.8 | 0.15–0.5 (arms, shoulders) | |
| 0.90–0.99 | Swole | 0.8–0.95 | 0.5–0.8 | |
| 1.0 | Peak | 1.0 | 0.8–1.0 | Mastery stars take over |

- Definition = `smoothstep(0.1, 0.95, size)`. It is nudged −0.1 when a muscle is "rusty" (decaying).

**Pump** (temporary, after logging; realistic and fun):
- **Size:** `pump[m] = 0.12 × min(1, n_today/6)`, plus 0.03 on muscles with a PR.
- **Timing:** full for 60 minutes, then eases to 0 by 3 hours.
- **Extra layers during the pump:** `definition` +0.1, `vascularity` +0.15, and `pump_flush` (a slight warm skin tint).
- **Display:** Home shows "PUMPED · 2h 10m" with a small flex idle.

**Aura tiers.** Three sources stack into one aura FX:
- **Shape/intensity from the weekly streak** (weekly goal hit):
  - 2 wk **Ember** (feet glow)
  - 4 wk **Glow** (rim light)
  - 8 wk **Flare** (rising particles)
  - 16 wk **Nova** (full aura)
  - 52 wk **Orbit** (orbiting ring)
  - A missed week drops **one** tier, not to zero. 1 free "rest week" token per 8 weeks.
- **PRs, temporary:**
  - **PR Spark** lasts 24 h.
  - 3 PRs in a week gives **Hot Streak** for 3 days (crackle FX).
- **Strength aura variant ("Iron"):** at strength tier Advanced+ the aura gets heavy, low-hanging particles instead of floaty ones (§9.4).
- **Color from prestige:** P0 neutral white-gold, P1 cyan, P2 amber, P3 crimson, P4 violet, P5 gold, P6 silver-white, P7 aurora gradient, P8 void with stars, P9 solar, P10 cosmic rainbow.

---

## 4. Account level, ranks, prestige

**Account XP** = Σ (credited muscle XP × **strength account multiplier**, §9) + bonuses (weekly goal +150, quests).
- Level formula: `Lv = 1 + floor((acctXP / 95)^(1/1.5))`, max 100.
- Lv 100 takes ~94k XP. A regular reaches Legend in about 10.5 months (sim, before quest/goal bonuses).

| Rank | Levels | Regular reaches | Casual reaches | **Powerlifter** reaches (no BW logged) |
|---|---|---|---|---|
| Noodle | 1–4 | start | start | start |
| Bronze | 5–19 | week 1 | week 2 | week 1 |
| Silver | 20–39 | 1.0 mo | 1.5 mo | 1.0 mo (1.2) |
| Gold | 40–64 | 3.0 mo | 5.0 mo | **2.9 mo** (3.5) |
| Platinum | 65–89 (**needs leg ratio < 1.5**) | 6.3 mo | 10.6 mo | **6.2 mo** (7.6) |
| Legend | 90–100 (**needs leg ratio < 1.5**) | 10.4 mo | — | **9.9 mo** (—, Lv 87 at 12 mo) |

- **The chest-only bro caps at Gold** (Lv 63 after 12 months) because untrained muscles give no account XP.
- The Platinum/Legend leg gate is the joke: "Legends have legs."

**Prestige (Call of Duty style).** At Lv 100 you can choose to **Prestige** (P1–P10), then **Cosmic Legend** (endless stars).
- **What resets:** account level goes to 1 and the rank badge restarts at Noodle with your prestige emblem on it.
- **Shorter later climbs:** prestige climbs need **35% of the first climb's XP**, about 3–4 months for a regular. That keeps the CoD "one more prestige" rhythm without a year-long grind.
- **What you get each time:**
  - A prestige emblem, shown on the rank badge, profile and loading screens.
  - An exclusive aura **color** (§3).
  - A themed **gear set**: P1 Orbit Visor, P2 Comet Chain, P3 Solar Gloves, and so on.
  - 1,000 coins.
  - A **new home-gym theme or app theme** at P1, P3, P5, P7 and P10.
  - Prestige-only quests.
- **What you keep:** all gear, coins, decor, muscle levels, Mastery stars, streak and aura tier.

**Body reset: two options considered.**
- **A. Hard reset:** the body drops to a 50% baseline and regrows (classic CoD feel).
  - Pro: you get the regrowth fantasy again.
  - Con: it lies about your real training, feels like losing months of work, and fights the "app mirrors your real body" core idea.
- **B. Body stays:** only account level and rank reset. ✅ **Chosen.**
  - The body is your real training history, so we never take it away.
  - The prestige "glow-up" comes from new aura colors, emblems, gear and themes, plus Mastery definition/vein skins.
  - **Optional opt-in "Fresh Start" mode** for players who *want* the regrowth fantasy: the visual body starts at 50% and regrows **3× faster** back to the true size. It's purely cosmetic and can be toggled off at any time.
- **Why prestige doesn't feel punishing:** it's optional and has no deadline. The button says "Ascend", not "Reset". Nothing is taken except the level number, and the cycles are shorter.

---

## 5. Economy tie-ins

**Coins** (from `plan.md` §12, unchanged): workout +20, exercise +5 (cap 6), PR +10 (cap 3), weekly goal +50, streak milestones, level-up and rank-up.
- The workout cap stays ~120/day.
- Quests and milestones sit **outside** the daily cap but have their own weekly limit (~200 coins/week from quests).
- Additions:
  - Prestige +1,000.
  - Mastery star +50.
  - Comeback quest +100.
- **Pacing:** ~300–400 coins/week for a regular, which covers one nice item per 1–2 weeks.

**Gear unlock gates** (an `unlockRule` JSON per item). Accessories are sorted by *how* you get them:

| Route | Examples | Gate |
|---|---|---|
| Shop | beanies, tanks, shades, decor | coins (50–1,500), some + rank |
| Earned | Squat Crown (quads Lv 25), Iron Pec Plate (chest Lv 30), Vein Tattoo (any muscle Mastery ★1) | muscle level / Mastery only, not buyable |
| Rank | Bronze sweatband → Legend cape | rank |
| Prestige | per-prestige sets + aura colors | prestige |
| Quest chains | Leg Warmers (3× Leg Day Hero), Rubber Chicken (joke) | quest completions |
| Theme | per-theme outfits | theme owned; universal items fit all characters via sockets (§7) |
| Seasonal | rotating 4–6 items/week | coins, time-limited |

**Quests** (1 daily + 3 weekly, picked from a pool, weighted toward your weakest spots):

| Quest | Condition | Reward |
|---|---|---|
| Daily Rep | log ≥ 3 working sets | 15c |
| **Leg Day Hero** (offered when legs are lagging) | ≥ 6 effective leg sets this week | 60c + Leg Warmers progress (1/3) |
| Balanced Week | every region trained ≥ 1× | 80c |
| Sweet Spot | every trained muscle hit exactly 2× | 60c |
| PR Hunter | 1 confirmed PR | 40c |
| Back Attack (when mirror muscles ≫ back) | ≥ 8 back sets this week | 60c |
| Comeback (after ≥ 14 days off) | 1 session | 100c + "Welcome back" emote |
| Theme story chain | e.g. "Fix Zeek's ship": 10 sessions | decor piece per chapter |

---

## 6. Workout-buddy layer

**Rules:**
- No guilt and no body-shaming. Never mention weight or appearance negatively.
- A missed day is never a "failure". It's "the bar misses you."
- At most 1 nudge per day and at most 3 unprompted pushes per week.
- Quiet hours are respected, and each notification type can be turned off.
- After a long break the buddy **celebrates** the return; it doesn't scold.

| Trigger | Reaction (on Home / summary) | Push notification (in character, opt-in) |
|---|---|---|
| Session logged | flex + pump glow, quip about the muscle | — |
| PR | antenna/eyes glow, trophy appears on the shelf, "PR Spark" aura | — |
| Legs lagging (ratio > 2) | wobble-legs idle, "my legs are buffering…" | Thu evening: "leg day quest is up. my calves believe in us." |
| Weekly fuel full on a muscle | "chest is cooked this week. back day?" | — |
| Streak 4/8/16 weeks | aura tier-up animation | "4 weeks straight. that's orbit-level consistency." |
| 3 days since last session (during a weekly goal) | sits on bench, tossing a kettlebell | "free for a quick one? even 3 sets counts." |
| 10+ days off | wakes up from a nap, happy to see you | at most once: "no pressure. i saved your spot." |
| Comeback session | confetti + "muscle memory: 2× regrowth active" | — |
| Pump active | idles flexing in the mirror | (optional) "pump ends in 30 min. selfie?" |
| Rank-up / prestige | big ceremony, new emblem | — |

- **Quips:** a short-lines JSON per theme keyed by trigger, with 5–10 variants each and no repeats within 7 days.
- **Context:** quips can include context (exercise name, PR weight, weeks of streak).

---

## 7. Onboarding: character / theme select

Screen 1 of onboarding: "Pick your training buddy". There are 3 cards with a live idle preview, and you can switch later in Settings without losing progress. The stats belong to the player, not the character.

| | **Zeek (Cosmic)** | **Kaito (Shonen)** | **Momo (Cozy)** |
|---|---|---|---|
| Character | green alien, sweatband, teal tank | grown-up anime gym guy (mid-20s), spiky black hair with red tips, red headband, black sleeveless gi-collar hoodie with gold flame, wrist wraps, charcoal joggers (`mockups-v7/kaito/`) | plush-like mochi creature-person: round head, small bear ears, top bun with pink scrunchie, sage sleeveless hoodie, lavender bike shorts (`mockups-v7/momo/`) |
| Home gym | spaceship garage, porthole, neon | rooftop dojo gym at dusk, city skyline, punching bag, banners | sunlit plant-filled studio, rug, fairy lights, tea corner |
| UI palette | forest green / amber / cyan (current) | ink navy / red / gold, speed-line accents | warm cream / blush / sage, rounded soft cards |
| Voice | dry, chill alien ("we lifting, earthling?") | hype rival-friend ("your power level is rising!") | warm, encouraging ("tiny steps still count ♡") |
| Aura style | cosmic particles | shonen flame aura (power-up) | sparkles and petals |
| Accessories | space gear (visor, antenna caps) | headbands, weighted gi, scouter-style shades | beanies, scrunchies, plush backpack |
| Theme-specific FX | antenna glow on PR | speed lines + aura burst on PR | heart sparkles + bounce on PR |

**What a theme changes:** character, home gym scene, UI color tokens and fonts, quip voice pack, aura style, and the theme accessory set. **What it does not change:** stats, XP math, quests and the economy.

**One rig and shape-key standard for every character:**
1. **Skeleton:** a Mixamo-named humanoid (`mixamorig:Hips`, `Spine`, `Spine1`, `Spine2`, `Neck`, `Head`, `LeftShoulder`, `LeftArm`, `LeftForeArm`, `LeftHand`, `LeftUpLeg`, `LeftLeg`, `LeftFoot`, `LeftToeBase`, and the right-side mirrors).
   - Every Mixamo workout animation (bench, squat, curl…) retargets to all characters unchanged. That's the "mix 'em all" plan for exercise animations.
   - Characters can differ in proportions; animations are retargeted per character once.
2. **Shape keys:** the same 11 names on every body mesh (`chest … legs_calves, noodle`, plus `strength_dense` from v1.1, §9.4), with the same meaning: 0 = starting body, 1 = Peak.
   - Each character's artist decides *how big* 1.0 looks (Kaito can go more extreme; Momo goes rounder and softer). The game logic only sends 0–1.
3. **Material params:** `vascularity`, `definition` and `pump_flush` are per region (arms, torso, legs) and exposed by the same names in every character's shader/material.
4. **Sockets:** empties parented to bones with fixed names:
   - `socket_head`, `socket_face`, `socket_neck`, `socket_back`, `socket_waist`, `socket_wrist_L/R`, `socket_hand_L/R`, `socket_feet`
   - `aura_root` on `Spine1`
5. **Clothing and accessories follow muscles:**
   - Clothing meshes carry the **same muscle shape keys** (a tank has `chest`, `back_lats`, `abs_core`, `shoulders`), driven by the body's values. Tops therefore stretch with growth.
   - Rigid accessories just ride sockets, with a per-character offset in `character.json`.
6. **Validation:** a Blender script checks bone names, shape-key names, sockets and material params before export, and fails the build if anything is missing.
   - Non-humanoid future starters (ghost, frog) map their own art onto the same keys (e.g. ghost tail = legs keys).

`character.json` per theme:
```json
{ "id": "zeek", "glb": "zeek.glb", "skeleton": "mixamo", "shapeKeys": ["chest","shoulders","arms_biceps","arms_triceps","back_lats","abs_core","legs_quads","legs_glutes","legs_calves","noodle","strength_dense"],
  "materialParams": ["vascularity","definition","pump_flush","chalk"], "sockets": {"socket_head": {"bone":"mixamorig:Head","offset":[0,0.12,0]}},
  "room": "space_garage", "uiTheme": "cosmic", "voicePack": "zeek_en", "auraStyle": "cosmic" }
```

---

## 8. Tuning knobs and simulation

| Knob | Value | Effect |
|---|---|---|
| `K_SIZE` | 2600 | overall speed of visual growth (±10% ≈ ±1 month to 90%) |
| `SIZE_NORM` | 0.985 | XP at which size hits 1.0 (~10.9k) |
| `SESSION_XP_MAX` / `SESSION_SETS_K` | 160 / 5 | per-day XP ceiling and how fast extra sets stop paying |
| `HELPER_SHARE` | 0.5 | helper-muscle credit |
| `RECOVERY_MULT` | <20 h ×0.4, <44 h ×0.7 | penalty for hitting the same muscle back-to-back |
| `WEEKLY_SOFT` / `WEEKLY_EXCESS` / `WEEKLY_CAP` | 200 / 10% / 230 | the 2×/week sweet spot and the anti-bro cap |
| `PR_BONUS_FRAC` / `PR_BONUS_CAP` | 25% / 40 XP | permanent PR reward |
| `PUMP_MAX` (+PR) | 0.12 (+0.03), 3 h | size of the temporary "drama" |
| `DECAY_GRACE` / `DECAY_RATE` / `DECAY_FLOOR` / `MEMORY_MULT` | 7 d / 1%/d / 70% / 2× | how much breaks hurt and how fast you bounce back |
| `ACCT_A`, exponent | 95, 1.5 | account level pace (Legend ~10.5 months) |
| `HEAVY_LOAD_LO` / `HI` / `HEAVY_CREDIT` | 70% / 85% / 1.10 | how heavy a low-rep set must be to count as a full set |
| `STR_ACCT_BONUS` / `STR_MUSCLE_BONUS` | 0.50 / 0.20 (× S^1.5) | strength speed-up of rank / of growth (§9) |
| `STR_MIN_LIFTS` / `STR_BW_MAX_AGE` / `STR_JUMP_FLAG` | 3 lifts / 60 d / 12% | strength-bonus gates and anti-cheese |
| Prestige climb factor | 0.35 | ~3–4 months per prestige |
| Noodle ratio start/full | 1.5 / 3.0 | when skinny legs kick in |

**Simulation:** `python progression_sim.py` (needs numpy and matplotlib; a venv is at `/workspace/.venv-sim`).
- It simulates 12 months for Casual (2×/week full body), Regular (4×/week upper/lower), Chest-only bro (5×/week), Regular with a 4-week break, **Powerlifter** (4×/week heavy compounds) and the same powerlifter with **no bodyweight logged** (control: no bonus), with an 8% skip rate.
- Each user has a strength profile (e1RM/bodyweight per lift that climbs with practice), which drives the strength index S.
- It plots per-muscle size, account level and S×100 (red) to `research/progression_sim.png` (2×3 grid).
- It asserts the checks below.

**Results:**
- ✅ Nobody exceeds 25% on any muscle after 5 sessions. The highest is 16.9% (casual chest/back).
- ✅ **Chest-only bro:**
  - Chest reaches 36% at 1 month, 71% at 3 months and 100% at about 10 months (the weekly cap keeps extra volume to ~1.2× the regular pace).
  - **Legs, back and core stay at 0%**, so noodle is maxed and the "Skipped leg day" state is permanent.
  - Account level is stuck at Gold (Lv 63).
- ✅ **Regular:** 30% / 63% / 86% / 95% / 99% at months 1 / 3 / 6 / 9 / 12, matching the targets.
- ✅ **Casual:** 21% / 46% / 71% / 85% / 91%. That's slower, but still visibly growing every month.
- ✅ **Farmer** (40 sets of curls a day for 5 days): 8.6% biceps.
- ✅ **Powerlifter:** ranks a bit faster than the regular (Gold 2.9 vs 3.0 mo, Legend 9.9 vs 10.4 mo) and **+28% account XP vs the same lifter without the bonus** (≤ 1.5× ✅). Details in §9.6.
- ✅ Bench-only bro and the no-bodyweight powerlifter get **no** strength bonus; a +15% e1RM jump is flagged; a heavy triple ≥ a hard 8.


---

## 9. Strength factor (powerlifter bonus, v1.1)

**Why:** Fernando wants strong lifters to rank up a bit faster. Strength is the most honest "I've put in the years" signal a lifting app has, so it boosts **pace** (rank and growth speed), never the body cap or the leg gate.

### 9.1 Strength index S (0–1)
For each of the 5 big lifts, take your **confirmed** best e1RM over the last 90 days divided by your **bodyweight**, then place it on the tier ladder:

| Lift (e1RM ÷ bodyweight) | Beginner | Novice | Intermediate | Advanced | Elite |
|---|---|---|---|---|---|
| Squat | 0.75 | 1.25 | 1.50 | 2.25 | 3.00 |
| Bench press | 0.50 | 0.75 | 1.00 | 1.50 | 2.00 |
| Deadlift | 1.00 | 1.50 | 2.00 | 2.50 | 3.00 |
| Overhead press | 0.35 | 0.55 | 0.75 | 1.00 | 1.35 |
| Barbell row | 0.50 | 0.75 | 1.00 | 1.50 | 1.75 |

```
tierPos(lift) = continuous 0..4 (0 = at/below Beginner line, 4 = Elite), linear between lines
S             = Σ tierPos over the 5 lifts / 20          # missing lifts count 0
S             = 0 if fewer than 3 lifts have a confirmed e1RM, or bodyweight is older than 60 days
```
- The table is the **male default** (standard strength-standard ratios, rounded). Settings offer a "standards" picker: *Default*, *Female* (≈ ×0.65 upper / ×0.75 lower), *Masters 40+ / 50+ / 60+* (age-adjusted, ×0.9 / ×0.8 / ×0.7). The picker never shows the user's sex/age anywhere else.
- **DOTS option:** users who compete can switch S to use their DOTS score from the squat + bench + deadlift total (S tiers at DOTS 200 / 280 / 340 / 400 / 480 ≈ the same 5 lines), which is the fairer bodyweight scaling for heavy lifters.
- Rolling 90-day best, so S decays slowly during long breaks instead of dropping overnight.
- Dumbbell / machine variants map to the lift with a coefficient (DB bench ×1.2 per pair total ÷ 2 … configurable), but only barbell/standard variants count toward Elite.

### 9.2 Multipliers
```
accountMult = 1 + 0.50 × S^1.5      # account XP / rank pace, up to 1.50× at Elite
muscleMult  = 1 + 0.20 × S^1.5      # muscle (size + lifetime) XP, up to 1.20× at Elite
```
| Tier (all 5 lifts) | S | Account / rank XP | Muscle XP |
|---|---|---|---|
| Beginner | 0.00 | ×1.00 | ×1.00 |
| Novice | 0.25 | ×1.06 | ×1.02 |
| Intermediate | 0.50 | ×1.18 | ×1.07 |
| Advanced | 0.75 | ×1.32 | ×1.13 |
| Elite | 1.00 | **×1.50** | **×1.20** |

- The S^1.5 curve keeps the bonus small for novices (they already grow fast) and makes it meaningful once you're genuinely strong.
- **Applied after the weekly cap** (so the 230 cap effectively becomes 230 × muscleMult). Otherwise a strong user whose weekly fuel is already full would never feel the bonus.
- **What it does not change:** max body size (still 1.0), the leg-ratio gate for Platinum/Legend, the PR rules, coins. A bench-only lifter can't use it to skip legs: it needs 3 lifts, and missing lifts count 0.
- UI: a small "STR ×1.24" chip next to the account XP bar; tapping it shows the 5-lift tier ladder with "next tier at 140 kg squat".

### 9.3 Bodyweight gate
- Bodyweight is **optional**. Without it the bonus is simply off (the app says "add your bodyweight to unlock your strength bonus"). Nothing else needs it.
- Must be updated at least every 60 days to keep the bonus (one-tap "still 82 kg?" prompt). Stored locally; never shown on the character or to the buddy, and the buddy never comments on it (§6 rules).
- Weight changes > 5% in 7 days need a confirm (stops "log 40 kg bodyweight, get Elite").

### 9.4 "Strength" visual tier
A separate look track, driven by S (not by size), so a strong-but-lean lifter looks different from a pumped bodybuilder:

| S | Tier name | Body | FX |
|---|---|---|---|
| < 0.25 | — | — | — |
| 0.25–0.50 | **Solid** | `strength_dense` 0.3: slightly thicker neck, traps, forearms, wrists; flatter, more "packed" torso silhouette | chalk puff on hand clap in the idle |
| 0.50–0.75 | **Dense** | `strength_dense` 0.6: thicker joints, wider stance, heavier walk cycle | chalk-dust burst on each logged heavy set, light ground thud |
| ≥ 0.75 | **Iron** | `strength_dense` 1.0: full "built like a fridge" look; belt + wrist-wrap cosmetics unlock | heavy-impact ground crack + dust ring on PRs, camera shake, "Iron" aura variant (heavy low-hanging particles, metallic rim light) |

- **Rig:** an 11th shape key `strength_dense` on every body (and on clothing, like the muscle keys), plus a material param `chalk` (0–1, white dust on hands/forearms). Both are added to the §7 standard and the `character.json` `shapeKeys` list. Theme flavor: Zeek gets meteor-impact craters, Kaito a shonen ground-crack with speed lines, Momo a soft "boing" dust cloud with a tiny star.
- The pump still plays on top; `strength_dense` stacks with the size keys (artists sculpt it on the Peak body too).

### 9.5 Anti-cheese
- **Confirmed e1RMs only:** a new e1RM more than **12% above the 90-day best within 14 days** is held as "unconfirmed" (§1 "Whoa, new PR?" sheet). It only counts toward S after a repeat set within 7 days or an attached video. Sim: `e1rm_flag()`.
- **Plausibility ceiling:** first logs above the Elite line × 1.15 always need confirmation.
- **e1RM sources:** only sets of 1–10 reps at RIR ≤ 3 (Epley gets unreliable above 10).
- **Bodyweight:** see §9.3. No bodyweight = no bonus.
- **3-lift minimum, missing lifts count 0:** you can't max S from one specialty lift.
- **Pace limit:** S can rise at most 0.10 per 30 days, so a dishonest jump still can't instantly unlock ×1.5.

### 9.6 Simulation: powerlifter (4×/week, mostly heavy low-rep compounds)
Template: Mon squat 5×3 @88% + bench 4×5 + row + RDL; Tue deadlift 4×3 @88% + OHP 4×5 + pulldown + curls; Thu bench 6×3 @88% + row + incline + pushdowns; Sat squat 4×5 @80% + deadlift doubles + OHP + leg press + calves. About 75% of sets are ≤ 5 reps at ≥ 80% e1RM. Strength starts at Intermediate (S 0.55 in month 1) and reaches Advanced (S 0.77) by month 12.

| Month | 1 | 3 | 6 | 9 | 12 |
|---|---|---|---|---|---|
| Strength index S | 0.55 | 0.63 | 0.71 | 0.75 | 0.77 |
| Account multiplier | ×1.20 | ×1.25 | ×1.30 | ×1.32 | ×1.34 |
| Account level (PL) | 20 | 41 | 64 | 84 | **100** |
| Account level (same PL, no bodyweight) | 18 | 36 | 56 | 72 | 87 |
| Account level (regular) | 20 | 39 | 62 | 81 | 99 |
| Avg size, upper (PL) | 0.29 | 0.62 | 0.86 | 0.95 | 0.98 |
| Avg size, lower (PL) | 0.24 | 0.56 | 0.79 | 0.87 | 0.92 |

- 12-month account XP: **PL 97.1k** vs the same lifter without bodyweight **75.8k (×1.28)** vs regular **92.2k**.
- Ranks: PL Gold 2.9 mo / Platinum 6.2 / Legend 9.9 vs regular 3.0 / 6.3 / 10.4. **A bit faster, as intended**, and the no-bodyweight control never reaches Legend in year 1.
- Body: PL chest and quads max at ~12 months, like the regular. Calves/arms lag (0.75–0.9) because the program barely trains them, which is true to life and shows up as a slightly "blocky" look, which the Strength tier embraces.
- Largest muscle after 5 sessions: 14.2% (still well under 25%).
