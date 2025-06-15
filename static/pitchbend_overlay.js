export const BASE_NOTE = 36;
export const SEMI_UNIT = 170.6458282470703;

export function computeOverlayNotes(sequence, selectedRow, ticksPerBeat, overrides = null, seed = false) {
  const overlay = [];
  if (selectedRow === null || selectedRow === undefined) return overlay;
  if (!sequence || !ticksPerBeat) return overlay;
  sequence.forEach((ev, idx) => {
    if (ev.n !== selectedRow) return;
    const pb = ev.a && ev.a.PitchBend;
    let semis = 0;
    if (pb && pb.length) {
      semis = Math.round(pb[0].value / SEMI_UNIT);
    }
    const id = ev.id ?? idx;
    if (overrides && overrides[id] !== undefined) {
      semis = overrides[id];
    } else if (seed && overrides) {
      overrides[id] = semis;
    }
    const viz = BASE_NOTE + semis;
    if (viz < 0 || viz > 127) return;
    overlay.push({
      id,
      semitone: semis,
      noteNumber: viz,
      startTime: ev.t / ticksPerBeat,
      duration: ev.g / ticksPerBeat
    });
  });
  return overlay;
}
