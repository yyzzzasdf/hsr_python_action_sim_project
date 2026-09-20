"""Manual Sparkle advance strip aligned below the merged action-axis chart."""

from __future__ import annotations

import streamlit as st

from hsr_core import (
    ARCHER,
    L,
    SPARKLE,
    SPARKLE_POLICY_OPTIONS,
    SimParams,
    SparklePolicy,
    simulate_action,
)
from hsr_plotting import (
    MERGED_AXIS_LAYOUT_WIDTH,
    MERGED_AXIS_MARGIN_L,
    MERGED_AXIS_MARGIN_R,
)

PULL_LABELS = ["A", "L"]
LABEL_TO_IDX = {"A": ARCHER, "L": L}
TURN_COL_WEIGHT = 22.0
_CHART_AXIS_SPAN = MERGED_AXIS_LAYOUT_WIDTH - MERGED_AXIS_MARGIN_L - MERGED_AXIS_MARGIN_R

_STRIP_COMPACT_CSS = """
<style>
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stRadio"] input[value="A"]) label {
    padding: 0.1rem 0.25rem !important;
    min-height: 0 !important;
    font-size: 0.78rem !important;
}
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stRadio"] input[value="A"]) div[role="radiogroup"] {
    gap: 0.15rem !important;
}
</style>
"""


def _column_weights_for_turns(
    turns: list[tuple[int, float, object]],
    tmax: float,
) -> list[float]:
    """Column weights so each A/L block center matches Plotly x = margin_l + (x/tmax)*plot_span."""
    if not turns:
        return [MERGED_AXIS_MARGIN_L, MERGED_AXIS_MARGIN_R]

    weights: list[float] = [float(MERGED_AXIS_MARGIN_L)]
    for i, (_, x_plot, _) in enumerate(turns):
        if i == 0:
            gap = (x_plot / tmax) * _CHART_AXIS_SPAN - TURN_COL_WEIGHT / 2
        else:
            prev_x = turns[i - 1][1]
            gap = ((x_plot - prev_x) / tmax) * _CHART_AXIS_SPAN - TURN_COL_WEIGHT
        weights.append(max(gap, 0.3))
        weights.append(TURN_COL_WEIGHT)

    last_x = turns[-1][1]
    trail = _CHART_AXIS_SPAN - (last_x / tmax) * _CHART_AXIS_SPAN - TURN_COL_WEIGHT / 2
    weights.append(max(trail, 0.3))
    weights.append(float(MERGED_AXIS_MARGIN_R))
    return weights


def init_manual_state() -> None:
    if "sparkle_manual_overrides" not in st.session_state:
        st.session_state.sparkle_manual_overrides = {}
    if "sparkle_policy_base" not in st.session_state:
        st.session_state.sparkle_policy_base = "alternate"
    if "_last_sidebar_policy" not in st.session_state:
        st.session_state._last_sidebar_policy = None


def on_sidebar_policy_change(selected: str) -> None:
    last = st.session_state._last_sidebar_policy
    if last is not None and selected != last:
        _clear_pull_widget_keys()
        if selected != "manual":
            st.session_state.sparkle_manual_overrides = {}
            st.session_state.sparkle_policy_base = selected
        elif not st.session_state.sparkle_manual_overrides:
            st.session_state.sparkle_policy_base = last if last != "manual" else "alternate"
    st.session_state._last_sidebar_policy = selected


def sync_strip_widgets_if_context_changed(signature: str, policy: str) -> None:
    """Reset A/L radios when policy or sim inputs change so they match auto targets."""
    prev_sig = st.session_state.get("_strip_sync_signature")
    prev_policy = st.session_state.get("_strip_sync_policy")

    if prev_policy is not None and prev_policy != policy:
        _clear_pull_widget_keys()
        st.session_state.sparkle_manual_overrides = {}
    elif prev_sig is not None and prev_sig != signature:
        _clear_pull_widget_keys()

    st.session_state["_strip_sync_signature"] = signature
    st.session_state["_strip_sync_policy"] = policy


def policy_selectbox_index() -> int:
    if st.session_state.sparkle_manual_overrides:
        return SPARKLE_POLICY_OPTIONS.index("manual")
    selected = st.session_state.get("sparkle_policy_select", "alternate")
    if selected in SPARKLE_POLICY_OPTIONS:
        return SPARKLE_POLICY_OPTIONS.index(selected)
    return SPARKLE_POLICY_OPTIONS.index("alternate")


def prune_stale_overrides(advance_df) -> None:
    if advance_df.empty:
        st.session_state.sparkle_manual_overrides = {}
        _clear_pull_widget_keys()
        return
    max_turn = int(advance_df["SparkleActionNo"].max())
    active_turns = set(range(1, max_turn + 1))
    st.session_state.sparkle_manual_overrides = {
        k: v
        for k, v in st.session_state.sparkle_manual_overrides.items()
        if k <= max_turn
    }
    for key in list(st.session_state.keys()):
        if key.startswith("sparkle_pull_"):
            suffix = key.removeprefix("sparkle_pull_")
            if suffix.isdigit() and int(suffix) not in active_turns:
                del st.session_state[key]


def _clear_pull_widget_keys() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("sparkle_pull_"):
            del st.session_state[key]


def effective_auto_policy(sidebar_policy: str) -> SparklePolicy:
    overrides = st.session_state.sparkle_manual_overrides
    if overrides:
        base: str = st.session_state.sparkle_policy_base
        return base if base != "manual" else "alternate"  # type: ignore[return-value]
    if sidebar_policy == "manual":
        return "alternate"
    return sidebar_policy  # type: ignore[return-value]


def build_sim_params(
    *,
    tmax: float,
    speed0: tuple[int, int, int],
    sparkle_initial_advance: float,
    sparkle_advance: float,
    l_speed_bonus: int,
    sidebar_policy: str,
) -> SimParams:
    overrides = dict(st.session_state.sparkle_manual_overrides)
    auto_policy = effective_auto_policy(sidebar_policy)
    return SimParams(
        tmax=tmax,
        speed0=speed0,
        sparkle_initial_advance=sparkle_initial_advance,
        sparkle_advance=sparkle_advance,
        l_speed_bonus=l_speed_bonus,
        sparkle_policy=auto_policy,
        sparkle_manual_targets=overrides,
    )


def strip_reference_policy(sidebar_policy: str) -> SparklePolicy:
    """Policy used to preview A/L strip and to detect manual overrides."""
    if sidebar_policy == "manual":
        return "alternate"
    return sidebar_policy  # type: ignore[return-value]


def simulate_auto_reference(
    speed0: tuple[int, int, int],
    params: SimParams,
    sidebar_policy: str,
) -> dict[int, int]:
    """Per-turn targets from the selected sidebar policy (no manual overrides)."""
    ref_params = SimParams(
        tmax=params.tmax,
        speed0=params.speed0,
        sparkle_initial_advance=params.sparkle_initial_advance,
        sparkle_advance=params.sparkle_advance,
        l_speed_bonus=params.l_speed_bonus,
        sparkle_policy=strip_reference_policy(sidebar_policy),
        sparkle_manual_targets={},
    )
    _, auto_advance, _, _ = simulate_action(speed0, ref_params)
    if auto_advance.empty:
        return {}
    return {
        int(row["SparkleActionNo"]): int(row["TargetIdx"])
        for _, row in auto_advance.iterrows()
    }


def _sparkle_plot_x(action_value: float, x_offset: tuple[float, float, float]) -> float:
    return float(action_value) + x_offset[SPARKLE]


def render_manual_strip_below_chart(
    advance_df,
    _action_df,
    params: SimParams,
    sidebar_policy: str,
    overrides_used: dict[int, int],
    *,
    tmax: float,
    x_offset: tuple[float, float, float],
) -> dict[int, int]:
    """Horizontal A/L pickers under the chart, spaced by Sparkle action AV (red lines)."""
    auto_policy = effective_auto_policy(sidebar_policy)

    head_l, head_r = st.columns([5, 1])
    with head_l:
        if overrides_used:
            st.caption(
                f"花火拉条（图下对齐红线）· 手动 {len(overrides_used)} 次 · "
                f"其余按 `{auto_policy}`"
            )
        elif sidebar_policy == "manual":
            st.caption("花火拉条（图下对齐红线）· 默认 `alternate` · 点 A / L 修改")
        else:
            st.caption(
                f"花火拉条（图下对齐红线）· 当前 `{sidebar_policy}` · 改任一次即切手动"
            )
    with head_r:
        if st.button("恢复自动", key="reset_manual_overrides", use_container_width=True):
            st.session_state.sparkle_manual_overrides = {}
            _clear_pull_widget_keys()
            st.rerun()

    if advance_df.empty:
        st.info("当前参数下尚无花火行动。")
        return {}

    policy_targets = simulate_auto_reference(params.speed0, params, sidebar_policy)
    turns: list[tuple[int, float, object]] = []
    for _, row in advance_df.iterrows():
        turn = int(row["SparkleActionNo"])
        x_plot = _sparkle_plot_x(float(row["ActionValue"]), x_offset)
        turns.append((turn, x_plot, row))

    turns.sort(key=lambda item: item[1])

    st.markdown(_STRIP_COMPACT_CSS, unsafe_allow_html=True)

    weights = _column_weights_for_turns(turns, float(tmax))
    cols = st.columns(weights)

    new_overrides: dict[int, int] = {}
    col_i = 0
    col_i += 1  # left margin spacer

    for turn, _x_plot, row in turns:
        col_i += 1  # gap column

        policy_idx = policy_targets.get(turn, ARCHER if turn % 2 == 1 else L)
        sim_idx = int(row["TargetIdx"])

        if turn in overrides_used:
            display_idx = 0 if overrides_used[turn] == ARCHER else 1
        else:
            display_idx = 0 if sim_idx == ARCHER else 1

        with cols[col_i]:
            choice = st.radio(
                "拉条",
                PULL_LABELS,
                index=display_idx,
                key=f"sparkle_pull_{turn}",
                horizontal=True,
                label_visibility="collapsed",
            )
            chosen_idx = LABEL_TO_IDX[choice]
            if chosen_idx != policy_idx:
                new_overrides[turn] = chosen_idx

        col_i += 1

    return new_overrides


def sync_overrides_after_panel(new_overrides: dict[int, int], sidebar_policy: str) -> bool:
    """Update session state; return True if a rerun is needed."""
    old = dict(st.session_state.sparkle_manual_overrides)
    if new_overrides == old:
        return False

    if new_overrides and not old:
        if sidebar_policy != "manual":
            st.session_state.sparkle_policy_base = sidebar_policy

    st.session_state.sparkle_manual_overrides = new_overrides
    return True
