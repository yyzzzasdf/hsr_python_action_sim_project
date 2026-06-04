"""Streamlit UI helpers: numeric inputs with typing and mouse-wheel adjustment."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

_WHEEL_SCRIPT = """
<script>
(function () {
  const doc = window.parent.document;
  if (!doc || doc.getElementById("hsr-wheel-number-inputs")) return;

  const style = doc.createElement("style");
  style.id = "hsr-wheel-number-inputs";
  style.textContent = `
    input[type="number"].hsr-wheel-active { outline: 2px solid rgba(255, 75, 75, 0.45); }
  `;
  doc.head.appendChild(style);

  function clamp(val, min, max) {
    if (!Number.isNaN(min)) val = Math.max(min, val);
    if (!Number.isNaN(max)) val = Math.min(max, val);
    return val;
  }

  function setNativeValue(input, value) {
    const setter = Object.getOwnPropertyDescriptor(
      window.parent.HTMLInputElement.prototype,
      "value"
    )?.set;
    if (setter) {
      setter.call(input, String(value));
    } else {
      input.value = String(value);
    }
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function bindWheel(input) {
    if (input.dataset.hsrWheelBound === "1") return;
    input.dataset.hsrWheelBound = "1";

    input.addEventListener("mouseenter", () => input.classList.add("hsr-wheel-active"));
    input.addEventListener("mouseleave", () => input.classList.remove("hsr-wheel-active"));

    input.addEventListener(
      "wheel",
      (e) => {
        const hovered = input.matches(":hover");
        const focused = doc.activeElement === input;
        if (!hovered && !focused) return;

        e.preventDefault();
        e.stopPropagation();

        const step = parseFloat(input.step);
        const delta = Number.isFinite(step) ? step : 1;
        const min = input.min === "" ? NaN : parseFloat(input.min);
        const max = input.max === "" ? NaN : parseFloat(input.max);

        let val = parseFloat(input.value);
        if (Number.isNaN(val)) val = Number.isFinite(min) ? min : 0;

        val += e.deltaY < 0 ? delta : -delta;
        val = clamp(val, min, max);
        setNativeValue(input, val);
      },
      { passive: false }
    );
  }

  function bindAll() {
    doc.querySelectorAll('input[type="number"]').forEach(bindWheel);
  }

  bindAll();
  const observer = new MutationObserver(bindAll);
  observer.observe(doc.body, { childList: true, subtree: true });
})();
</script>
"""


def inject_number_input_wheel() -> None:
    """Enable mouse-wheel adjustment on all number inputs (hover or focus)."""
    components.html(_WHEEL_SCRIPT, height=0)


def int_param(
    label: str,
    *,
    min_value: int,
    max_value: int,
    value: int,
    step: int = 1,
    key: str | None = None,
    help: str | None = None,
) -> int:
    """Integer parameter: type directly or scroll wheel when hovered/focused."""
    n = st.number_input(
        label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        step=step,
        key=key,
        help=help,
    )
    return int(n)


def percent_param(
    label: str,
    *,
    value_pct: int,
    step: int = 1,
    key: str | None = None,
    help: str | None = None,
) -> float:
    """Percentage 0–100 shown in UI; returns fraction 0.0–1.0."""
    pct = int_param(
        label,
        min_value=0,
        max_value=100,
        value=value_pct,
        step=step,
        key=key,
        help=help,
    )
    return pct / 100.0
