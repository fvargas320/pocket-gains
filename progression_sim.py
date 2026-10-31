#!/usr/bin/env python3
"""Pocket Gains progression simulator (see progression.md).

Simulates 12 months for several user types and plots per-muscle visual size
(the 0–1 shape-key value before pump) to research/progression_sim.png.
Run: python progression_sim.py   (needs numpy + matplotlib)
"""
import math, random
from collections import defaultdict
from pathlib import Path

# ----------------------------- tuning knobs ---------------------------------
K_SIZE          = 2600    # XP "time constant" of the size curve
SIZE_NORM       = 0.985   # size = (1-e^-xp/K)/SIZE_NORM, clamped to 1 -> max at ~10.9k XP
SESSION_XP_MAX  = 160     # per muscle per day (asymptote)
SESSION_SETS_K  = 5.0     # effective sets that give 63% of SESSION_XP_MAX
HELPER_SHARE    = 0.5     # helper muscles get 50% of a set's stimulus
WEEKLY_SOFT     = 200     # per muscle, per calendar week (resets Monday): raw XP up to this is credited 100% (~2 solid sessions)
WEEKLY_EXCESS   = 0.10    # raw XP above WEEKLY_SOFT is credited at 10% ...
RECOVERY_MULT   = [(20, 0.4), (44, 0.7)]  # hours since that muscle was last trained -> multiplier
WEEKLY_CAP      = 230     # ... up to a hard cap of credited XP per muscle per calendar week
PR_BONUS_FRAC   = 0.25    # PR bonus = 25% of that muscle's session XP ...
PR_BONUS_CAP    = 40      # ... capped at 40 XP, max one PR bonus per muscle per session
DECAY_GRACE     = 7       # days untrained before the size track decays
DECAY_RATE      = 0.01    # per day, of current size-XP
DECAY_FLOOR     = 0.70    # of peak size-XP
MEMORY_MULT     = 2.0     # size-track XP multiplier while regrowing below peak
PUMP_MAX        = 0.12    # temporary shape-key boost right after a session (fades over 3 h)
ACCT_A          = 95      # account XP for level L = ACCT_A * (L-1)^1.5  -> Lv100 at ~94k XP
# --- strength factor (section 9 of progression.md) ---
HEAVY_LOAD_LO   = 0.70    # load (fraction of e1RM) where the heavy-set credit starts
HEAVY_LOAD_HI   = 0.85    # ... and where it reaches its full value
HEAVY_CREDIT    = 1.10    # rep-factor for a set at >= 85% e1RM (a hard 8 has rep-factor 1.0)
SET_STIM_MAX    = 1.25    # cap per set
STR_ACCT_BONUS  = 0.50    # account/rank XP multiplier = 1 + 0.50 * S^1.5   (S = strength index 0..1)
STR_MUSCLE_BONUS= 0.20    # muscle (size) XP multiplier = 1 + 0.20 * S^1.5
STR_MIN_LIFTS   = 3       # need e1RMs on >= 3 of the 5 big lifts (no bench-only bonus)
STR_BW_MAX_AGE  = 60      # bodyweight must be logged within 60 days or the bonus is off
STR_JUMP_FLAG   = 0.12    # new e1RM > 12% above the 90-day best (within 14 days) -> "needs verify"
# -----------------------------------------------------------------------------

MUSCLES = ["chest", "shoulders", "arms_biceps", "arms_triceps", "back_lats",
           "abs_core", "legs_quads", "legs_glutes", "legs_calves"]
UPPER = ["chest", "shoulders", "arms_biceps", "arms_triceps", "back_lats"]
LOWER = ["legs_quads", "legs_glutes", "legs_calves"]

EX = {  # exercise: (primary, [helpers])
    "bench": ("chest", ["arms_triceps", "shoulders"]),
    "incline_db": ("chest", ["shoulders"]),
    "fly": ("chest", []),
    "ohp": ("shoulders", ["arms_triceps"]),
    "lateral": ("shoulders", []),
    "row": ("back_lats", ["arms_biceps"]),
    "pulldown": ("back_lats", ["arms_biceps"]),
    "curl": ("arms_biceps", []),
    "pushdown": ("arms_triceps", []),
    "squat": ("legs_quads", ["legs_glutes", "abs_core"]),
    "leg_press": ("legs_quads", ["legs_glutes"]),
    "rdl": ("legs_glutes", ["back_lats"]),
    "calf": ("legs_calves", []),
    "crunch": ("abs_core", []),
    "deadlift": ("legs_glutes", ["back_lats", "legs_quads"]),
}

# Strength standards: e1RM / bodyweight at the 5 tier boundaries
#                beginner novice intermediate advanced elite   (tier position 0..4)
STR_TIERS = {
    "squat":    (0.75, 1.25, 1.50, 2.25, 3.00),
    "bench":    (0.50, 0.75, 1.00, 1.50, 2.00),
    "deadlift": (1.00, 1.50, 2.00, 2.50, 3.00),
    "ohp":      (0.35, 0.55, 0.75, 1.00, 1.35),
    "row":      (0.50, 0.75, 1.00, 1.50, 1.75),
}
TIER_NAMES = ["Beginner", "Novice", "Intermediate", "Advanced", "Elite"]


def set_stimulus(reps, effort=1.0, load=0.75):
    """One working set -> stimulus (a hard 8 at effort 1.0 = 1.0).
    effort: 1.0 = 0-1 RIR, 0.95 = 1-2 RIR, 0.9 = 2-3 RIR, 0.8 = 4+ RIR.
    load: fraction of the lift's current e1RM. Heavy sets get a rep-factor floor so a
    near-max triple is worth at least as much as a hard 8."""
    rep_f = min(reps, 15) / 8
    heavy = HEAVY_CREDIT * min(1.0, max(0.0, (load - HEAVY_LOAD_LO) / (HEAVY_LOAD_HI - HEAVY_LOAD_LO)))
    return min(SET_STIM_MAX, effort ** 2 * max(rep_f, heavy))


def tier_position(lift, ratio):
    """Continuous 0..4 position on the tier ladder (0 = beginner line or below, 4 = elite)."""
    t = STR_TIERS[lift]
    if ratio <= t[0]:
        return 0.0
    for i in range(4):
        if ratio < t[i + 1]:
            return i + (ratio - t[i]) / (t[i + 1] - t[i])
    return 4.0


def strength_index(ratios, bw_age_days=0):
    """ratios: {lift: e1RM/bodyweight} for confirmed lifts. Returns S in 0..1 (0 = no bonus)."""
    if bw_age_days is None or bw_age_days > STR_BW_MAX_AGE:
        return 0.0
    pos = [tier_position(l, r) for l, r in ratios.items() if l in STR_TIERS]
    if len(pos) < STR_MIN_LIFTS:
        return 0.0
    pos += [0.0] * (5 - len(pos))           # missing lifts count as beginner
    return sum(pos) / (4 * len(pos))


def strength_mults(S):
    return 1 + STR_ACCT_BONUS * S ** 1.5, 1 + STR_MUSCLE_BONUS * S ** 1.5


def e1rm_flag(best_90d, new_e1rm, days_since_best):
    """Anti-cheese: True = hold the e1RM as unconfirmed until verified (repeat within 7 days or video)."""
    return best_90d > 0 and days_since_best <= 14 and new_e1rm > best_90d * (1 + STR_JUMP_FLAG)

UA = [("bench", 4), ("row", 4), ("ohp", 3), ("curl", 3), ("pushdown", 3)]
UB = [("incline_db", 4), ("pulldown", 4), ("lateral", 3), ("curl", 3), ("pushdown", 3)]
LA = [("squat", 4), ("rdl", 3), ("leg_press", 3), ("calf", 4), ("crunch", 3)]
LB = [("leg_press", 4), ("rdl", 3), ("squat", 3), ("calf", 4), ("crunch", 3)]
FB_A = [("bench", 3), ("row", 3), ("squat", 3), ("ohp", 2), ("curl", 2), ("calf", 2), ("crunch", 2)]
FB_B = [("incline_db", 3), ("pulldown", 3), ("rdl", 3), ("leg_press", 2), ("pushdown", 2), ("calf", 2)]
BRO = [("bench", 5), ("incline_db", 4), ("fly", 4), ("curl", 4), ("pushdown", 3), ("lateral", 3)]
# Powerlifter: (exercise, sets, reps, load as fraction of e1RM, effort). Mostly heavy low-rep compounds.
# ~75% of sets are heavy (<=5 reps, >=80% e1RM) competition-lift work; the rest is typical PL accessory work.
PL_SQ = [("squat", 5, 3, 0.88, 0.95), ("bench", 4, 5, 0.82, 0.95), ("row", 4, 5, 0.80, 0.9),
         ("rdl", 3, 6, 0.75, 0.9), ("crunch", 2, 12, 0.6, 0.9)]
PL_DL = [("deadlift", 4, 3, 0.88, 0.95), ("ohp", 4, 5, 0.82, 0.95), ("pulldown", 3, 6, 0.80, 0.9),
         ("curl", 2, 10, 0.7, 0.9)]
PL_BN = [("bench", 6, 3, 0.88, 0.95), ("row", 4, 5, 0.80, 0.9), ("incline_db", 3, 8, 0.75, 0.9),
         ("pushdown", 2, 8, 0.75, 0.9)]
PL_VOL = [("squat", 4, 5, 0.80, 0.9), ("deadlift", 2, 2, 0.92, 0.95), ("ohp", 3, 5, 0.80, 0.9),
          ("leg_press", 2, 8, 0.75, 0.9), ("calf", 3, 10, 0.7, 0.9)]
PL = {0: PL_SQ, 1: PL_DL, 3: PL_BN, 5: PL_VOL}

USERS = {  # weekday -> template ; (0=Mon)
    "Casual (2x/wk full body)": {1: FB_A, 4: FB_B},
    "Regular (4x/wk upper/lower)": {0: UA, 1: LA, 3: UB, 4: LB},
    "Chest-only bro (5x/wk)": {d: BRO for d in range(5)},
    "Regular + 4-wk break (month 5)": {0: UA, 1: LA, 3: UB, 4: LB},
    "Powerlifter (4x/wk heavy compounds)": PL,
    "Powerlifter, no bodyweight logged": PL,
}
SKIP_P = 0.08

# Strength profile per user: e1RM/bodyweight at day 0 and the ratio it approaches with practice
# (ratio = r0 + (rmax - r0) * (1 - e^(-sessions_of_that_lift / 40))). Lifts not listed are never tested.
REG_STR = ({"squat": 0.9, "bench": 0.65, "ohp": 0.45, "row": 0.6, "deadlift": 1.1},
           {"squat": 1.45, "bench": 1.0, "ohp": 0.7, "row": 0.95, "deadlift": 1.7})
STRENGTH = {
    "Casual (2x/wk full body)": ({"squat": 0.8, "bench": 0.6, "ohp": 0.4, "row": 0.55},
                                 {"squat": 1.3, "bench": 0.9, "ohp": 0.6, "row": 0.85}, 0),
    "Regular (4x/wk upper/lower)": (*REG_STR, 0),
    "Chest-only bro (5x/wk)": ({"bench": 0.8}, {"bench": 1.4}, 0),      # only 1 big lift -> no bonus
    "Regular + 4-wk break (month 5)": (*REG_STR, 0),
    "Powerlifter (4x/wk heavy compounds)": ({"squat": 1.6, "bench": 1.05, "deadlift": 2.0, "ohp": 0.7, "row": 0.95},
                                            {"squat": 2.5, "bench": 1.6, "deadlift": 2.8, "ohp": 1.0, "row": 1.4}, 0),
    "Powerlifter, no bodyweight logged": ({"squat": 1.6, "bench": 1.05, "deadlift": 2.0, "ohp": 0.7, "row": 0.95},
                                          {"squat": 2.5, "bench": 1.6, "deadlift": 2.8, "ohp": 1.0, "row": 1.4}, None),
}
STR_TAU = 40   # sessions of a lift for ~63% of the way to its 12-month ceiling


def weekly_credit(raw):
    """Credited XP for a given raw XP total in one calendar week."""
    return min(raw, WEEKLY_SOFT) + WEEKLY_EXCESS * max(0.0, raw - WEEKLY_SOFT)


def size_of(xp):
    return min(1.0, (1 - math.exp(-xp / K_SIZE)) / SIZE_NORM)


def level_of(xp):
    return 1 + int(49 * size_of(xp) + 1e-9)


def acct_level(xp):
    return min(100, 1 + int((xp / ACCT_A) ** (1 / 1.5)))


def session_xp(n_eff):
    return SESSION_XP_MAX * (1 - math.exp(-n_eff / SESSION_SETS_K))


def simulate(name, sched, days=365, seed=7):
    rng = random.Random(seed)
    life = defaultdict(float); sz = defaultdict(float); peak = defaultdict(float)
    last = {}; hist = defaultdict(list)  # muscle -> [(day, xp)]
    acct = 0.0; sessions = 0; sess_series = []; series = {m: [] for m in MUSCLES}; acct_series = []
    first5 = None
    r0, rmax, bw_age = STRENGTH.get(name, ({}, {}, None))
    lift_sessions = defaultdict(int); S = 0.0; s_series = []
    for day in range(days):
        wd = day % 7
        brk = name.startswith("Regular +") and 150 <= day < 178
        tmpl = sched.get(wd) if not brk else None
        if tmpl and rng.random() > SKIP_P:
            sessions += 1
            n = defaultdict(float)
            pr_muscles = set()
            pr_p = 0.45 * math.exp(-day / 60) + 0.04   # PR chance per exercise falls over time
            for item in tmpl:
                ex, sets = item[0], item[1]
                reps, load, effort = (item[2], item[3], item[4]) if len(item) > 2 else (8, 0.75, 1.0)
                prim, helpers = EX[ex]
                stim = sets * set_stimulus(reps, effort, load)   # hard 8 = 1.0 per set
                if ex in r0:
                    lift_sessions[ex] += 1
                n[prim] += stim
                for h in helpers:
                    n[h] += stim * HELPER_SHARE
                if rng.random() < pr_p:
                    pr_muscles.add(prim)
            ratios = {l: r0[l] + (rmax[l] - r0[l]) * (1 - math.exp(-lift_sessions[l] / STR_TAU))
                      for l in r0 if lift_sessions[l] > 0}
            S = strength_index(ratios, bw_age)
            acct_mult, muscle_mult = strength_mults(S)
            for m, ne in n.items():
                if ne < 0.5:
                    continue
                rm = 1.0
                if m in last:
                    hrs = (day - last[m]) * 24
                    for lim, mult in RECOVERY_MULT:
                        if hrs < lim:
                            rm = mult; break
                raw = session_xp(ne) * rm
                if m in pr_muscles:
                    raw += min(PR_BONUS_CAP, PR_BONUS_FRAC * raw)
                raw_week = sum(r for d, r, _ in hist[m] if d // 7 == day // 7)
                cred_week = sum(c for d, _, c in hist[m] if d // 7 == day // 7)
                xp = weekly_credit(raw_week + raw) - weekly_credit(raw_week)
                xp = max(0.0, min(xp, WEEKLY_CAP - cred_week))
                hist[m].append((day, raw, xp)); last[m] = day
                acct += xp * acct_mult          # strength bonus applies after the weekly cap
                xp *= muscle_mult
                life[m] += xp
                gain = xp * (MEMORY_MULT if sz[m] < peak[m] else 1.0)
                sz[m] = min(peak[m], sz[m] + gain) if sz[m] < peak[m] else sz[m] + gain
                if sz[m] + 1e-9 >= peak[m]:
                    sz[m] = max(sz[m], peak[m]); peak[m] = sz[m]
            if sessions == 5:
                first5 = max(size_of(sz[m]) for m in MUSCLES)
        # decay
        for m in MUSCLES:
            if m in last and day - last[m] > DECAY_GRACE:
                sz[m] = max(DECAY_FLOOR * peak[m], sz[m] * (1 - DECAY_RATE))
        for m in MUSCLES:
            series[m].append(size_of(sz[m]))
        acct_series.append(acct_level(acct)); sess_series.append(sessions); s_series.append(S)
    return dict(series=series, acct=acct_series, sess=sess_series, life=life, sessions=sessions, first5=first5,
                S=s_series, acct_xp=acct)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = Path(__file__).parent / "research" / "progression_sim.png"
    out.parent.mkdir(exist_ok=True)
    results = {n: simulate(n, s) for n, s in USERS.items()}
    colors = {"chest": "#F2A33A", "shoulders": "#C8643B", "arms_biceps": "#E8D36A", "arms_triceps": "#B9A24A",
              "back_lats": "#2FA59A", "abs_core": "#9FD8C0", "legs_quads": "#5EF2E6",
              "legs_glutes": "#3C8DD8", "legs_calves": "#7A6CF0"}
    fig, axes = plt.subplots(2, 3, figsize=(21, 10.5), sharex=True, sharey=True)
    for ax, (name, r) in zip(axes.flat, results.items()):
        t = [d / 30.4 for d in range(365)]
        for m in MUSCLES:
            ax.plot(t, r["series"][m], color=colors[m], lw=2.2 if m in ("chest", "legs_quads") else 1.3,
                    label=m)
        for y, lab in [(0.3, "30%"), (0.6, "60%"), (0.9, "90%")]:
            ax.axhline(y, color="#888", lw=0.6, ls=":")
        for mo in (1, 3, 6, 9, 12):
            ax.axvline(mo, color="#ccc", lw=0.5)
        ax2 = ax.twinx(); ax2.plot(t, r["acct"], color="k", lw=1, ls="--", label="account level")
        ax2.plot(t, [100 * v for v in r["S"]], color="#C0392B", lw=1, ls="-.", label="strength index x100")
        ax2.set_ylim(0, 105)
        ax2.set_ylabel("account Lv (dashed) / strength idx x100 (red)", fontsize=8)
        ax.set_title(f"{name} — {r['sessions']} sessions", fontsize=11)
        ax.set_ylim(0, 1.02); ax.grid(alpha=0.2)
    for a in axes[1]:
        a.set_xlabel("months")
    axes[0][0].set_ylabel("visual size (shape key, no pump)"); axes[1][0].set_ylabel("visual size (shape key, no pump)")
    axes[0][0].legend(fontsize=7, ncol=3, loc="lower right")
    fig.suptitle("Pocket Gains progression sim (12 months)", fontsize=14)
    fig.tight_layout(); fig.savefig(out, dpi=110)
    print(f"chart -> {out}\n")

    def at(r, m, month):
        return r["series"][m][min(364, int(month * 30.4))]
    for name, r in results.items():
        print(f"== {name}: {r['sessions']} sessions, max muscle size after 5 sessions = {r['first5']:.3f}, "
              f"account XP {r['acct_xp']:.0f}")
        for mo in (1, 3, 6, 9, 12):
            up = sum(at(r, m, mo) for m in UPPER) / len(UPPER)
            lo = sum(at(r, m, mo) for m in LOWER) / len(LOWER)
            print(f"  m{mo:>2}: chest {at(r,'chest',mo):.2f}  quads {at(r,'legs_quads',mo):.2f}  "
                  f"upperAvg {up:.2f}  lowerAvg {lo:.2f}  acctLv {r['acct'][min(364,int(mo*30.4))]}  "
                  f"S {r['S'][min(364,int(mo*30.4))]:.2f} (acct x{strength_mults(r['S'][min(364,int(mo*30.4))])[0]:.2f})")
    print("\nMilestones (avg size of all 9 muscles; first day reached -> sessions logged, month)")
    for name, r in results.items():
        avg = [sum(r["series"][m][d] for m in MUSCLES) / len(MUSCLES) for d in range(365)]
        row = []
        for th in (0.10, 0.30, 0.60, 0.90, 0.99):
            d = next((i for i, v in enumerate(avg) if v >= th), None)
            row.append(f"{int(th*100)}%: " + (f"{r['sess'][d]} sess/{d/30.4:.1f}mo" if d is not None else "never"))
        print(f"  {name}: " + " | ".join(row))
        ranks = []
        for lv, rk in ((5, "Bronze"), (20, "Silver"), (40, "Gold"), (65, "Platinum"), (90, "Legend")):
            d = next((i for i, v in enumerate(r["acct"]) if v >= lv), None)
            ranks.append(f"{rk} " + (f"{d/30.4:.1f}mo" if d is not None else "-"))
        print("     ranks: " + ", ".join(ranks))
    # checks
    assert all(r["first5"] < 0.25 for r in results.values()), "someone near max after 5 sessions"
    bro = results["Chest-only bro (5x/wk)"]
    assert max(bro["series"][m][-1] for m in LOWER) < 0.1, "bro legs grew"
    pl = results["Powerlifter (4x/wk heavy compounds)"]; plnb = results["Powerlifter, no bodyweight logged"]
    reg = results["Regular (4x/wk upper/lower)"]
    def day_lv(r, lv):
        return next((i for i, v in enumerate(r["acct"]) if v >= lv), 10**9)
    assert bro["S"][-1] == 0.0, "bench-only bro got a strength bonus"
    assert max(plnb["S"]) == 0.0, "bonus without bodyweight"
    assert day_lv(pl, 40) < day_lv(plnb, 40), "strength bonus did not speed up ranking"
    assert pl["acct_xp"] <= 1.5 * plnb["acct_xp"] + 1, "strength bonus above 1.5x"
    assert day_lv(pl, 40) < day_lv(reg, 40) and day_lv(pl, 90) < day_lv(reg, 90), "powerlifter not faster than regular"
    hard8 = set_stimulus(8, 0.95, 0.75); triple = set_stimulus(3, 0.95, 0.90)
    assert triple >= hard8, "heavy triple worth less than a hard 8"
    assert e1rm_flag(100, 115, 7) and not e1rm_flag(100, 108, 7)
    print("\nCHECKS PASSED: nobody >25% after 5 sessions; chest-only bro legs stay <10%; bench-only bro and "
          "no-bodyweight users get no strength bonus; bonus <= 1.5x; powerlifter reaches Gold and Legend before regular; "
          "heavy triple >= hard 8; +15% e1RM jump flagged.")
    print("\nSet stimulus (hard 8 @0-1 RIR = 1.00):")
    for lab, a in [("8 reps, 1-2 RIR, 75%", (8, 0.95, 0.75)), ("3 reps, 1-2 RIR, 90%", (3, 0.95, 0.90)),
                   ("1 rep, 0 RIR, 100%", (1, 1.0, 1.0)), ("5 reps, 1-2 RIR, 85%", (5, 0.95, 0.85)),
                   ("5x5 @80%, 2-3 RIR", (5, 0.90, 0.80)), ("12 reps, 0 RIR", (12, 1.0, 0.65)),
                   ("3 reps @60% (easy)", (3, 0.8, 0.60))]:
        print(f"  {lab:24s} -> {set_stimulus(*a):.2f}")
    print("\nStrength multipliers by tier (all 5 lifts at that tier):")
    for i, tn in enumerate(TIER_NAMES):
        S = i / 4; a, m = strength_mults(S); print(f"  {tn:12s} S={S:.2f}  account x{a:.2f}  muscle x{m:.2f}")
    print("\nRank timing, powerlifter with vs without bodyweight vs regular:")
    for lv, rk in ((20, "Silver"), (40, "Gold"), (65, "Platinum"), (90, "Legend")):
        f = lambda r: f"{day_lv(r, lv)/30.4:.1f}mo" if day_lv(r, lv) < 10**8 else "-"
        print(f"  {rk:9s} PL {f(pl):>7s} | PL no-BW {f(plnb):>7s} | regular {f(reg):>7s}")
    print(f"  12-mo account XP: PL {pl['acct_xp']:.0f}, PL no-BW {plnb['acct_xp']:.0f} "
          f"(x{pl['acct_xp']/plnb['acct_xp']:.2f}), regular {reg['acct_xp']:.0f}")
    # single-session / PR numbers for the doc
    x = session_xp(4); print(f"\nOne 4-set chest session from zero: +{x:.0f} XP -> size {size_of(x):.3f}, level {level_of(x)}")
    pr = min(PR_BONUS_CAP, PR_BONUS_FRAC * x); print(f"  PR bonus +{pr:.0f} XP -> size {size_of(x+pr):.3f}")
    for base in (2400, 6000):
        print(f"  same session at {size_of(base):.2f} size: +{size_of(base+x)-size_of(base):.4f}; with PR +{size_of(base+x+pr)-size_of(base):.4f}")
    # farmer: 40 sets of curls every day for 5 days
    raw_tot = 0.0; cred = 0.0
    for d in range(5):
        raw = session_xp(40) * (1.0 if d == 0 else RECOVERY_MULT[1][1])
        x = weekly_credit(raw_tot + raw) - weekly_credit(raw_tot)
        x = min(x, WEEKLY_CAP - cred); raw_tot += raw; cred += x
    print(f"Farmer (40 curl sets/day x5 days): biceps XP {cred:.0f} -> size {size_of(cred):.3f}")


if __name__ == "__main__":
    main()
