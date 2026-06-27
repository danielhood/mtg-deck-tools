const RARITY_LABELS: Record<string, string> = {
  common: "Common",
  uncommon: "Uncommon",
  rare: "Rare",
  mythic: "Mythic",
  special: "Special",
  bonus: "Bonus",
};

export function normalizeRarityId(rarity: string | null | undefined): string | null {
  const id = rarity?.trim().toLowerCase();
  return id ? id : null;
}

export function formatRarityLabel(rarity: string | null | undefined): string | null {
  const id = normalizeRarityId(rarity);
  if (!id) return null;
  return RARITY_LABELS[id] ?? id.charAt(0).toUpperCase() + id.slice(1);
}

export function rarityCssClass(rarity: string | null | undefined): string {
  const id = normalizeRarityId(rarity);
  if (!id) return "";
  if (id in RARITY_LABELS) return `rarity-${id}`;
  return "rarity-unknown";
}
