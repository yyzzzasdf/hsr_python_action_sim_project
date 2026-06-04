from __future__ import annotations

import pandas as pd

from hsr_core import SimParams, simulate_action
from hsr_plotting import plot_waste_heatmap, plot_alternation_heatmap


def run_speed_sweep() -> pd.DataFrame:
    params = SimParams()

    v_sparkle_list = [160]
    v_archer_list = list(range(100, 141, 5))
    v_rin_list = list(range(90, 131, 5))

    rows = []

    for vs in v_sparkle_list:
        for va in v_archer_list:
            for vr in v_rin_list:
                speed0 = (vs, va, vr)
                action_df, advance_df, flags, _ = simulate_action(speed0, params)
                rows.append(
                    {
                        "vSparkle": vs,
                        "vArcher": va,
                        "vRin": vr,
                        "ActualAltOK": int(flags["ActualAltOK"]),
                        "TargetAltOK": int(flags["TargetAltOK"]),
                        "SparkleTurns": int((action_df["Character"] == "花火").sum()),
                        "ArcherTurns": int((action_df["Character"] == "Archer").sum()),
                        "RinTurns": int((action_df["Character"] == "远坂凛").sum()),
                        "WasteNum": int(advance_df["IsWasted"].sum()),
                        "WasteTotalPercent": float(advance_df["WastePercent"].sum()),
                    }
                )

    result_df = pd.DataFrame(rows)
    result_df.to_excel("speed_sweep_result.xlsx", index=False)

    fig_waste = plot_waste_heatmap(result_df, v_sparkle=v_sparkle_list[0], v_archer_list=v_archer_list, v_rin_list=v_rin_list)
    fig_waste.write_html("speed_sweep_waste_heatmap.html")

    fig_alt = plot_alternation_heatmap(result_df, v_sparkle=v_sparkle_list[0], v_archer_list=v_archer_list, v_rin_list=v_rin_list)
    fig_alt.write_html("speed_sweep_alternation_heatmap.html")

    return result_df


def main() -> None:
    result_df = run_speed_sweep()
    print(result_df.to_string(index=False))
    print("\n已生成：")
    print("- speed_sweep_result.xlsx")
    print("- speed_sweep_waste_heatmap.html")
    print("- speed_sweep_alternation_heatmap.html")


if __name__ == "__main__":
    main()
