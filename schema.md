# Data Schema

Every document processed by this project (invoice, receipt or other) is described
by one record with the fields below. This record is the "correct answer" used to
generate test documents and to measure how accurate the extraction is.

## Fields

| Field | Type | Format | Description |
|---|---|---|---|
| `doc_type` | text | `invoice`, `receipt` or `other` | The kind of document. |
| `language` | text | `en`, `sv` or `fi` | Language of the document (English, Swedish, Finnish). |
| `supplier` | text | Free text | Name of the company that issued the document. Required. |
| `invoice_number` | text or null | e.g. `"10234"` | Stored as text so leading zeros are kept. Can be empty (`null`) for receipts. |
| `invoice_date` | date | `YYYY-MM-DD` | Always stored in this format, even if the document shows `14.9.2026` or `14 September 2026`. |
| `currency` | text | `EUR`, `SEK` or `GBP` | ISO currency code, never a symbol such as `€` or `kr`. |
| `total` | decimal | 2 decimals, e.g. `1245.50` | The final amount to pay, including VAT. |
| `vat_amount` | decimal | 2 decimals, e.g. `249.10` | The VAT amount in money, not the percentage. |

## Rules

- All values are stored in one standard (normalized) format, even though the
  document itself may show them differently. For example, `1 245,50 €` on a Finnish
  invoice is stored as `1245.50`.
- Money values use decimals, not floating-point numbers, to avoid rounding errors.
- `vat_amount` cannot be larger than `total`.
- A missing value (`null`) means the document does not have that field. It is not
  the same as "the model failed to find it".

## Example

```json
{
  "doc_type": "invoice",
  "language": "fi",
  "supplier": "Example Oy",
  "invoice_number": "10234",
  "invoice_date": "2026-09-14",
  "currency": "EUR",
  "total": 1245.50,
  "vat_amount": 249.10
}
```

## Notes

- The Python version of this schema is in `src/schema.py`.
- `schema.json` is generated automatically from `src/schema.py`. Do not edit it by hand.