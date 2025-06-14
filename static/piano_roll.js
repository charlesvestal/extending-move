export class PianoRoll {
  constructor(container, options = {}) {
    this.container = container;
    this.notes = options.notes || [];
    this.region = options.region || 4.0;
    this.draw();
  }

  getRange() {
    if (!this.notes.length) return { min: 60, max: 71 };
    let min = Math.min(...this.notes.map(n => n.noteNumber));
    let max = Math.max(...this.notes.map(n => n.noteNumber));
    if (max - min < 11) {
      const extra = 11 - (max - min);
      min = Math.max(0, min - Math.floor(extra / 2));
      max = Math.min(127, max + Math.ceil(extra / 2));
    }
    return { min, max };
  }

  draw() {
    const { min, max } = this.getRange();
    const noteRange = max - min + 1;
    const containerWidth = this.container.clientWidth;
    const containerHeight = this.container.clientHeight;
    const h = containerHeight / noteRange;
    this.container.innerHTML = '';
    this.notes.forEach(n => {
      const el = document.createElement('div');
      el.className = 'note';
      const x = (n.startTime / this.region) * containerWidth;
      const w = (n.duration / this.region) * containerWidth;
      const y = containerHeight - (n.noteNumber - min + 1) * h;
      el.style.left = x + 'px';
      el.style.top = y + 'px';
      el.style.width = w + 'px';
      el.style.height = h + 'px';
      this.container.appendChild(el);
    });
  }
}
