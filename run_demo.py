from hsr_core import SimParams, simulate_action, export_to_excel
from hsr_plotting import plot_merged_action_axis, plot_separated_action_axis


def main() -> None:
    params = SimParams()
    speed0 = (160, 120, 100)

    action_df, advance_df, flags, _ = simulate_action(speed0, params)

    print("===================== 行动记录 =====================")
    print(action_df.to_string(index=False))

    print("\n===================== 花火拉条记录 =====================")
    print(advance_df.to_string(index=False))

    print("\n===================== 判定结果 =====================")
    print("Archer / L实际行动：", "严格交替" if flags["ActualAltOK"] else "不是严格交替")
    print("花火拉条目标：", "严格交替" if flags["TargetAltOK"] else "不是严格交替")

    fig_merged = plot_merged_action_axis(action_df, advance_df, params)
    fig_merged.write_html("demo_action_axis.html")

    fig_separated = plot_separated_action_axis(action_df, advance_df, params)
    fig_separated.write_html("demo_action_axis_separated.html")

    export_to_excel("demo_action_result.xlsx", action_df, advance_df)

    print("\n已生成：")
    print("- demo_action_axis.html")
    print("- demo_action_axis_separated.html")
    print("- demo_action_result.xlsx")


if __name__ == "__main__":
    main()
