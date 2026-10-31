# Pocket Gains

Fernando's personal gym game, built in Flutter. You log real workouts, and your avatar gets visibly stronger **one muscle group at a time**. Train chest and the chest grows. Skip leg day and you get toothpick legs (plus a comedic "SKIPPED LEG DAY" card). Size decays slowly if you stop training, but earned levels and XP never go down.

The hero avatar is **Zeek**, a minty-green 3D alien. He has half-lidded almond eyes, a smirk, and two antennae with amber tips that glow on a PR and droop when he's tired. His default outfit is a terracotta sweatband, a teal tank with a cream leaf logo, and black gym shorts. Two more selectable "training buddy" themes, **Kaito** (shonen) and **Momo** (cozy), are in design.

> This repo holds **design docs, art, the 3D pipeline and its assets**. The Flutter app prototype lives separately, in a **Cursor Origin draft** (see Status).
> Paths in the Blender scripts are absolute and point at `/workspace/gym-app/...`, the live working copy on the agent box. This repo is a staging snapshot of that folder (see "Re-syncing").

## Folder map

| Path | What it is |
|---|---|
| `plan.md` | Main feasibility and architecture doc: stack, data model, XP, avatar rendering, gear and ranks, MVP list, App Store notes, risks. §17 locks Zeek as the hero and his on-model notes. |
| `plan.v2-rive.bak.md`, `plan.v5-pre-zeek.bak.md` | Older snapshots of the plan, kept for history. |
| `progression.md` | Progression design v1: per-muscle XP from sessions, levels 1–50 mapped to **shape-key weights**, the visual rewards ladder, ranks and prestige, the coin economy, the workout-buddy layer, theme select (Zeek / Kaito / Momo), the strength factor. |
| `progression_sim.py` | Simulator for tuning the progression curves (output chart: `research/progression_sim.png`). |
| `mockups/` → `mockups-v6/` | fal image mockups (GPT Image on fal), one folder per style iteration: v1 dark/premium, v2 cozy, v3 ghost, v4 grown-up directions, v5 species lineup, **v6 Zeek sheet + home (style lock)**. |
| `mockups-ui/` | App screen mockups (home, exercise picker, set logger, rest timer, summary, muscle map, locker/shop), plus `ux-notes.md` and the prompts. |
| `mockups-v7/` | Theme characters **Kaito** and **Momo**: sheets, A-pose fronts, home gyms, and `drafts/`. Still in progress. |
| `prototype-art/` | The 2D paper-doll prototype: Zeek cut into per-part sprites with noodle/normal/buff tiers, `rig.json`, the cut/assemble tools, and bend checks. This was the earlier sprite approach; 3D is the current direction. |
| `ref/` | Style references (`reference.png`, `babyghosts/` with SOURCE.md). |
| `research/` | `3d-tools.md`: a shortlist of auto-riggers, animation sources, mocap, toon shading, and Flutter 3D runtimes, with license checks (**watch the SMPL non-commercial trap**). |
| `3d/` | Everything for the 3D Zeek (see below). |

### `3d/`

| Path | What it is |
|---|---|
| `zeek_v1.glb` | First Tripo-generated Zeek (raw, unrigged). |
| `zeek_v2.blend`, `zeek_v2_rigged.glb` | v2 result: rigged, with shape keys and gear. The GLB is the runtime export. |
| `alternates/` | Other generations compared during model selection (Tripo H3.1 raw and cleaned, Hunyuan 3.1 Pro). |
| `refs/`, `refs_v2/` | Orthographic turnaround refs fed to image-to-3D. |
| `tools/` | Headless Blender (and PIL/numpy) scripts. **`v2_*`** build v2 step by step: `v2_prep` (import and clean the Tripo mesh) → `v2_rig` → `v2_shapes` → `v2_legdef` → `v2_gear` → `v2_final` (preview renders) → `v2_anim` → `v2_export`. `v2_common` holds the shared scene, toon shader, outline, and camera code. **`v3_*`** rebuild from v2's rig: `v3_01_rig` (finger bones, antenna cleanup) → `v3_02_shapes` (dramatic radial growth) → `v3_03_face_bake` → `v3_04_face_mat` (expression decals) → `v3_05_gear`. The helpers are `v3_common`, `v3_face_draw`, `v3_gear_tex`, and `v3_tex_clean`. Also here: `preview.py`, `reorient.py`, and `topo.py`. |
| `v2work/`, `v3work/` | Numbered intermediate `.blend` per pipeline step (`01_…` → `0N_…`), plus `joints.json`, `fingers.json`, etc. Each script opens the previous step's file and saves the next. |
| `tex/` | Body basecolor, detail/normal maps, muscle masks, face expression decals (grin/grit/smirk/tired), and gear textures (beanie, headband, wraps, tank, leaf logo). |
| `mixamo/` | Mixamo clips (FBX): Air Squat, Bicep Curl, Push Up, Burpee, Lifting, Flexing, Idle, Victory, and others. These retarget straight onto the Mixamo-named rig. |
| `mocap/` | Extra motion sources: CMU BVH clips, Mesh2Motion human GLBs, and the Quaternius Universal Animation Library 1 & 2 (extracted, with their License.txt). |
| `previews/` | Renders: v1 turntable/contact sheet, Hunyuan-vs-Tripo comparisons, v2 states (base, outfit, chest day, leg day, maxed, noodle, flex.mp4), and `v3/` (in progress). |

## 3D pipeline

1. **Concept → model.** Orthographic refs (`3d/refs*`) go through **Tripo image-to-3D on fal**. Hunyuan was tested and lost (see `previews/compare_*`). The result is `alternates/zeek_base_tripoh31_raw.glb`.
2. **Blender 4.2 headless on the box.** Every step is a script (`blender -b -P 3d/tools/<step>.py`) that opens the previous step's `.blend` and saves the next. That makes the pipeline reproducible and lets an agent edit it.
3. **Rig.** A **Mixamo-named skeleton** (`mixamorig:*` bones) so Mixamo/UAL/CMU clips retarget with no remapping. **Antenna bones** are added for emotes (glow/droop/jiggle). v3 adds finger bones.
4. **Per-muscle shape keys.** Each muscle region (chest, back, shoulders, arms, core, quads, glutes/hams, calves…) gets its own key. The game drives them with 0–1 weights from the per-muscle level (`progression.md` §2). v3 makes the growth far more dramatic (radial volume about the bone axes plus sculpted torso pushes).
5. **Gear as separate meshes.** The tank, beanie, headband, wraps, gold chain, etc. are separate skinned meshes that carry the same shape keys, so clothes grow with the body. They're toggled at runtime.
6. **Look.** Toon shading plus an inverted-hull outline. Face expressions are texture decals, not geometry.
7. **Animation.** Mixamo clips first. Custom lifts (bench, deadlift…) come later from phone-video mocap on the 4090.
8. **Export → runtime.** One GLB with a skinned mesh, shape keys as morph targets, and gear as child meshes or `KHR_materials_variants`. **The runtime target is [`flutter_scene`](https://pub.dev/packages/flutter_scene)** in the Flutter app (morph weights, skinning, toon `.fmat`).

## Hardware split

- **Agent box (Linux):** Blender 4.2 headless, scripted pipeline steps, quick EEVEE/Workbench previews, fal calls.
- **RTX 4090 Windows desktop:** heavy rendering (Cycles, turntables), video-to-mocap, and UniRig/ML experiments.
- **M2 Max Mac:** Flutter iOS builds and on-device testing (Xcode).

## Status / next steps (as of Oct 30, 2026)

- **Zeek v3 in progress** (`3d/v3work`, `3d/tools/v3_*`, `3d/previews/v3`):
  - dramatic per-muscle growth (done in `02_shapes`, still being tuned)
  - face fixes: re-domed face, baked detail, and four expression decals
  - gear rebuilt (headband, wraps, beanie, tank)
  - **Mixamo retarget** of the `3d/mixamo` clips onto the v3 rig, then a GLB export for flutter_scene
- **Kaito and Momo themes:** character and home-gym mockups in `mockups-v7/` (drafts still iterating), defined in `progression.md` §7. They'll go through the same 3D pipeline after Zeek v3.
- **Flutter prototype:** lives in a **separate Cursor Origin draft**, not in this repo. Next: a flutter_scene spike with one Mixamo curl, two shape keys and one gear variant on a real iPhone (built on the M2 Max) and Android.

## Not in this repo

- `repo-gamedev/` is a third-party clone (gamedev-skills/awesome-gamedev-agent-skills, Apache-2.0). Re-clone it if you need it.
- Zip archives (`3d/mocap/*.zip`, `prototype-art/zeek-parts.zip`) are left out. Their contents are already extracted next to them.
- Also excluded: Blender `*.blend1` backups, virtualenvs, `__pycache__`, scratch/temp render frames, `.env`/secrets, and any file over 100 MB. See `.gitignore` / `.rsync-exclude`.
- **Git LFS** holds `*.glb *.blend *.fbx *.mp4 *.bvh *.npy` and all PNG/JPG under `3d/` (see `.gitattributes`). Run `git lfs install` before you clone.

## Re-syncing from the working copy

```bash
cd /workspace/pocket-gains-repo && rsync -a --delete --max-size=100m --exclude-from=.rsync-exclude --exclude=.rsync-exclude --exclude=README.md --exclude=.gitignore --exclude=.gitattributes /workspace/gym-app/ ./ && git add -A && git commit -m "Sync from gym-app $(date +%F)" && git push
```
