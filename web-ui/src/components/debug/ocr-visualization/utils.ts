/**
 * Parse location from various formats to {x, y, width, height}
 */
export function parseLocation(
  location: unknown
): { x: number; y: number; width: number; height: number } | null {
  if (!location) return null;

  // Already in dict format: {x, y, width, height}
  if (typeof location === 'object' && !Array.isArray(location) && location !== null) {
    const loc = location as Record<string, unknown>;
    if ('x' in loc && 'y' in loc) {
      return {
        x: Number(loc.x) || 0,
        y: Number(loc.y) || 0,
        width: Number(loc.width) || 0,
        height: Number(loc.height) || 0,
      };
    }
  }

  // Array format
  if (Array.isArray(location)) {
    // Polygon format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    if (location.length >= 4 && Array.isArray(location[0])) {
      const points = location as number[][];
      const xs = points.map(p => p[0]);
      const ys = points.map(p => p[1]);
      const xMin = Math.min(...xs);
      const yMin = Math.min(...ys);
      const xMax = Math.max(...xs);
      const yMax = Math.max(...ys);
      return {
        x: xMin,
        y: yMin,
        width: xMax - xMin,
        height: yMax - yMin,
      };
    }

    // Flat array format: [x, y, width, height] or [x1, y1, x2, y2]
    if (location.length === 4 && typeof location[0] === 'number') {
      const [a, b, c, d] = location as number[];
      // Heuristic: if c,d are much larger than a,b, it's [x1,y1,x2,y2]
      if (c > a * 2 || d > b * 2) {
        return { x: a, y: b, width: c - a, height: d - b };
      }
      return { x: a, y: b, width: c, height: d };
    }
  }

  return null;
}
