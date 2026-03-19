/**
 * Palette of visually distinct colors for dark backgrounds.
 * Order chosen so adjacent indices contrast well.
 */
const PALETTE = [
  '#ef5350', // red-5
  '#ec407a', // pink-5
  '#ab47bc', // purple-5
  '#5c6bc0', // indigo-5
  '#42a5f5', // blue-5
  '#29b6f6', // light-blue-5
  '#26c6da', // cyan-5
  '#26a69a', // teal-5
  '#66bb6a', // green-5
  '#9ccc65', // light-green-5
  '#d4e157', // lime-5
  '#ffee58', // yellow-5
  '#ffca28', // amber-5
  '#ffa726', // orange-5
  '#ff7043', // deep-orange-5
];

/**
 * Simple string hash → consistent palette index.
 */
function hashString(s: string): number {
  let hash = 0;
  for (let i = 0; i < s.length; i++) {
    hash = ((hash << 5) - hash + s.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

/**
 * Returns a consistent color for a given name (metric name, category name, etc.)
 */
export function colorFor(name: string): string {
  return PALETTE[hashString(name) % PALETTE.length];
}

/**
 * Returns an array of consistent colors for an array of names.
 * If two names hash to the same color, shifts the second to the next available.
 */
export function colorsFor(names: string[]): string[] {
  const used = new Set<string>();
  return names.map((name) => {
    let idx = hashString(name) % PALETTE.length;
    let color = PALETTE[idx];
    // Resolve collisions by stepping forward
    let attempts = 0;
    while (used.has(color) && attempts < PALETTE.length) {
      idx = (idx + 1) % PALETTE.length;
      color = PALETTE[idx];
      attempts++;
    }
    used.add(color);
    return color;
  });
}
