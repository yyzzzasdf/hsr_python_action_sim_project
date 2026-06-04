from __future__ import annotations

import io
import pandas as pd
import streamlit as st

from hsr_core import SimParams, simulate_action
from hsr_plotting import (
    plot_merged_action_axis,
    plot_separated_action_axis,
    plot_waste_heatmap,
    plot_alternation_heatmap,
)

st.set_page_config(page_title="HSR 行动轴仿真器", layout="wide")
st.title("星穹铁道行动轴交互仿真器")

with st.sidebar:
    st.header("基础参数")

    tmax = st.number_input("仿真总行动值", min_value=100, max_value=5000, value=500, step=50)

    v_sparkle = st.slider("花火速度", min_value=50, max_value=250, value=160, step=1)
    v_archer = st.slider("Archer速度", min_value=50, max_value=250, value=120, step=1)
    v_rin = st.slider("远坂凛速度", min_value=50, max_value=250, value=100, step=1)

    st.header("规则参数")

    sparkle_initial_advance = st.slider("花火入战斗行动提前百分比", 0, 100, 40, 1) / 100.0
    sparkle_advance = st.slider("花火每次行动提前百分比", 0, 100, 50, 1) / 100.0
    rin_speed_bonus = st.slider("远坂凛第一次行动后速度增加", 0, 100, 20, 1)

    sparkle_policy = st.selectbox(
        "花火拉条策略",
        ["alternate", "always_archer", "always_rin", "min_progress", "max_remaining_av", "avoid_waste"],
        index=0,
    )

    offset_on = st.checkbox("同行动值竖线轻微错开", value=False)

params = SimParams(
    tmax=float(tmax),
    speed0=(v_sparkle, v_archer, v_rin),
    sparkle_initial_advance=sparkle_initial_advance,
    sparkle_advance=sparkle_advance,
    rin_speed_bonus=rin_speed_bonus,
    sparkle_policy=sparkle_policy,
)

speed0 = (v_sparkle, v_archer, v_rin)
action_df, advance_df, flags, final_state = simulate_action(speed0, params)

waste_num = int(advance_df["IsWasted"].sum()) if not advance_df.empty else 0
waste_total = float(advance_df["WastePercent"].sum()) if not advance_df.empty else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("花火行动次数", int((action_df["Character"] == "花火").sum()))
c2.metric("Archer行动次数", int((action_df["Character"] == "Archer").sum()))
c3.metric("远坂凛行动次数", int((action_df["Character"] == "远坂凛").sum()))
c4.metric("花火拉条总浪费", f"{waste_total:.2f}%")

c5, c6 = st.columns(2)
c5.info("Archer / 远坂凛实际行动：" + ("严格交替" if flags["ActualAltOK"] else "不是严格交替"))
c6.info("花火拉条目标：" + ("严格交替" if flags["TargetAltOK"] else "不是严格交替"))

x_offset = (-0.35, 0.0, 0.35) if offset_on else (0.0, 0.0, 0.0)

tab1, tab2, tab3, tab4 = st.tabs(["合并行动轴", "分角色行动轴", "行动与拉条表", "速度鲁棒性扫描"])

with tab1:
    fig = plot_merged_action_axis(action_df, advance_df, params, x_offset=x_offset)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = plot_separated_action_axis(action_df, advance_df, params)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("行动记录")
    st.dataframe(action_df, use_container_width=True)

    st.subheader("花火拉条记录")
    st.dataframe(advance_df, use_container_width=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        action_df.to_excel(writer, sheet_name="ActionLog", index=False)
        advance_df.to_excel(writer, sheet_name="AdvanceLog", index=False)
        summary_df = pd.DataFrame([
            {
                "vSparkle": v_sparkle,
                "vArcher": v_archer,
                "vRin": v_rin,
                "WasteNum": waste_num,
                "WasteTotalPercent": waste_total,
                "ActualAltOK": flags["ActualAltOK"],
                "TargetAltOK": flags["TargetAltOK"],
            }
        ])
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

    st.download_button(
        "下载当前仿真 Excel",
        data=output.getvalue(),
        file_name="hsr_action_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with tab4:
    st.subheader("速度鲁棒性扫描")
    st.caption("默认固定当前花火速度，扫描 Archer 和远坂凛速度。")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        archer_min = st.number_input("Archer速度下限", value=100, step=1)
        archer_max = st.number_input("Archer速度上限", value=140, step=1)
        archer_step = st.number_input("Archer速度步长", value=5, min_value=1, step=1)

    with col_b:
        rin_min = st.number_input("远坂凛速度下限", value=90, step=1)
        rin_max = st.number_input("远坂凛速度上限", value=130, step=1)
        rin_step = st.number_input("远坂凛速度步长", value=5, min_value=1, step=1)

    with col_c:
        sweep_v_sparkle = st.number_input("固定花火速度", value=v_sparkle, step=1)
        run_sweep = st.button("开始扫描")

    if run_sweep:
        v_archer_list = list(range(int(archer_min), int(archer_max) + 1, int(archer_step)))
        v_rin_list = list(range(int(rin_min), int(rin_max) + 1, int(rin_step)))

        rows = []
        progress_bar = st.progress(0)
        total = len(v_archer_list) * len(v_rin_list)
        count = 0

        for va in v_archer_list:
            for vr in v_rin_list:
                sweep_params = SimParams(
                    tmax=float(tmax),
                    speed0=(int(sweep_v_sparkle), int(va), int(vr)),
                    sparkle_initial_advance=sparkle_initial_advance,
                    sparkle_advance=sparkle_advance,
                    rin_speed_bonus=rin_speed_bonus,
                    sparkle_policy=sparkle_policy,
                )
                a_df, adv_df, flg, _ = simulate_action((int(sweep_v_sparkle), int(va), int(vr)), sweep_params)
                rows.append(
                    {
                        "vSparkle": int(sweep_v_sparkle),
                        "vArcher": int(va),
                        "vRin": int(vr),
                        "ActualAltOK": int(flg["ActualAltOK"]),
                        "TargetAltOK": int(flg["TargetAltOK"]),
                        "SparkleTurns": int((a_df["Character"] == "花火").sum()),
                        "ArcherTurns": int((a_df["Character"] == "Archer").sum()),
                        "RinTurns": int((a_df["Character"] == "远坂凛").sum()),
                        "WasteNum": int(adv_df["IsWasted"].sum()),
                        "WasteTotalPercent": float(adv_df["WastePercent"].sum()),
                    }
                )
                count += 1
                progress_bar.progress(count / total)

        result_df = pd.DataFrame(rows)
        st.subheader("扫描结果")
        st.dataframe(result_df, use_container_width=True)

        fig_waste = plot_waste_heatmap(result_df, int(sweep_v_sparkle), v_archer_list, v_rin_list)
        st.plotly_chart(fig_waste, use_container_width=True)

        fig_alt = plot_alternation_heatmap(result_df, int(sweep_v_sparkle), v_archer_list, v_rin_list)
        st.plotly_chart(fig_alt, use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            result_df.to_excel(writer, sheet_name="Sweep", index=False)

        st.download_button(
            "下载扫描结果 Excel",
            data=output.getvalue(),
            file_name="hsr_speed_sweep_result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
