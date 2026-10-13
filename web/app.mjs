import { calculateMetrics } from "./calculator.mjs";

const form = document.getElementById("calculator");
const profile = document.getElementById("profile");
const custom = document.getElementById("custom-group");
const error = document.getElementById("error");
const results = document.getElementById("results");
const empty = document.getElementById("empty");
const download = document.getElementById("download");
let lastResult = null;

profile.addEventListener("change", () => {
  custom.hidden = profile.value !== "custom";
  results.hidden = true;
  empty.hidden = false;
  download.disabled = true;
  lastResult = null;
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  error.hidden = true;
  results.hidden = true;
  empty.hidden = false;
  download.disabled = true;
  lastResult = null;
  const number = (name) => {
    const el = form.elements.namedItem(name);
    if (!el || el.value.trim() === "") throw new RangeError("Complete all numeric fields.");
    return Number(el.value);
  };
  try {
    const tbw_fraction = profile.value === "custom" ? number("tbw_fraction") : Number(profile.value);
    const result = calculateMetrics({
      weight_kg: number("weight_kg"),
      serum_sodium: number("serum_sodium"),
      target_sodium: number("target_sodium"),
      tbw_fraction,
      fluid_sodium: number("fluid_sodium"),
      fluid_potassium: number("fluid_potassium")
    });
    lastResult = result;
    document.getElementById("tbw-result").textContent = result.total_body_water_l.toFixed(2);
    document.getElementById("deficit-result").textContent = result.free_water_deficit_l.toFixed(2);
    const delta = result.estimated_sodium_change_per_l_mmol_l;
    document.getElementById("change-result").textContent =
      (delta > 0 ? "+" : "") + delta.toFixed(2);
    document.getElementById("formula-details").textContent =
      "Deficit = " + result.total_body_water_l.toFixed(2) + " × (" +
      result.serum_sodium_mmol_l + " / " + result.target_sodium_mmol_l +
      " − 1). Predicted ΔNa/L = (" + result.fluid_sodium_mmol_l + " + " +
      result.fluid_potassium_mmol_l + " − " + result.serum_sodium_mmol_l +
      ") / (" + result.total_body_water_l.toFixed(2) + " + 1).";
    results.hidden = false;
    empty.hidden = true;
    download.disabled = false;
  } catch (cause) {
    error.textContent = cause instanceof Error ? cause.message : "Invalid input.";
    error.hidden = false;
  }
});

download.addEventListener("click", () => {
  if (!lastResult) return;
  const blob = new Blob([JSON.stringify(lastResult, null, 2) + "\n"], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "water-deficit-estimate.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

form.addEventListener("reset", () => {
  queueMicrotask(() => {
    custom.hidden = true;
    error.hidden = true;
    results.hidden = true;
    empty.hidden = false;
    lastResult = null;
    download.disabled = true;
  });
});
