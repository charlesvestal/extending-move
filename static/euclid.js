export function euclideanRhythm(steps, pulses, rotate = 0) {
  if (steps <= 0) return [];
  pulses = Math.max(0, Math.min(pulses, steps));
  rotate = ((rotate % steps) + steps) % steps;
  const pattern = [];
  let bucket = 0;
  for (let i = 0; i < steps; i++) {
    bucket += pulses;
    if (bucket >= steps) {
      bucket -= steps;
      pattern.push((i + rotate) % steps);
    }
  }
  return pattern.sort((a, b) => a - b);
}
