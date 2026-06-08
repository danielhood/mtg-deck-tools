export const MANA_PIPS = [
  { id: "W", label: "White" },
  { id: "U", label: "Blue" },
  { id: "B", label: "Black" },
  { id: "R", label: "Red" },
  { id: "G", label: "Green" },
] as const;

export const COLOR_ORDER = ["W", "U", "B", "R", "G"] as const;

/** Colorless cards in deck-view filters — shown as void (∅) like the wizard. */
export const VOID_COLOR_ID = "void";
