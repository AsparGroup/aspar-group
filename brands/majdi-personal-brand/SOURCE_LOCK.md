# SOURCE LOCK — Majdi Personal Branding

Status: ACTIVE / CANONICAL

## Purpose
This file is the mandatory pre-execution lock for every task involving Majdi Garbouj personal branding: carousel, social post, cover, personal-brand visual, template, photo selection, copy-to-design routing, or Canva generation.

## Canonical sources
1. Canva Brand Kit: `Majdi Garbouj` — brand kit id `kAHUKzrWU3g`.
2. Google Drive folder: `Palette couleurs des marques` — folder id `1ENaD-iyyG_AfY60qtL4TRq7dhXlG88Og`.
3. Google Drive source registry: `01 — SOURCE AUTHORITY & DATA REGISTRY` — file id `1nEjrIIbkBnsRubyLvuElxXCLsUP0BNcO6uSrPmKA-24`.
4. Approved photo library must be resolved from Drive before using or generating a portrait asset.

## Canonical palette
Personal branding is monochrome / silver / ivory. No brand accent color is allowed unless a newer canonical source explicitly supersedes this file.

- `#111111`
- `#0F0F0F`
- `#2B2B2B`
- `#3F3F3F`
- `#6E6E6E`
- `#8A8A8A`
- `#A0A0A0`
- `#C8C8C8`
- `#D8D8D2`
- `#F7F7F2`
- `#FFFFFF`

## Typography
- Primary family: `Montserrat`.
- Approved weights: Light, Regular, Medium, SemiBold, Bold, ExtraBold.

## Identity elements
- Majdi Garbouj handwritten signature is a canonical distinguishing element.
- Monogram / icon may be used when sourced from the canonical brand assets.
- Portrait treatment should remain monochrome / dark / premium unless the canonical source says otherwise.

## Mandatory behavior
Before any personal-branding design execution, the agent MUST:
1. Resolve `brand = majdi_personal_brand`.
2. Load this SOURCE LOCK.
3. Resolve the Canva Brand Kit and relevant Drive assets.
4. Reuse canonical palette, typography, logo/signature and approved photos.
5. Reject blue, yellow, green, orange or any other non-canonical brand color even if present in an inspiration reference.
6. Treat external references only as composition / hierarchy / rhythm inspiration, never as brand authority.
7. Never ask the user to resend the visual identity when these canonical sources are accessible and non-conflicting.
8. Ask the user only when a canonical source is missing, inaccessible, or two canonical sources conflict.

## STOP conditions
`SOURCE_LOCK = STOP` if:
- canonical brand sources cannot be resolved;
- a requested asset is not approved and would require inventing a replacement;
- there is a conflict between canonical sources that cannot be resolved automatically.

Otherwise: `SOURCE_LOCK = PASS` and execution continues.
