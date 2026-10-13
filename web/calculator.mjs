// Adult hypernatremia estimation; mirrors water_deficit.calculate_metrics.
function within(name, value, min, max) {
  if (typeof value !== "number" || !Number.isFinite(value) ||
      value < min || value > max) {
    throw new RangeError(name + " must be between " + min + " and " + max + ".");
  }
  return value;
}

export function calculateMetrics({
  weight_kg, serum_sodium, tbw_fraction,
  target_sodium = 140, fluid_sodium = 0, fluid_potassium = 0
}) {
  const weight = within("Weight", weight_kg, 1, 500);
  const sodium = within("Measured sodium", serum_sodium, 100, 250);
  const fraction = within("TBW fraction", tbw_fraction, 0.3, 0.8);
  const target = within("Target sodium", target_sodium, 120, 200);
  const fluidNa = within("Infusate sodium", fluid_sodium, 0, 600);
  const fluidK = within("Infusate potassium", fluid_potassium, 0, 200);
  if (sodium <= 145) throw new RangeError("Measured sodium must exceed 145 mmol/L (hypernatremia).");
  if (target > sodium) throw new RangeError("Target sodium cannot exceed measured sodium.");
  const tbw = weight * fraction;
  return {
    weight_kg: weight,
    serum_sodium_mmol_l: sodium,
    target_sodium_mmol_l: target,
    tbw_fraction: fraction,
    total_body_water_l: tbw,
    free_water_deficit_l: Math.max(0, tbw * (sodium / target - 1)),
    fluid_sodium_mmol_l: fluidNa,
    fluid_potassium_mmol_l: fluidK,
    estimated_sodium_change_per_l_mmol_l: (fluidNa + fluidK - sodium) / (tbw + 1)
  };
}
