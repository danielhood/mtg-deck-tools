# Scryfall bulk data metadata fields

Properties on a **bulk data download object** from the Scryfall `/bulk-data` API — not fields on individual cards inside the JSON file.

For oracle card object fields, see [oracle-card-fields.md](oracle-card-fields.md).

| Property | Type | Details |
| --- | --- | --- |
| `id` | UUID | A unique ID for this bulk item. |
| `uri` | URI | The Scryfall API URI for this file. |
| `type` | String | A computer-readable string for the kind of bulk item (e.g. `oracle_cards`). |
| `name` | String | A human-readable name for this file. |
| `description` | String | A human-readable description for this file. |
| `download_uri` | URI | The URI that hosts this bulk file for fetching. |
| `updated_at` | Timestamp | The time when this file was last updated. |
| `size` | Integer | The size of this file in integer bytes. |
| `content_type` | MIME Type | The MIME type of this file. |
| `content_encoding` | Encoding | The Content-Encoding used when you download the file. |
