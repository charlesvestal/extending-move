export const BASE_NOTE = 36;
export const SEMI_UNIT = 170.6458282470703;

export function computeOverlayNotes(sequence, selectedRow, ticksPerBeat) {
  const overlay = [];
  if (selectedRow === null || selectedRow === undefined) return overlay;
  if (!sequence || !ticksPerBeat) return overlay;
  sequence.forEach((ev, idx) => {
    if (ev.n !== selectedRow) return;
    const pb = ev.a && ev.a.PitchBend;
    const value = (pb && pb.length) ? pb[0].value : 0;
    const semis = Math.round(value / SEMI_UNIT);
    const viz = BASE_NOTE + semis;
    if (viz < 0 || viz > 127) return;
    overlay.push({
      noteNumber: viz,
      startTime: ev.t / ticksPerBeat,
      duration: ev.g / ticksPerBeat,
      eventIndex: idx
    });
  });
  return overlay;
}
