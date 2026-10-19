# Privacy and security

Paper Studio is a single-user local desktop application. Its loopback service is not intended for public hosting, reverse-proxy exposure, or untrusted multi-user access.

Optional secret persistence uses Windows DPAPI for the current user, outside the checkout. Memory-only mode is available. Encryption does not protect against malware running as that user. Protect backups and runtime data accordingly.

Network requests have explicit purposes: arXiv/project discovery fetches public resources; writing sends selected text and optional images to the configured model; draft submission uploads prepared content to WeChat; optional formatter setup downloads packages. Local storage does not imply offline inference.

The public source contains no account configuration or private documents. Git ignore rules are a convenience, not a guarantee: inspect staged paths and content before committing. Do not force-add runtime files. GitHub Pages deploys only the static research catalog.

Report issues with synthetic inputs and redacted diagnostics. Never post a real model key, AppSecret, access token, cookie, private manuscript, or runtime archive. If a credential is disclosed, revoke it through its provider; deleting a visible file does not remove copies from Git history.
