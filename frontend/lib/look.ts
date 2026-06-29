/** Tiny localStorage helper for the "bring this look" feature.
 *
 * When a user picks a recommended style to take to a salon, we stash its id +
 * name; the booking form reads it back and attaches it to the request.
 */

export interface SavedLook {
  id: string;
  name: string;
}

const KEY = "cutpoint_look";

export function saveLook(look: SavedLook): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(look));
  } catch {
    /* storage unavailable */
  }
}

export function getSavedLook(): SavedLook | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as SavedLook) : null;
  } catch {
    return null;
  }
}

export function clearLook(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* storage unavailable */
  }
}
