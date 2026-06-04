from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

SPARKLE = 0
ARCHER = 1
RIN = 2
CHAR_NAMES = ["花火", "Archer", "远坂凛"]

SparklePolicy = Literal[
    "alternate",
    "always_archer",
    "always_rin",
    "min_progress",
    "max_remaining_av",
    "avoid_waste",
]


@dataclass
class SimParams:
    """Simulation parameters."""

    tmax: float = 500.0
    gauge_max: float = 10000.0
    tol: float = 1e-9

    char_names: list[str] = field(default_factory=lambda: CHAR_NAMES.copy())

    # Initial integer speed values.
    speed0: tuple[int, int, int] = (160, 120, 100)

    # Sparkle initial advance from Vonwacq.
    sparkle_initial_advance: float = 0.40

    # Sparkle advance effect.
    sparkle_advance: float = 0.50

    # Rin speed bonus after her first action.
    rin_speed_bonus: int = 20

    # Same-AV action priority. Default: Sparkle > Archer > Rin.
    priority: tuple[int, int, int] = (SPARKLE, ARCHER, RIN)

    # Sparkle targeting policy.
    sparkle_policy: SparklePolicy = "alternate"


def choose_sparkle_target(
    progress: np.ndarray,
    speed: np.ndarray,
    sparkle_turn_count: int,
    params: SimParams,
) -> int:
    """Choose Sparkle's advance target."""

    policy = params.sparkle_policy

    if policy == "alternate":
        return ARCHER if sparkle_turn_count % 2 == 1 else RIN

    if policy == "always_archer":
        return ARCHER

    if policy == "always_rin":
        return RIN

    if policy == "min_progress":
        return ARCHER if progress[ARCHER] <= progress[RIN] else RIN

    if policy == "max_remaining_av":
        remain_archer = (params.gauge_max - progress[ARCHER]) / speed[ARCHER]
        remain_rin = (params.gauge_max - progress[RIN]) / speed[RIN]
        return ARCHER if remain_archer >= remain_rin else RIN

    if policy == "avoid_waste":
        add_progress = params.gauge_max * params.sparkle_advance
        waste_archer = max(0.0, progress[ARCHER] + add_progress - params.gauge_max)
        waste_rin = max(0.0, progress[RIN] + add_progress - params.gauge_max)

        if waste_archer < waste_rin:
            return ARCHER
        if waste_rin < waste_archer:
            return RIN

        remain_archer = (params.gauge_max - progress[ARCHER]) / speed[ARCHER]
        remain_rin = (params.gauge_max - progress[RIN]) / speed[RIN]
        return ARCHER if remain_archer >= remain_rin else RIN

    raise ValueError(f"Unsupported sparkle_policy: {policy}")


def check_alternation(action_df: pd.DataFrame, advance_df: pd.DataFrame) -> dict:
    """Check actual Archer/Rin action alternation and Sparkle target alternation."""

    non_sparkle = action_df[action_df["Character"] != "花火"].copy()
    seq = non_sparkle["Character"].tolist()
    times = non_sparkle["ActionValue"].tolist()

    actual_alt_ok = True
    bad_actual_alt_pos: list[int] = []

    for k in range(1, len(seq)):
        if seq[k] == seq[k - 1]:
            actual_alt_ok = False
            bad_actual_alt_pos.append(k)

    targets = advance_df["Target"].tolist() if not advance_df.empty else []

    target_alt_ok = True
    bad_target_alt_pos: list[int] = []

    for k in range(1, len(targets)):
        if targets[k] == targets[k - 1]:
            target_alt_ok = False
            bad_target_alt_pos.append(k)

    return {
        "ActualAltOK": actual_alt_ok,
        "BadActualAltPos": bad_actual_alt_pos,
        "TargetAltOK": target_alt_ok,
        "BadTargetAltPos": bad_target_alt_pos,
        "NonSparkleSeq": seq,
        "NonSparkleTime": times,
    }


def simulate_action(
    speed0: tuple[int, int, int] | list[int] | np.ndarray | None = None,
    params: SimParams | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    """Event-driven action-axis simulation."""

    if params is None:
        params = SimParams()

    if speed0 is None:
        speed0 = params.speed0

    speed = np.asarray(speed0, dtype=float).reshape(-1)
    if speed.size != 3:
        raise ValueError("speed0 must contain three values: [Sparkle, Archer, Rin].")

    speed = np.round(speed).astype(float)
    if np.any(speed <= 0):
        raise ValueError("All speeds must be positive integers.")

    t = 0.0
    progress = np.zeros(3, dtype=float)
    progress[SPARKLE] = params.gauge_max * params.sparkle_initial_advance

    action_count = np.zeros(3, dtype=int)
    sparkle_turn_count = 0
    rin_first_action_done = False

    action_rows = []
    advance_rows = []

    max_event_num = 100000
    event_num = 0

    while True:
        while np.any(progress >= params.gauge_max - params.tol):
            event_num += 1
            if event_num > max_event_num:
                raise RuntimeError("Too many events. Please check rules for a possible infinite loop.")

            actor = None
            for idx in params.priority:
                if progress[idx] >= params.gauge_max - params.tol:
                    actor = idx
                    break

            if actor is None:
                raise RuntimeError("Internal error: no actor selected.")

            action_count[actor] += 1

            action_rows.append(
                {
                    "ActionValue": t,
                    "Character": params.char_names[actor],
                    "CharacterIdx": actor,
                    "ActionCount": int(action_count[actor]),
                    "SpeedAtAction": int(round(speed[actor])),
                    "ProgressAtActionPercent": progress[actor] / params.gauge_max * 100.0,
                }
            )

            progress[actor] = 0.0

            if actor == RIN and not rin_first_action_done:
                rin_first_action_done = True
                speed[RIN] += params.rin_speed_bonus

            if actor == SPARKLE:
                sparkle_turn_count += 1
                target = choose_sparkle_target(progress, speed, sparkle_turn_count, params)

                before_progress = progress[target]
                add_progress = params.gauge_max * params.sparkle_advance

                waste_progress = max(0.0, before_progress + add_progress - params.gauge_max)
                effective_progress = add_progress - waste_progress
                progress[target] = min(params.gauge_max, before_progress + add_progress)

                advance_rows.append(
                    {
                        "ActionValue": t,
                        "SparkleActionNo": sparkle_turn_count,
                        "Target": params.char_names[target],
                        "TargetIdx": target,
                        "TargetProgressBeforePercent": before_progress / params.gauge_max * 100.0,
                        "AdvancePercent": params.sparkle_advance * 100.0,
                        "EffectiveAdvancePercent": effective_progress / params.gauge_max * 100.0,
                        "WastePercent": waste_progress / params.gauge_max * 100.0,
                        "IsWasted": waste_progress > params.tol,
                    }
                )

        remain_av = (params.gauge_max - progress) / speed
        dt = float(np.min(remain_av))
        next_t = t + dt

        if next_t > params.tmax + params.tol:
            break

        if abs(next_t - params.tmax) < 1e-8:
            next_t = params.tmax
            dt = next_t - t

        progress = progress + speed * dt
        t = next_t

        close_to_full = np.abs(progress - params.gauge_max) < 1e-7
        progress[close_to_full] = params.gauge_max

    action_df = pd.DataFrame(action_rows)
    advance_df = pd.DataFrame(advance_rows)

    if action_df.empty:
        action_df = pd.DataFrame(
            columns=["ActionValue", "Character", "CharacterIdx", "ActionCount", "SpeedAtAction", "ProgressAtActionPercent"]
        )

    if advance_df.empty:
        advance_df = pd.DataFrame(
            columns=[
                "ActionValue", "SparkleActionNo", "Target", "TargetIdx",
                "TargetProgressBeforePercent", "AdvancePercent",
                "EffectiveAdvancePercent", "WastePercent", "IsWasted",
            ]
        )

    flags = check_alternation(action_df, advance_df)

    final_state = {
        "t": t,
        "progress": progress.copy(),
        "speed": speed.copy(),
        "action_count": action_count.copy(),
        "sparkle_turn_count": sparkle_turn_count,
        "rin_first_action_done": rin_first_action_done,
    }

    return action_df, advance_df, flags, final_state


def export_to_excel(
    filename: str,
    action_df: pd.DataFrame,
    advance_df: pd.DataFrame,
    summary_df: pd.DataFrame | None = None,
) -> None:
    """Export action log, advance log and optional summary to Excel."""

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        action_df.to_excel(writer, sheet_name="ActionLog", index=False)
        advance_df.to_excel(writer, sheet_name="AdvanceLog", index=False)
        if summary_df is not None:
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
