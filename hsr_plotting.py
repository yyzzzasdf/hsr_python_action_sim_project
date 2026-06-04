from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from hsr_core import SimParams


def plot_merged_action_axis(
    action_df: pd.DataFrame,
    advance_df: pd.DataFrame,
    params: SimParams | None = None,
    x_offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> go.Figure:
    """Plot merged action axis."""

    if params is None:
        params = SimParams()

    fig = go.Figure()
    y_min = 0.0
    y_max = 1.0
    y_base = 0.5

    fig.add_trace(
        go.Scatter(
            x=[0, params.tmax],
            y=[y_base, y_base],
            mode="lines",
            line=dict(color="black", width=1),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    colors = ["red", "blue", "green"]
    dashes = ["solid", "dash", "dash"]

    for name, color, dash in zip(params.char_names, colors, dashes):
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color=color, dash=dash, width=2),
                name=name,
            )
        )

    text_y = [0.92, 0.78, 0.64]

    for i, name in enumerate(params.char_names):
        sub = action_df[action_df["Character"] == name]

        for _, row in sub.iterrows():
            x = float(row["ActionValue"]) + x_offset[i]
            action_no = int(row["ActionCount"])
            speed = int(row["SpeedAtAction"])

            fig.add_trace(
                go.Scatter(
                    x=[x, x],
                    y=[y_min, y_max],
                    mode="lines",
                    line=dict(color=colors[i], dash=dashes[i], width=2),
                    showlegend=False,
                    hovertemplate=(
                        f"角色：{name}<br>"
                        f"第 {action_no} 次行动<br>"
                        f"行动值：{row['ActionValue']:.6f}<br>"
                        f"速度：{speed}<extra></extra>"
                    ),
                )
            )

            fig.add_annotation(
                x=x,
                y=text_y[i],
                text=f"{name}{action_no}",
                showarrow=False,
                textangle=-90,
                font=dict(size=10),
            )

    if not advance_df.empty:
        for _, row in advance_df.iterrows():
            if bool(row["IsWasted"]):
                fig.add_annotation(
                    x=float(row["ActionValue"]),
                    y=0.12,
                    text=f"拉{row['Target']}浪费 {row['WastePercent']:.1f}%",
                    showarrow=False,
                    font=dict(size=11, color="black"),
                )

    fig.update_layout(
        title="三角色行动值数轴仿真：合并显示",
        xaxis_title="行动值",
        yaxis_title="行动数轴",
        xaxis=dict(range=[0, params.tmax]),
        yaxis=dict(range=[y_min, y_max], tickvals=[y_base], ticktext=["行动数轴"]),
        legend=dict(orientation="v"),
        hovermode="closest",
        height=520,
        margin=dict(l=60, r=40, t=60, b=60),
    )

    return fig


def plot_separated_action_axis(
    action_df: pd.DataFrame,
    advance_df: pd.DataFrame,
    params: SimParams | None = None,
) -> go.Figure:
    """Plot separated action axes."""

    if params is None:
        params = SimParams()

    fig = go.Figure()
    y_pos = [1.00, 1.18, 1.36]
    symbols = ["circle", "square", "triangle-up"]
    colors = ["red", "blue", "green"]

    for i, name in enumerate(params.char_names):
        fig.add_trace(
            go.Scatter(
                x=[0, params.tmax],
                y=[y_pos[i], y_pos[i]],
                mode="lines",
                line=dict(color="black", width=1),
                showlegend=False,
                hoverinfo="skip",
            )
        )

        sub = action_df[action_df["Character"] == name]
        customdata = None
        if len(sub) > 0:
            customdata = np.stack([sub["Character"], sub["ActionCount"], sub["SpeedAtAction"]], axis=1)

        fig.add_trace(
            go.Scatter(
                x=sub["ActionValue"],
                y=[y_pos[i]] * len(sub),
                mode="markers+text",
                marker=dict(size=11, symbol=symbols[i], color=colors[i]),
                text=sub["ActionCount"].astype(str),
                textposition="top center",
                name=name,
                customdata=customdata,
                hovertemplate=(
                    "角色：%{customdata[0]}<br>"
                    "第 %{customdata[1]} 次行动<br>"
                    "行动值：%{x:.6f}<br>"
                    "速度：%{customdata[2]}<extra></extra>"
                ),
            )
        )

    if not advance_df.empty:
        for _, row in advance_df.iterrows():
            if bool(row["IsWasted"]):
                target_idx = int(row["TargetIdx"])
                fig.add_annotation(
                    x=float(row["ActionValue"]),
                    y=y_pos[target_idx] - 0.055,
                    text=f"浪费 {row['WastePercent']:.1f}%",
                    showarrow=False,
                    font=dict(size=11, color="black"),
                )

    fig.update_layout(
        title="三角色行动值数轴仿真：分开显示",
        xaxis_title="行动值",
        yaxis=dict(range=[0.90, 1.46], tickvals=y_pos, ticktext=params.char_names),
        xaxis=dict(range=[0, params.tmax]),
        height=520,
        margin=dict(l=60, r=40, t=60, b=60),
    )

    return fig


def plot_waste_heatmap(
    result_df: pd.DataFrame,
    v_sparkle: int,
    v_archer_list: list[int] | np.ndarray,
    v_rin_list: list[int] | np.ndarray,
) -> go.Figure:
    """Plot heatmap of total Sparkle advance waste."""

    z = np.full((len(v_rin_list), len(v_archer_list)), np.nan)

    for i, v_rin in enumerate(v_rin_list):
        for j, v_archer in enumerate(v_archer_list):
            idx = (
                (result_df["vSparkle"] == v_sparkle)
                & (result_df["vArcher"] == v_archer)
                & (result_df["vRin"] == v_rin)
            )
            if idx.any():
                z[i, j] = float(result_df.loc[idx, "WasteTotalPercent"].iloc[0])

    fig = go.Figure(
        data=go.Heatmap(
            x=list(v_archer_list),
            y=list(v_rin_list),
            z=z,
            colorscale="Viridis",
            colorbar=dict(title="浪费百分比"),
            hovertemplate=(
                "Archer速度：%{x}<br>"
                "远坂凛速度：%{y}<br>"
                "总浪费：%{z:.2f}%<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=f"花火拉条总浪费百分比，花火速度 = {v_sparkle}",
        xaxis_title="Archer 速度",
        yaxis_title="远坂凛速度",
        height=560,
    )

    return fig


def plot_alternation_heatmap(
    result_df: pd.DataFrame,
    v_sparkle: int,
    v_archer_list: list[int] | np.ndarray,
    v_rin_list: list[int] | np.ndarray,
) -> go.Figure:
    """Plot heatmap of actual Archer/Rin strict alternation."""

    z = np.full((len(v_rin_list), len(v_archer_list)), np.nan)

    for i, v_rin in enumerate(v_rin_list):
        for j, v_archer in enumerate(v_archer_list):
            idx = (
                (result_df["vSparkle"] == v_sparkle)
                & (result_df["vArcher"] == v_archer)
                & (result_df["vRin"] == v_rin)
            )
            if idx.any():
                z[i, j] = float(result_df.loc[idx, "ActualAltOK"].iloc[0])

    colorscale = [
        [0.0, "rgb(220, 60, 60)"],
        [0.49, "rgb(220, 60, 60)"],
        [0.50, "rgb(60, 170, 80)"],
        [1.0, "rgb(60, 170, 80)"],
    ]

    fig = go.Figure(
        data=go.Heatmap(
            x=list(v_archer_list),
            y=list(v_rin_list),
            z=z,
            zmin=0,
            zmax=1,
            colorscale=colorscale,
            colorbar=dict(title="是否交替", tickvals=[0, 1], ticktext=["0 不严格", "1 严格"]),
            hovertemplate=(
                "Archer速度：%{x}<br>"
                "远坂凛速度：%{y}<br>"
                "严格交替：%{z}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=f"Archer / 远坂凛是否严格交替，花火速度 = {v_sparkle}",
        xaxis_title="Archer 速度",
        yaxis_title="远坂凛速度",
        height=560,
    )

    return fig
