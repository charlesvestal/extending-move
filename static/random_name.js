const ADJECTIVES = [
  'Fuzzy', 'Groovy', 'Smooth', 'Bouncy', 'Sharp', 'Lush', 'Bright', 'Warm'
];
const NOUNS = [
  'Bass', 'Chord', 'Lead', 'Pad', 'Beat', 'Rhythm', 'Tone', 'Wave'
];
function generateRandomName() {
  const adj = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)];
  const noun = NOUNS[Math.floor(Math.random() * NOUNS.length)];
  return `${adj} ${noun}`;
}
if (typeof window !== 'undefined') {
  window.generateRandomName = generateRandomName;
}
