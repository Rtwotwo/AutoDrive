# User guide

## Import and identify

Use an arXiv abstract/PDF URL, ID, or local PDF. Verify the original English title, authors, affiliations, paper URL, project page, and code repository. PDF uploads can identify an embedded arXiv ID and fetch metadata. If that service fails, use **Re-identify paper information** or edit the card. Preserve manually verified values.

Rename a workspace item without changing its paper title; pin frequent items or move them to the reversible recycle bin. Active items cannot be removed while processing.

## Connect a model

Create a named profile with base URL, exact model ID, and API key. OpenAI-compatible does not guarantee image support or identical context limits. Save credentials only for Windows-user-encrypted persistence; otherwise use memory-only mode. Keep keys out of prompts, screenshots, exports, and Git. Changing providers requires checking the key again.

Vision analysis needs a compatible model. Text-only models can use extracted text and captions. Provider usage can incur charges. Local storage does not prevent selected content from being sent to the configured model.

## Prepare illustrations

Check architecture diagrams, quantitative results, and qualitative examples. Embedded images may be only one panel, with vector labels or arrows outside the raster object. Prefer a complete caption-based crop when needed. Use native extraction for complete raster figures or import a clean PNG/JPEG replacement.

Uncertain full-page candidates stay unselected. Crop them manually, checking axes, table headings, units, legends, and all panels. Retain attribution for project-page media. Importing an image does not grant permission to redistribute it.

## Write and design

Select a technical explanation, overview, or available editorial style. Adaptive mode chooses structure from the paper and available evidence. A length target is not permission to invent content. Long responses use bounded continuation and private stage checkpoints.

Review the identity card, mechanism, experimental conditions, comparisons, qualitative examples, and limitations. Page arrays belong in the evidence panel, not the final prose. Apply a built-in theme or Baoyu formatting; generate a wide or square local cover if useful. Inspect the mobile preview. HTML/ZIP export creates local files only.

## Submit a draft

1. Enter AppID/AppSecret locally. Confirm material and draft permissions in the official WeChat developer console.
2. Allowlist the actual public egress IP. VPNs, proxies, and network changes can change it.
3. Choose a cover and inspect title, byline, digest, source link, and formatted body in the upload preview.
4. Use field preparation for oversized card fields. It preserves the original article and records adjustments.
5. Complete review checks, approve the current version, and submit. Retain the receipt.
6. Check the official draft box, add videos where needed, send a phone preview, and publish there.

The upload adapter conservatively uses a 32-character title, 16-character byline, and 120-character card digest. These are application policies, not manuscript limits. The short digest is separate from the body summary. HTML markup counts toward the body budget: the application can compact it, but does not silently delete article content.

## Direct and batch modes

Direct mode explicitly selects a paper for automatic generation and draft submission. Discovery mode additionally checks project and implementation resources. Neither mode claims human approval; review the result in WeChat.

Metadata is listed first. Each queue downloads and completes one paper before starting the next. Immediate stop interrupts at the next safe boundary; finish-current stops before the next paper. A stop cannot undo a request already accepted by WeChat. Check receipts before retrying.

Configure topics, model, target account, and daily cap before enabling an external scheduler. The default is five attempts per Beijing day, counting processing attempts even when they later fail, to avoid uncontrolled retries. No eligible paper means no article. Installation creates no scheduled task.

## Export and recovery

ZIP bundles contain article HTML/assets and structured editing/evidence files. They cannot be uploaded directly as a WeChat article. Use API delivery or copy rendered HTML and upload local media manually.

Back up runtime data separately from source. DPAPI settings normally require the same Windows user and machine environment; re-enter credentials on a new computer. Never attach a private backup to a public issue.
