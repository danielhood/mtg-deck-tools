/** Plain-text deck import template (UX13b) — keep in sync with docs/specs/product/deck-input.md */

export const DECK_IMPORT_TEMPLATE = `Commander
Your Commander Name Here

Deck
1x Sol Ring
1x Grave Pact
14 Swamp
Forest x13

# One card per line. Optional quantity: 1x Card, 1 Card, 14 Card, or Card x14
# Section headers Commander and Deck are optional (use Commander for each partner line).
# Lines starting with # are comments. Sideboard sections are ignored.
`;

export const DECK_IMPORT_TEMPLATE_FILENAME = "deck-import-template.txt";

export function downloadDeckImportTemplate(): void {
  const blob = new Blob([DECK_IMPORT_TEMPLATE], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = DECK_IMPORT_TEMPLATE_FILENAME;
  anchor.click();
  URL.revokeObjectURL(url);
}
