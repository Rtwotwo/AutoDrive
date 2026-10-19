# Installation and troubleshooting

| Symptom | Action |
|---|---|
| `py` is missing | Install Python 3.11 with its launcher, or create `.venv` using your Python 3.11 executable and rerun setup. |
| PowerShell blocks a script | Use the documented per-invocation `-ExecutionPolicy Bypass` command; do not change machine-wide policy. |
| Package download fails | Check network and package-index settings, then rerun setup. Keep TLS verification enabled. |
| Blank desktop window | Install/repair Microsoft WebView2 Runtime. Run `python.exe desktop.py` from a terminal for local diagnostics. |
| Already-running notice | Relaunch should activate the existing window. Save work before terminating a genuinely stuck process. |
| No articles in the checkout | Data is outside source: `%LOCALAPPDATA%\PaperStudio`, your override, or a legacy private installation directory. |
| Incorrect PDF title | Re-identify the paper and check its information card; unusual page layouts still need manual verification. |
| PDF has no usable text | Run OCR externally and import the searchable result. Page images are not extracted evidence. |
| Incomplete or loose crops | Manually crop or replace with a complete image. Native embedded images may omit vector labels. |
| Missing result illustrations | Check selection and coverage for architecture, quantitative, and qualitative figures. Do not use unrelated images to satisfy coverage. |
| Model output ends early | Verify exact model ID and provider output cap; resume the saved stage. Bounded continuation cannot overcome context limits or every malformed response. |
| Generation times out | Completed stages remain available. Inspect the current job before retrying; avoid concurrent duplicate jobs. |
| Baoyu unavailable | Run `setup-formatter.ps1`, ensure Node.js/npm is available, and permit first-use package downloads. Built-in layouts work offline. |
| WeChat error `40164` | Add the API request's actual public IP to the account allowlist and save. Check proxy/VPN routing; private LAN IPs are not substitutes. |
| Authentication/permission error | Verify AppID/AppSecret pairing and actual material/draft permissions. AppID presence alone is insufficient. |
| Approval was invalidated | Content, image, cover, layout, upload-field, or account changes require reviewing the new snapshot. |
| Digest exceeds 120 characters | Use field preparation; it shortens the upload card while preserving original content and adjustment history. |
| HTML body exceeds budget | Compact formatting first, then explicitly edit large/repeated content if necessary and review again. |
| Submission outcome unknown | Inspect WeChat and the local receipt before retrying. Blind retries may create duplicates. |
| Videos absent in draft | Insert them in the official editor. Local MP4 files do not upload with HTML. |
| Daily run produces nothing | Check enablement, external scheduling, eligibility, resource verification, daily cap, and whether the computer is awake. No eligible papers is a normal no-op. |
| Encrypted credentials fail after migration | Re-enter on the new computer. Do not turn encrypted configuration into plaintext files. |

For reproduction, use synthetic or public papers and include OS/Python versions plus a redacted error. Never attach `.dpapi` files, private runtime folders, keys, cookies, token-bearing API responses, or personal account screenshots.
