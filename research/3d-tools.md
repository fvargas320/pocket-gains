# Pocket Gains: 3D tools shortlist for the Zeek pipeline
_Research done Oct 30, 2026 (PT). I checked licenses and last activity on the live repo or vendor page. "Last push" is the date of the latest GitHub push. Research only: I installed nothing and signed up for nothing._

Legend: ✅ commercial use OK · ⚠️ OK with conditions · ⛔ non-commercial or research only (don't ship its outputs)

> **Big licensing trap: SMPL.** Most video-to-mocap and text-to-motion research models output **SMPL/SMPL-H** bodies, or were trained on **AMASS/HumanML3D/Human3.6M**. The SMPL model and these datasets are **non-commercial** unless you buy a license (Meshcapade sells SMPL commercial licenses). An MIT tag on the *code* does **not** make the *outputs* safe for a paid game. All of these are flagged ⛔ below.

---

## 0. The repos Fernando sent
**Likely source post:** https://x.com/badboyfoxy/status/2115834352223261002. The repo is linked in its self-reply https://x.com/badboyfoxy/status/2115834358863126885. ⚠️ I haven't confirmed this is the exact post Fernando meant. The other 17 replies don't link any other repos.

| Repo | License | Activity | Verdict for us |
|---|---|---|---|
| [gamedev-skills/awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills) | Apache-2.0 ✅ | 77 skills, last commit 2026-10-28 | **Moderately useful.** No Blender or rigging skill. Worth stealing: `disciplines/create-game-assets` (3D pipeline gates for topology, UVs, and rig; GLB as the runtime format; caution on AI-generated meshes; `provenance.md` license records; asset-manifest + report scripts), `shader-programming` (fresnel rim and outline notes), and `godot-shaders` (toon ramp reference). Use it for asset-hygiene and licensing records, not for Blender automation. |
| [scottstts/Threejs-Awesome-Graphics-Agent-Skills](https://github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills) _(bonus, same topic)_ | MIT ✅ | ★951, pushed 2026-10-22 | Only relevant if we prototype in three.js or web. Low priority. |

---

## 1. Auto-rigging (ranked for a cartoon alien with antennae)
| # | Tool | License / cost | Commercial | Antennae? | Use | Effort |
|---|---|---|---|---|---|---|
| 1 | **[Rigify](https://docs.blender.org/manual/en/4.2/addons/rigging/rigify/index.html)** (built into Blender) | GPL tool, rig output is yours, free | ✅ | **Yes.** Add `basic.copy_chain`/`limbs.super_finger`-style chains for each antenna, which gives proper bones and jiggle | Production rig. Export deform bones only to GLB | Medium (half a day to a day) |
| 2 | **[Mesh2Motion](https://app.mesh2motion.org)** ([repo](https://github.com/Mesh2Motion/mesh2motion-app)) | Code MIT, animation assets CC0 ([assets repo](https://github.com/Mesh2Motion/mesh2motion-assets), CC0, pushed 2026-10-29) | ✅ | Partly. Template humanoid skeleton fitted in the browser, antennae get skinned to the head (add bones afterwards in Blender) | Fastest skinned GLB with CC0 clips already attached, plus a retarget tool. Open-source Mixamo alternative, ★3.6k, pushed 2026-10-26 | Low |
| 3 | **[AccuRIG](https://actorcore.reallusion.com/auto-rig)** (Reallusion, free app) | Free. Rigged output of your own original character is yours to sell. ActorCore motions are under a separate EULA | ✅ (own char) | No. Humanoid only, so add antenna bones in Blender | Good humanoid weights and fingers | Low. Needs a Reallusion account, which I didn't sign up for |
| 4 | **[Mixamo auto-rigger](https://www.mixamo.com)** | Free with Adobe ID. Royalty-free in games, no attribution; no raw-file redistribution or ML training ([FAQ](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html)) | ✅ | No. Bipeds only, and big appendages can confuse it | Quick humanoid rig that matches the Mixamo clip library directly | Low. Needs an Adobe ID |
| 5 | **[UniRig](https://github.com/VAST-AI-Research/UniRig)** | Code MIT, HF weights MIT. ★1.9k, pushed 2026-06-04 | ✅ | **Yes.** Predicts arbitrary skeletons (trained on Rig-XL + VRoid/anime) | Experimental: try it on `zeek_v1.glb` on the 4090 or box to get a starting skeleton | Medium. Python/CUDA setup, results vary |
| 6 | [Puppeteer](https://github.com/Seed3D/Puppeteer) / [MagicArticulate](https://github.com/Seed3D/MagicArticulate) | Apache-2.0 code + weights. Pushed 2025-09 | ✅ | Yes (any object) | Research-grade alternative to UniRig. Puppeteer also does video-guided animation | Medium-high |
| 7 | [Tripo rig/animate API](https://developers.tripo3d.ai/en/docs/animations-rig) | Paid: rig 25 credits, retarget 10 credits/clip ($0.01/credit) ([pricing](https://developers.tripo3d.ai/en/pricing)) | ⚠️ per Tripo plan terms | No. Biped or quadruped presets only | Convenient since Zeek came from Tripo, but antennae stay unrigged | Low, paid |
| 8 | [Anything World](https://app.anything.world/) | Free tier is personal/student only. Paid from about $30/mo | ⚠️ requires an "Animated by Anything World" credit | Yes (creatures) | Not recommended (attribution + cost) | Low, paid |
| 9 | [RigNet](https://github.com/zhan-xu/RigNet) | GPL-3.0, last push 2024-11 | ✅ output, stale | Yes | Superseded by UniRig | High |
| – | [Auto-Rig Pro](https://superhivemarket.com/products/auto-rig-pro) | Paid (about $40) | ✅ | Yes | Best paid Blender option (rig + Smart retarget + game export) if we'll spend money | Low-medium |

**For Zeek:** Rigify, either from scratch or seeded by a UniRig/Mesh2Motion skeleton, is the only free route that gives the antennae real bones. Keep bone names Mixamo-compatible so retargeting stays trivial.

---

## 2. Workout animation sources
### 2a. Ready-made clips (ranked)
| # | Source | License | Commercial | What's there for us | Effort |
|---|---|---|---|---|---|
| 1 | **[Mixamo](https://www.mixamo.com)** | Adobe terms ([FAQ](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html)) | ✅ in-game, no raw-file redistribution | Reportedly Bicep Curl, Air Squat, Push Up, Jumping Jacks, Situps, Burpee, Kettlebell Swing, plus idles, cheers, victory, flex-style poses. **No bench press or deadlift that I could confirm** | Low (needs Adobe ID) |
| 2 | **[Mesh2Motion CC0 library](https://github.com/Mesh2Motion/mesh2motion-assets)** | CC0 | ✅ | Pushup, Jumping Jacks, Cheering, Victory, Victory Fist Pump, Power Up, Idle_A, Idle_FoldArms, Tired Hunched, plus CMU subject-91 clips | Low |
| 3 | **[Quaternius Universal Animation Library 1](https://quaternius.com/packs/universalanimationlibrary.html) / [2](https://quaternius.com/packs/universalanimationlibrary2.html)** | CC0 | ✅ | 250+ general clips (idles, jog, jump, crouch, dance, celebrate), Mixamo-retargetable. Few lifts | Low |
| 4 | **[CMU Graphics Lab mocap](http://mocap.cs.cmu.edu/)** ([BVH via cgspeed](https://sites.google.com/a/cgspeed.com/cgspeed/motion-capture/the-motionbuilder-friendly-bvh-conversion-release-of-cmus-motion-capture-database)) | "May be copied, modified, or redistributed without permission" ([FAQ](http://mocap.cs.cmu.edu/faqs.php)) | ✅ | Subj 13 #29–31 and 14 #6/14/20: jumping jacks, squats, side twists, stretches. Raw mocap, so it needs cleanup | Medium |

### 2b. Make our own (bench press, deadlift, curls, flex) from phone video on the 4090
| # | Tool | License | Commercial | Notes | Effort |
|---|---|---|---|---|---|
| 1 | **[FreeMoCap](https://github.com/freemocap/freemocap)** | AGPL-3.0 (tool). Your captured data is yours | ✅ outputs | ★10.6k, pushed today. Multi-webcam (2–4 cheap cams) to Blender rig. No SMPL. **Best free option for custom lifts** | Medium (camera setup + calibration) |
| 2 | **[BlendArMocap](https://github.com/cgtinker/BlendArMocap)** | GPL-3.0, MediaPipe | ✅ outputs | Single-camera, inside Blender, transfers to Rigify. Rougher depth; last push 2025-12 | Low-medium |
| 3 | **[Rokoko Vision](https://www.rokoko.com/products/vision)** | Free Starter plan: about 30 s/month video-to-motion, FBX export (BVH needs the $10/mo plan). Generated data can be used commercially | ✅ | Easiest, good for 1–2 short lifts per month. Needs an account (not created) | Low |
| 4 | **[HY-Motion 1.0](https://github.com/Tencent-Hunyuan/HY-Motion-1.0)** (text-to-motion) | Tencent HY-Motion community license | ⚠️ commercial OK, but **excludes EU, UK, and South Korea**. Over 1M MAU needs Tencent approval. Outputs on an SMPL-H skeleton (check SMPL terms) | Prompt "barbell deadlift" and get a clip. A global app store release conflicts with the territory exclusion, so legal review is needed | Medium |
| ⛔ | [GVHMR](https://github.com/zju3dv/GVHMR) | Research/educational/non-profit only | ⛔ | Best quality world-grounded video mocap, **non-commercial** | – |
| ⛔ | [VIBE](https://github.com/mkocabas/VIBE) | Non-commercial research license, stale (2023) | ⛔ | – | – |
| ⛔ | [SMPLer-X](https://github.com/MotrixLab/SMPLer-X) | S-Lab 1.0, non-commercial | ⛔ | – | – |
| ⛔* | [WHAM](https://github.com/yohanshin/WHAM), [TRAM](https://github.com/yufu-wang/tram), [4D-Humans](https://github.com/shubham-goel/4D-Humans)/[PHALP](https://github.com/brjathu/PHALP) | Code MIT, but **outputs are SMPL bodies** (SMPL is non-commercial) | ⛔* | Usable only for internal reference or a commercial SMPL license | – |
| ⛔* | [MotionBERT](https://github.com/Walter0807/MotionBERT) | Code Apache-2.0, trained on Human3.6M/AMASS (non-commercial data) | ⛔* | Research | – |
| ⚠️ | [EasyMocap](https://github.com/zju3dv/EasyMocap) | Project Registration License: free for research/personal, **commercial needs registration** | ⚠️ | – | – |
| ⛔* | Text-to-motion: [MoMask](https://github.com/EricGuo5513/momask-codes), [MDM](https://github.com/GuyTevet/motion-diffusion-model), [T2M-GPT](https://github.com/Mael-zys/T2M-GPT), [MotionGPT](https://github.com/OpenMotionLab/MotionGPT) | Code MIT/Apache, but **trained on HumanML3D/AMASS + SMPL** (non-commercial) | ⛔* | Fine for previs, don't ship the outputs | – |

\* = code license is permissive, but the outputs or data carry SMPL/AMASS non-commercial terms.

### 2c. Retargeting onto Zeek (in Blender)
| # | Tool | License | Commercial | Notes | Effort |
|---|---|---|---|---|---|
| 1 | **[Rokoko Studio Live for Blender](https://github.com/Rokoko/rokoko-studio-live-blender)** | LGPL-3.0, pushed 2026-10-29 | ✅ | Free retarget panel (bone-list mapping, T-pose). Works with Mixamo/BVH/FBX | Low |
| 2 | **[Expy Kit](https://github.com/pKrime/Expy-Kit)** | GPL | ✅ | Converts between rig conventions (Mixamo, Rigify, UE) and binds actions | Low-medium |
| 3 | [Diffeomorphic retarget_bvh](https://github.com/Diffeomorphic/retarget_bvh) | GPL-2.0+, pushed 2026-08 | ✅ | Good for CMU BVH | Low-medium |
| – | Auto-Rig Pro (paid) | Paid | ✅ | Most polished, if we buy it | Low |

---

## 3. Blender helpers (MCP, toon/outline)
| # | Tool | License | Commercial | Use | Effort |
|---|---|---|---|---|---|
| 1 | **[Blender Lab official MCP server](https://www.blender.org/lab/mcp-server/)** ([repo](https://projects.blender.org/lab/blender_mcp)) | GPL-3.0, v1.0.3 (2026-09-11) | ✅ | Agent-driven Blender scripting. **Needs Blender 5.1+**, so it fits Fernando's 5.2 desktop but not the box's 4.2.3. It runs LLM code unguarded, so use a sandboxed file | Low |
| 2 | **[mcp-for-blender](https://github.com/ahujasid/mcp-for-blender)** (formerly blender-mcp) | MIT, ★32.8k, pushed 2026-10-29 | ✅ | Popular community MCP that works on older Blender too | Low |
| 3 | **Built-in toon setup**: EEVEE Shader-to-RGB + ColorRamp, Solidify-flip-normals inverted-hull outline, Line Art for renders | Blender (GPL tool, output yours) | ✅ | The inverted-hull outline **exports to glTF** as a second, back-face material mesh, so it works at runtime too. Line Art and Freestyle are render-only (sprites) | Low |
| 4 | [LSCherry](https://github.com/lvoxx/LSCherry) | GPL-3.0, pushed 2026-09 | ✅ | Toon shader presets for Blender 4.x/5.x (for renders/sprites) | Low |
| 5 | [Malt](https://github.com/bnpr/Malt) | MIT, pushed 2026-03 | ✅ | Full NPR render engine. Overkill unless we go sprites | Medium |
| – | [glTF-Blender-IO](https://github.com/KhronosGroup/glTF-Blender-IO) | Apache-2.0 (built in) | ✅ | Exports skins, shape keys, multiple actions, and `KHR_materials_variants` (gear/skins) | – |

Per-muscle shape keys: plain Blender shape keys, exported as glTF morph targets. Keep the count modest (about 8–16) for mobile.

---

## 4. Flutter runtime
| # | Package | License | Skinning | Morph targets | Gear/mesh swap | Flame? | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **[flutter_scene](https://pub.dev/packages/flutter_scene)** ([repo](https://github.com/bdero/flutter_scene)) | MIT. v0.24.3, pushed 2026-10-30 | ✅ | ✅ (`morphWeights`) | ✅ `KHR_materials_variants` with instant switching, plus runtime node add/remove | Separate `SceneView` widget. Stack it with Flame UI, or use it alone | **Pick.** Requires Flutter 3.47+ with Flutter GPU enabled (Info.plist / manifest flag). Custom `.fmat` GLSL gives toon shading, and the inverted-hull mesh works. It's pre-1.0, so minor versions can break |
| 2 | **[thermion](https://pub.dev/packages/thermion_flutter)** ([repo](https://github.com/nmfisher/thermion)) | Apache-2.0. v0.5.0, pushed 2026-10-30 | ✅ | ✅ | ✅ (add/remove entities, Filament materials) | Widget overlay | **Backup.** Filament-based and more mature renderer. Android arm64 only, and toon needs custom Filament materials |
| 3 | [flame_3d](https://pub.dev/packages/flame_3d) | MIT, 0.3.2 | ✅ (skinning shader) | ? | manual | Native Flame | Self-described "do not use for production". Android/iOS/macOS only |
| 4 | [three_js (Dart)](https://pub.dev/packages/three_js) | MIT, 0.3.0 (6 months old), ★91 | ✅ | ⚠️ "Morphtargets does not work on some [Android] devices" | ✅ | Widget | Too risky for shape keys on Android |
| 5 | [model_viewer_plus](https://pub.dev/packages/model_viewer_plus) | Apache-2.0, 1.10.0 (11 months old) | ✅ (plays animations) | ❌ no morph-weight control from Dart | Variants only via JS | WebView | Viewer only. Fine for a "showroom" screen, not for gameplay |
| – | **Pre-rendered sprites** (Blender to PNG sheets to Flame `SpriteAnimation`) | – | – | – | Bake each gear combo | ✅ native Flame | **Fallback.** Zero runtime risk and perfect toon look, but the asset count grows with gear × muscle × anim combinations |

---

## Recommended stack
1. **Rigging:** Blender **Rigify** on `zeek_v1.glb` (after retopo/cleanup), with explicit 2–3 bone chains per antenna (+ spring/jiggle baked in Blender). Seed it fast with **Mesh2Motion** or **UniRig**, and use **Mixamo-compatible bone names**. Fallback: AccuRIG/Mixamo for the body, then hand-add antenna bones.
2. **Workout animation source:**
   - Start with **Mixamo** (curls, squats, push-ups, idles, celebrations) plus the **Mesh2Motion CC0** and **Quaternius CC0** libraries.
   - Fill gaps (**bench press, deadlift, flex poses**) by capturing Fernando on video with **FreeMoCap** (free, AGPL tool, outputs are ours), or **Rokoko Vision** free tier for short clips.
   - Retarget with the **Rokoko Blender add-on** or **Expy Kit**, then clean up in Blender. Hand-key flex poses, since they're short and stylized.
   - Avoid SMPL-based models (GVHMR, WHAM, 4DHumans, MoMask…) for shipped clips.
3. **Flutter runtime:**
   - Use **flutter_scene**: one GLB with a skinned mesh, muscle shape keys as morph targets, gear as child meshes or `KHR_materials_variants`, and a toon `.fmat` plus an inverted-hull outline.
   - Hosted as a `SceneView` widget alongside Flame/Flutter UI.
   - **thermion** is the plan B. **Pre-rendered sprites** are the plan C if Flutter GPU causes device issues.
   - Use **Blender Lab MCP** (on Blender 5.2) or **mcp-for-blender** to script the repetitive Blender steps.

**Next steps:** run UniRig and Mesh2Motion on `zeek_v1.glb` side by side → pick a skeleton → Rigify → test-export one Mixamo curl + 2 shape keys + 1 gear variant into a flutter_scene spike on a real Android and iPhone.

---
_Link check (Oct 30, 2026 PT): every link returned HTTP 200, except three. mocap.cs.cmu.edu returned a 500 to curl, and Adobe helpx and projects.blender.org returned 403 to curl (bot blocking). I opened all three successfully with a page fetcher._
