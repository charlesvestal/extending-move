export const BASE_NOTE = 36;
export const SEMI_UNIT = 170.6458282470703;

export function noteNumberToPitchbend(n) {
  return (n - BASE_NOTE) * SEMI_UNIT;
}

export function computeOverlayNotes(sequence, selectedRow, ticksPerBeat) {
  const overlay = [];
  if (selectedRow === null || selectedRow === undefined) return overlay;
  if (!sequence || !ticksPerBeat) return overlay;
  sequence.forEach((ev, idx) => {
    if (ev.n !== selectedRow) return;
    // Treat missing or zero-length PitchBend as value 0 (C2)
    const pb = ev.a && ev.a.PitchBend;
    const value = (pb && pb.length) ? pb[0].value : 0;
    const semis = Math.round(value / SEMI_UNIT);
    const viz = BASE_NOTE + semis;
    if (viz < 0 || viz > 127) return;
    overlay.push({
      index: idx,
      noteNumber: viz,
      startTime: ev.t / ticksPerBeat,
      duration: ev.g / ticksPerBeat
    });
  });
  return overlay;
}
