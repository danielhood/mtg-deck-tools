import { pollWizardMetaUntilReady, postImport, type ImportResponse } from "./api";

export const IMPORT_BUSY_LEAD = "Downloading and importing card data…";
export const IMPORT_BUSY_NOTE = "This may take several minutes.";

export const REFRESH_CONFIRM_MESSAGE =
  "Re-download Scryfall oracle bulk and rebuild the card database? This may take several minutes.";

export async function runCardImport(
  onProgress?: (message: string) => void,
): Promise<ImportResponse> {
  onProgress?.(IMPORT_BUSY_LEAD);
  const result = await postImport();
  onProgress?.("Finalizing database…");
  await pollWizardMetaUntilReady();
  return result;
}
