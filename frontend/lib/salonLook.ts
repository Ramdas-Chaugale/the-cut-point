/**
 * Placeholder branding for salons that have not uploaded a photo.
 *
 * None of the seeded salons has one, so without this every card and banner
 * drew the same dark tile. Hashing the name gives each salon a colour that is
 * stable across visits and distinct from its neighbours in the grid.
 */

/** A stable hue in [0, 360) derived from the salon name. */
export function salonHue(name: string): number {
  let h = 0;
  for (let i = 0; i < name.length; i += 1) {
    h = (h * 31 + name.charCodeAt(i)) % 360;
  }
  return h;
}

/** Up to two initials, so "Sharp Fades Barbers" reads as SF rather than S. */
export function salonInitials(name: string): string {
  return name
    .split(/\s+/)
    .filter((w) => /[a-z0-9]/i.test(w))
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
}

/** The diagonal gradient used behind the initials. */
export function salonGradient(name: string): string {
  const h = salonHue(name);
  return `linear-gradient(135deg, hsl(${h} 42% 32%), hsl(${(h + 40) % 360} 48% 20%))`;
}
