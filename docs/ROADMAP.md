# Pocket Gains: status and roadmap

Audit date: 31 Oct 2026. This repo is the design, art, and 3D-asset snapshot. It is not the app. Phase 1 is this document only: no pipeline rewrite, no Flutter project.

The owner is Fernando. The hero is **Zeek**, a mint-green alien whose body changes one muscle group at a time as real workouts are logged. Levels and lifetime XP never go down. Displayed size can shrink (the "skipped leg day" gag) and then grow back faster (muscle memory).

## Which document wins

The markdown files disagree, because the design moved from Rive, to a Flame paper doll, to a rigged glTF, and the older sections were left in place. When they conflict, use the later source:

| Topic | Use this | Ignore this until it is edited |
|---|---|---|
| Look, Zeek model notes, home gym | `plan.md` §17 and `README.md` | `plan.md` §10 (cozy v2), §16 (Puff as hero) |
| Training buddies | `progression.md` §7: **Zeek, Kaito, Momo** | `plan.md` §17 roster (Hops, Puff, Glorp). Those mockups exist; no 3D was built for them |
| XP, levels, shape-key weights, strength bonus | `progression.md` and `progression_sim.py` | `plan.md` §3 (`log2` volume formula, 3–4 sprite tiers) |
| Runtime | `README.md` + `research/3d-tools.md`: **Flutter + `flutter_scene`**, one GLB, morph weights | `plan.md` §1 and §4 (Flame paper doll). `plan.v2-rive.bak.md` (Rive; already rejected) |
| Gear in the file that exists | Separate nodes on `3d/zeek_v3_rigged.glb`, toggled with `extras.visible_default` | `research/3d-tools.md` suggestion of `KHR_materials_variants` (not in the export) |
| Logging UX | `mockups-ui/ux-notes.md` | — |

`ref/babyghosts/SOURCE.md` is a mood board only. Those images are third-party and must not be copied or fed to a generator.

## Product vision (from the docs)

Log a real workout. Zeek gets visibly stronger in the muscles that workout trained. Skip legs and the legs go thin, with a comedic "SKIPPED LEG DAY" state. A single session should be visible immediately (pump, veins, a flex). Permanent growth stays slow: about a year of 3–4 sessions a week to max the body (`progression.md` goal, and the simulator hits it).

**Features that are specified, and not built as an app:**

- Onboarding: name, bodyweight (optional; required only for the strength bonus), buddy pick (Zeek / Kaito / Momo). Stats belong to the player, so switching buddy does not reset the body.
- Fast set logging: one-tap "same as last time", thumb-zone steppers, undo instead of confirm, rest timer, haptics, PR badge, per-muscle XP pops on the body (`mockups-ui/ux-notes.md`).
- Per-muscle progression for nine regions, plus a noodle/imbalance shape, a temporary pump, and a separate "strength density" look for people who lift heavy (`progression.md` §1–§3, §9).
- Account ranks Noodle → Bronze → Silver → Gold → Platinum → Legend. Platinum and Legend require legs (ratio under 1.5). Optional prestige resets the account level only, never the body.
- Coins, a cosmetic shop, a decoratable home gym, quests, and a buddy that nudges at most once a day. No pay-to-win. Coins never buy XP.
- HealthKit / Health Connect write, local notifications, later cloud sync and cosmetic IAP.
- Three themes change the character, the room, the UI palette, the quip voice, and the aura. They do not change the math.

**Stated next steps already in `README.md` (30 Oct 2026):** finish Zeek v3 (Mixamo retarget, then a GLB for `flutter_scene`), take Kaito and Momo through the same pipeline after that, and spike `flutter_scene` on a real iPhone and Android. The retarget and the GLB export have since landed in `3d/zeek_v3_rigged.glb` (see below). The Flutter spike has not, and the app is not in this repo.

## What is in the repo

There is no application. No `pubspec.yaml`, `package.json`, Xcode project, Gradle project, or Unity project. `flutter` and `blender` are not on this machine. The Flutter prototype is described as a separate Cursor Origin draft and was not available to this audit.

| Path | State |
|---|---|
| `plan.md`, `progression.md`, backups, `mockups-ui/ux-notes.md`, `research/3d-tools.md` | Design. Complete enough to build against, with the conflicts in the table above |
| `progression_sim.py` | The only program that runs here. Ports the §8 knobs. **This is the growth spec.** The app should call the same functions, not a second formula |
| `mockups/` through `mockups-v7/` | fal image mockups. v6 locks Zeek (`zeek-sheet.png`, `zeek-home.png`). v7 is Kaito and Momo, still marked in progress. UI screens are in `mockups-ui/` |
| `prototype-art/zeek/` | Superseded 2D paper doll. Real PNGs (not LFS) plus `rig.json` (noodle / normal / buff parts, anchors). Tools are PIL scripts with the same `/workspace/gym-app/...` paths. Fallback if the 3D runtime fails on device, not the current direction |
| `3d/tools/v2_*.py`, `v3_*.py` | Headless Blender 4.2 pipeline. Each step opens the previous `.blend` and writes the next. Paths are absolute and point at `/workspace/gym-app/3d`, which is the live copy this repo was snapshotted from (`README.md`). They do not run from this checkout as-is |
| `3d/zeek_v3_rigged.glb` | **The runtime asset.** Inspected this run (see Build). v1 is an unrigged Tripo mesh. v2 is rigged with shape keys and no animation clips |
| `3d/mixamo/*.fbx` | 11 Mixamo clips. Retargeted into the v3 GLB. Bench press is not one of them; it is hand-keyed in `v3_07_props_aura.py` |
| `3d/kaito/`, `3d/momo/` | Tripo H3.1 multiview meshes, about 2 million triangles, no rig, no shape keys (`3d/NOTES-kaito-momo.md`). Janus failures are the `*_v1_janus.glb` files; do not use those |
| `3d/mocap/` | CMU BVH, Mesh2Motion human GLBs, Quaternius UAL1 and UAL2 (CC0 `License.txt` is present). Not retargeted onto Zeek |
| `3d/previews/` | Renders and turntables, including v3 stills and per-clip mp4s. All of these are Git LFS pointers in a smudge-skipped clone |

### Tech stack the docs commit to

- **App:** Flutter. Widgets for logging, shop, stats. `flutter_scene` (`SceneView`) for Zeek. Riverpod, go_router, Drift. Flame only if the home-gym room stays 2D, or as the fallback sprite host. Rive is dropped.
- **Character:** one glTF binary, Mixamo-named skin, morph targets per muscle, gear as extra skinned meshes that carry the same morph names.
- **Not the stack:** Unity, React Native, Expo, a web three.js app, or an ML model inside the client.

`research/3d-tools.md` (30 Oct 2026) picks `flutter_scene` because it exposes morph weights and skinning. Thermion is the backup. Pre-rendered sprites are plan C. `three_js` is called out as unsafe for morphs on some Android devices. The package is pre-1.0 and wants a recent Flutter with Flutter GPU enabled.

### Data model

There is no database in this repo. The intended tables are in `plan.md` §2 and §12, tightened by `progression.md`:

- `Exercise(id, name, primaryMuscle, secondaryMuscles[], mechanic)`
- `Workout`, `SetEntry(weightKg, reps, rpe or RIR, isPR)`
- Per muscle, **two XP tracks**: `lifetimeXP` (level, never decays) and `sizeXP` (the morph, decays). Plus `lastTrainedAt` and peak size for the muscle-memory multiplier
- `Profile` (account XP, rank, streak), `Wallet` / `CoinLedger`, gear, room JSON

Muscles that have a morph today: `chest`, `shoulders`, `arms_biceps`, `arms_triceps`, `back_lats`, `abs_core`, `legs_quads`, `legs_glutes`, `legs_calves`, and `noodle`. `strength_dense` is specified in `progression.md` §9.4 and is **not** in the GLB.

`progression_sim.py` tags a small exercise set (bench, incline, fly, ohp, lateral, row, pulldown, curl, pushdown, squat, leg press, rdl, calf). Primary gets 100% of the set, each helper gets 50%. There is no 80-exercise library yet (`plan.md` MVP item 2, possibly seeded from wger; that license still needs a check before any copy).

## Build and run (this machine, 31 Oct 2026)

Nothing here is an app, so there was nothing to `flutter build` or `npm run`.

| Check | Result |
|---|---|
| `flutter` | Not installed. No `pubspec.yaml` to build |
| `blender` | Not on `PATH`. `apt-cache search '^blender$'` returned no package. The pipeline was not installed or re-run. It needs Blender 4.2, the LFS `.blend` files (~471 MB), and the scripts' `/workspace/gym-app` prefix |
| Git LFS | `git-lfs` 3.8.0 is installed. This clone had `GIT_LFS_SKIP_SMUDGE=1`, so **174 files (~1.08 GB)** were 130-byte pointers: every `.glb`, `.blend`, `.fbx`, `.mp4`, `.bvh`, and the png/jpg files under `3d/` |
| `git lfs pull --include="3d/zeek_v1.glb,3d/zeek_v2_rigged.glb,3d/zeek_v3_rigged.glb"` | Succeeded. Those three files were parsed and then left as LFS objects. They are not part of this change |
| `python3 progression_sim.py` | Failed first: `ModuleNotFoundError: No module named 'matplotlib'` (numpy 1.26.4 was already present). After `pip install matplotlib`, the script ran and printed **`CHECKS PASSED`**. Chart path: `research/progression_sim.png` (output matched the committed chart; not part of this change) |

Sim numbers that matched `progression.md`: a regular 4×/week lifter is about 30% / 63% / 86% / 95% / 99% size at months 1 / 3 / 6 / 9 / 12, Legend at 10.4 months, and nobody is over 25% on any muscle after 5 sessions. A chest-only program leaves legs at 0 and caps the account at Gold (level 63). A 4-set chest session from zero is **+88 XP → size 0.034** (level 2); a PR on that session adds 22 XP → size 0.042.

To run the only program in a fresh checkout:

```bash
git lfs install
git lfs pull    # ~1.1 GB; required before any Blender step or before opening previews
python3 -m pip install matplotlib
python3 progression_sim.py
```

The Blender steps will not run until the checkout is at `/workspace/gym-app` or the absolute paths in `3d/tools/*.py` and `prototype-art/tools/*.py` are pointed at the repo root. That path change is real work and was deliberately not done in this pass.

## What the v3 GLB actually contains

Parsed from `3d/zeek_v3_rigged.glb` (9,178,956 bytes, Khronos glTF Blender I/O v4.2.70). This is the file to load. Do not load v1 or v2 for the app.

**Body.** `Zeek_Body`: 16,849 verts, 28,499 tris, skinned to `Zeek_Rig`. That count matches the decimate in `v2_prep.py` (`DECIMATE` ratio `28500 / n0` on `alternates/zeek_base_tripoh31_raw.glb`), not a hand retopo. `zeek_v1.glb` is an earlier unrigged Tripo export: 79,162 verts, 147,192 tris, no skeleton. The raw alternate was not pulled in this audit, so its triangle count is unverified. 28.5k is enough for a first device spike. Elbows, fingers, and UV stretching are the quality ceiling to look at before calling the mesh final.

**Skeleton.** 53 joints. Mixamo names (`mixamorig:Hips` through fingers) plus `Antenna_L_01..03` and `Antenna_R_01..03`. `HeadTop_End` is present and marked non-deforming in the v3 rig script.

**Morph targets on `Zeek_Body`, all weights 0:**

`arms_biceps`, `arms_triceps`, `shoulders`, `chest`, `back_lats`, `abs_core`, `legs_quads`, `legs_glutes`, `legs_calves`, `noodle`

Same names are copied onto the clothes that have to grow: tank and gold chain (upper-body keys + noodle), wrist wraps (biceps, triceps, noodle). Headband, beanie, sunglasses, and the face cards have **no** morphs. There is no `strength_dense` key and no separate hamstring key (RDLs credit `legs_glutes` and `back_lats` only, so the back of the thigh will not grow).

**How the keys were made.** `v3_02_shapes.py` pushes vertices radially around the bone axis, masked by skin weights and by which way the surface faces (front of the upper arm = biceps, back = triceps), then Laplacian-smooths. Chest, lats, glutes, and abs are sculpted as gaussian pushes, including a six-pack. Noodle is the inverse: skinny limbs and a narrower torso, and it is what the skipped-leg-day ratio drives. These are real morph targets, not a runtime bone-scale trick.

**Gear and expressions are nodes, hidden or shown.** `extras.visible_default` on the exported nodes:

| On by default | Off by default |
|---|---|
| Body, smirk face card, beanie, tank, gold chain | Headband, wraps, sunglasses, grin / grit / tired faces, dumbbells, barbell, bench, aura shell, aura flames |

The style lock in `plan.md` §17 is a **terracotta sweatband**, teal tank, and black shorts, not a beanie and a gold chain. Shorts are painted into the body, not a separate mesh. The spike should pick the starter outfit on purpose (headband on, beanie and chain off) and not trust `visible_default` as the design.

Face expressions are four alpha-card meshes (`Zeek_Face_Grin`, `Grit`, `Smirk`, `Tired`), not blend shapes. Show one.

**Animations (12), sampled on all 53 joints (translation, rotation, and scale):**

| Clip | Length | Use |
|---|---|---|
| `Zeek_BreathingIdle` | 10.0 s | Home idle, loop |
| `Zeek_MutantFlexingMuscles` | 4.7 s | Flex, PR, pump pose |
| `Zeek_BicepCurl` | 5.9 s | Curls. Show both dumbbells |
| `Zeek_AirSquat` | 1.9 s | Squat, leg press |
| `Zeek_BenchPress` | 3.6 s | Bench and incline. Hand-keyed, not Mixamo. Show barbell and bench |
| `Zeek_Lifting` | 7.2 s | Generic barbell stand-in for row / RDL / deadlift. Show barbell |
| `Zeek_PushUp` | 1.6 s | Push-up |
| `Zeek_Burpee` | 3.2 s | Burpee |
| `Zeek_JumpingJacks` | 1.1 s | Jumping jacks |
| `Zeek_BicycleCrunch` | 1.1 s | Core |
| `Zeek_Victory` | 4.5 s | Level-up / rank-up |
| `Zeek_RunningTired` | 7.0 s | Gassed, decayed, or end of a hard session |

There is no deadlift, overhead press, row, calf raise, or fly clip. Antenna bones are not in the Mixamo sources, so these clips do not droop or jiggle the antennae. Glow-on-PR is not a separate emissive mesh on the antenna tips.

**Look in the file vs look in the stills.** `v3_09_export.py` strips the inverted-hull outline and writes Principled BSDF materials named `*_Toon_PBR`. The glTF only uses `KHR_materials_emissive_strength`, on the aura. Vascularity and definition are Blender render effects. The body node carries `extras.vascularity = 0` and nothing in the app can drive it until a custom `flutter_scene` `.fmat` exists. The v3 preview stills will look punchier than the GLB on a phone. That is expected for the first spike.

**Other mesh cost.** An aura shell (`Zeek_Body.001`, also 28,499 tris, same 10 morphs) is parented and hidden. Leave it off. Default-on meshes are about 46k triangles (body 28.5k, chain 7.4k, tank 4.1k, beanie 3.9k, smirk card 2.1k). Fine for one character. Kaito and Momo at ~2M tris are not.

**Rig defect to look at, not to block on.** Each hand has both `*HandPinky*` and `*HandLittle*` (six finger chains). `v3_01_rig.py` grew a bone chain per mesh island it found in the decimated hand. If the curl shows an extra digit, delete one chain in Blender and re-export. Do not retarget from scratch first.

## 3D pipeline recommendation

Keep what v3 already is. Do not switch the growth method, and do not regenerate Zeek from a new image-to-3D model until a side-by-side beats the Tripo mesh on the orthographic refs in `3d/refs*` (Hunyuan 3.1 Pro already lost that comparison; the contact sheets are in `3d/previews/`).

### Growth: morph targets, not bone scaling

Bone scaling an upper arm makes the whole limb thicker, including the elbow, and it cannot separate biceps from triceps, push a pec shelf forward, or draw a six-pack. Clothes skinned to that bone balloon at the joint. The v3 keys already do the thing bone scale cannot: radial growth about the bone, masked by facing, with torso shapes sculpted on top, and the same deltas copied onto the tank and the wraps so the shirt grows with the chest.

Use bone scale only as a debug stand-in if a morph fails to import. Do not ship it.

`strength_dense` (thicker neck, traps, forearms, a "packed" torso for strong-but-lean lifters) should be an 11th morph, sculpted the same way, including on the tank. It is driven by the strength index S, not by muscle size. It is the main Blender job left on Zeek, and it is not required for the first playable.

### Logged work → morph weight

Port `progression_sim.py`. One logged working set becomes a stimulus `s` in about 0–1.25 (Epley e1RM, proximity to the 90-day best or an RIR override, and a heavy-set floor so a triple at 90% counts like a hard 8). Warm-ups are 0. Sum `s` onto the primary muscle and `0.5 * s` onto each helper for the calendar day. Turn that into XP:

```
XP = 160 * (1 - exp(-n / 5)) * recovery
```

Recovery is ×0.4 if that muscle was trained under 20 hours ago, ×0.7 under 44 hours, else ×1.0. The first 200 raw XP per muscle per week count in full, the rest at 10%, hard cap 230, then multiplied by the strength muscle bonus (at most ×1.20) after the cap. A PR adds 25% of that muscle's session XP, capped at 40, once per muscle per session.

Two tracks:

```
size     = min(1, (1 - exp(-sizeXP / 2600)) / 0.985)    # 1.0 near 10.9k size XP
level    = 1 + floor(49 * size(lifetimeXP))             # 1..50, from lifetime XP only
shapeKey = min(1, size(sizeXP) + pump)                  # the weight written to the GLB
```

`pump` is `0.12 * min(1, n_today/6)` plus 0.03 on a PR muscle. Full for 60 minutes, gone by 3 hours. It is added in the client on top of the saved size. It is not persisted as XP.

`noodle` is not a muscle. It is the imbalance of average upper size over average lower size: 0 below a ratio of 1.5, 1 at a ratio of 3. Upper is chest, shoulders, both arm keys, and back. Lower is quads, glutes, calves. Drive it on the body and on every mesh that has the `noodle` target (tank, chain, wraps).

Decay (size track only, after 7 untrained days, 1% of size XP per day, floor 70% of peak) and the ×2 muscle-memory rate live in the same file. Account level, ranks, and the strength index S are in `progression.md` §4 and §9. S needs bodyweight newer than 60 days and confirmed e1RMs on at least 3 of the 5 big lifts. No bodyweight means no strength bonus, and the rest of the game still works.

The first screen does not need the weekly cap, decay, or S. It needs `s → XP → size → morph weight` for chest, triceps, and shoulders, saved across launches.

### Idle, flex, lift

On the home screen, loop `Zeek_BreathingIdle`. After a set, play the clip for that exercise once (table above), then return to idle. On a PR or a level-up, play `Zeek_MutantFlexingMuscles` or `Zeek_Victory`. While `pump > 0`, the idle can cross-fade a little of the flex. Antenna droop and tip glow are a follow-up: a short additive clip on `Antenna_*`, plus an emissive material on the tips. Do not block the spike on that.

Props: the curl clip does not move the dumbbells by itself. `extras` on the prop nodes and the action notes in `v3_07_props_aura.py` say which props belong to which clip (`Zeek_BicepCurl` → both dumbbells, `Zeek_Lifting` → barbell, `Zeek_BenchPress` → barbell and bench). Show those nodes for the length of the clip. They are parented in the scene, not skinned.

### Where each tool runs

Nothing in this list runs inside the app. The phone plays one GLB.

| Job | Where | Tool | Notes |
|---|---|---|---|
| Concept sheets, UI mockups, transparent cutouts | fal.ai | GPT Image / the Flare edit path already used for `mockups-ui/` | Locked refs: `mockups-v6/zeek-sheet.png` first in `image_urls`. Do not send `ref/babyghosts/` |
| Image → mesh for a new character | fal.ai | `tripo3d/h3.1/multiview-to-3d` | Slot order that worked: front, side_left (faces image-left), back, side_right. The swapped order produced the Janus meshes |
| Optional local image-to-3D experiments | RTX 4090 | [microsoft/TRELLIS](https://github.com/microsoft/TRELLIS), [Tencent-Hunyuan/Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) | Not run on these refs. Hunyuan 3.1 Pro on fal already lost to Tripo for Zeek. A local checkpoint has to beat `3d/previews/compare_*` before it replaces the hero. Treat licenses as unverified until read |
| Decimate, rig, shape keys, gear, export | Blender 4.2, scripted | The `3d/tools/v3_*.py` chain. glTF export via Blender's Khronos exporter (Apache-2.0) | Production path. Output is the GLB |
| Auto-rig a new body (Kaito, Momo, antennae) | 4090 or the CPU box, then Blender | [VAST-AI-Research/UniRig](https://github.com/VAST-AI-Research/UniRig) (MIT code and weights) to seed a skeleton, then Rigify or the existing Mixamo-named builder | Mixamo and AccuRIG do not rig antennae. Keep deform bone names Mixamo-compatible so the 12 clips retarget |
| Fast skinned preview | Browser | [Mesh2Motion/mesh2motion-app](https://github.com/Mesh2Motion/mesh2motion-app) (MIT) and [mesh2motion-assets](https://github.com/Mesh2Motion/mesh2motion-assets) (CC0) | Humanoid template. Antennae come back as head weights; add bones after |
| Motions that Mixamo does not have (deadlift, a real row) | 4090, multi-camera | [freemocap/freemocap](https://github.com/freemocap/freemocap) (AGPL tool, captured motion is yours) | Do not ship SMPL-output models (GVHMR, WHAM, 4D-Humans, MoMask, MDM). The code license does not make the body license commercial. Full list and the territory issue on HY-Motion are in `research/3d-tools.md` |
| Retarget | Blender | The retarget already in `v3_06_anim.py`. Rokoko Studio Live or Expy Kit if a new skeleton does not share Mixamo names | |
| Toon shader, outline, vascularity | In the app, later | `flutter_scene` `.fmat`, inverted-hull mesh if you re-enable the outline at export | Not a Blender render |
| Play the character | Phone | [`flutter_scene`](https://pub.dev/packages/flutter_scene) | Morph weights, skinning, node show/hide. No fal, no Blender, no PyTorch |

Asset hygiene worth stealing from [gamedev-skills/awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills) (Apache-2.0): `disciplines/create-game-assets` (topology, a GLB as the runtime file, a provenance note per generated mesh). There is no Blender skill in that repo. `repo-gamedev/` is gitignored; re-clone it if you want it.

Kaito and Momo stay references until Zeek is on a phone. Their notes already say the production steps: retopo toward 8–15k tris, the shared joint list, the same 11 shape-key names, face cards for expressions. Kaito needs longer limbs. Do not import the 2M-triangle scans into Flutter.

## Milestones

Smallest thing a person can actually see, first. Design systems that are already written down (coins, prestige, quests, the full shop, HealthKit, IAP) wait until a logged set changes Zeek and the change is still there tomorrow.

### M1. Zeek on a phone

A new minimal Flutter app, or the existing Origin draft moved into this repo, with one `SceneView`.

- Load `3d/zeek_v3_rigged.glb`.
- Hide every node whose `extras.visible_default` is false, then turn the headband on and the beanie and gold chain off, so he matches the v6 sheet.
- Show only the smirk face card.
- Two controls write morph weights on **every** mesh that has that target (`Zeek_Body`, tank, chain, wraps): `chest` and `noodle`.
- Loop `Zeek_BreathingIdle`. A button plays `Zeek_BicepCurl` and shows the dumbbells for the length of the clip.
- Run it on one iPhone (M2 Max, Xcode) and one Android device. `flutter_scene` needs Flutter GPU enabled.

**Done when** dragging chest from 0 to 1 grows the pecs and the tank together, noodle thins the limbs, and the curl plays without the mesh exploding. If an extra finger shows, that is the Pinky/Little cleanup, then a re-export. If morph weights do not move the mesh on device, stop and try thermion before any new art. The paper doll in `prototype-art/zeek/` is the fallback only after both 3D runtimes fail.

### M2. One exercise changes the body, and a relaunch keeps it

On top of M1. Bench press only.

- Log weight and reps. No library, no templates yet.
- Port set stimulus, the session XP curve, and `size()` from `progression_sim.py` for chest (primary), triceps, and shoulders (helpers). Skip the weekly cap, decay, and the strength bonus.
- Persist `sizeXP` and `lifetimeXP` for those three muscles (Drift, or a single JSON file if Drift slows the spike).
- The home morph weights are the saved sizes. A 4×8 hard bench from a new profile should land near **chest size 0.03**, matching the sim's +88 XP example within a small tolerance you write down next to the test.
- Undo the last set.

**Done when** killing the app and reopening it shows the same chest.

### M3. The rest of the muscles, and the clip that matches the set

- All nine keys plus `noodle`, using the sim's exercise list (about 13 movements).
- Summary plays the clip from the table above; otherwise idle. Props show and hide with the clip.
- Skipped-leg-day: after a chest-only log, `noodle` is visibly up and quads stay at 0.
- Weekly fuel cap and the 7-day size decay can land here or immediately after. They are pure functions of the same file. Lifetime level still never drops.

**Done when** a squat grows quads and glutes, a curl grows biceps, and a chest-only week makes the legs thinner without lowering the chest level.

### After that, in order

4. **Pump and expressions.** Add `pump` on top of saved size for three hours. Swap the face card (smirk / grit / tired / grin) from session state. PR plays the flex clip. Still no custom shader.
5. **Starter gear and the locker, cosmetic only.** Toggle the nodes that already exist (headband, beanie, wraps, sunglasses, chain). No shop economy required to prove the switch.
6. **`strength_dense` morph.** Sculpt it in Blender on the body and the tank, export, drive it from S. This is the first milestone that needs the 4090 and Blender. Also the moment to fix the extra finger if M1 did not.
7. **Toon `.fmat`.** Outline and a vascularity/definition ramp so the phone is closer to `3d/previews/v3/`. Until then the PBR GLB is an accepted look.
8. **Pipeline hygiene, whenever it blocks a re-export.** `git lfs pull` in the README's setup, and a single repo-root prefix instead of `/workspace/gym-app` in the Blender scripts. Do not rewrite the steps themselves.
9. **Real logging UX from `mockups-ui/ux-notes.md`.** Same-as-last-time, rest timer, haptics, the muscle filter. This is what has to beat a boring logger. The character is not a reason to ship a slow set entry.
10. **Kaito, then Momo.** Same skeleton names, same morph names, their own room and palette (`progression.md` §7). Retopo first. The 2M-tri scans stay out of the app.
11. **Deadlift and a real row**, captured with FreeMoCap on the 4090 and retargeted. `Zeek_Lifting` is the stand-in until then.
12. **Coins, quests, ranks, prestige, notifications, HealthKit, App Store.** The design in `progression.md` §4–§6 and `plan.md` §5–§7 is the spec. Cosmetic only. No XP for sale.

## Working, stubbed, missing

**Working as files, verified this run**

- Design for the fantasy, the math, the UX, and the tool shortlist.
- `progression_sim.py` (with matplotlib installed). Checks passed.
- `3d/zeek_v3_rigged.glb`: skin, 10 morphs, 12 clips, gear nodes, face cards, props. Parsed, not rendered on a phone.
- 2D paper-doll PNGs and `rig.json`, if the 3D path is abandoned.

**Stubbed or half-done**

- v3 "toon" materials are PBR.
- Antenna emotion, vascularity, definition, aura tiers: designed, and partly present as hidden meshes, not driven.
- `strength_dense`: designed, not sculpted.
- Kaito and Momo: concepts and raw scans.
- Bench press animation: procedural, not mocap.
- Blender scripts: complete enough to have produced v3, not runnable in this checkout (paths, no Blender, LFS blends not pulled).
- Default outfit flags do not match the style lock.
- Extra finger bones.
- `plan.md` §1–§4 still describes the paper doll.

**Missing**

- The Flutter app, the database, the exercise library, accounts, the shop, notifications, HealthKit, and any on-device test of morph weights.
- Hamstring morph, deadlift clip, row clip.
- A validation script that checks bone names, morph names, and sockets before export (`progression.md` §7 asks for one; it does not exist).
- `character.json` sidecars. The GLB `extras` are the stand-in.

## Do not do next

- Do not regenerate Zeek from a new image-to-3D model.
- Do not import Kaito or Momo into the app at scan density.
- Do not put a diffusion, mocap, or auto-rig model in the client.
- Do not ship clips whose body is SMPL.
- Do not build the coin economy, prestige, or the isometric room before M2 is saved to disk.
- Do not revive Rive, or the Hops / Puff / Glorp roster, unless Fernando overrides `progression.md` §7.
