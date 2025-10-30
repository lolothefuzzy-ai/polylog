Archive index
===============

This file lists the archived zip files and how to restore them.

Files created:

- `archive/backups.zip` — compressed archive of `archive/backups` (previously contained repository backup files). See `archive/backups_contents.txt` for the listing before zipping.
- `archive/legacy.zip` — compressed archive of `archive/legacy` (previously contained large legacy archives like ALLDOCS/_archive_legacy_code and _archive_legacy_docs and other caches). See `archive/legacy_contents.txt` for the listing before zipping.

How to restore:

1. To inspect contents without extracting:

```powershell
# list zip contents
Expand-Archive -Path archive\backups.zip -DestinationPath tmp_backups -WhatIf
# or use 7zip/list command-line if installed
```

2. To restore fully (be careful; this will overwrite existing files with the same names):

```powershell
Expand-Archive -Path archive\backups.zip -DestinationPath . -Force
Expand-Archive -Path archive\legacy.zip -DestinationPath . -Force
```

Notes:
- I preserved `archive/backups_contents.txt` and `archive/legacy_contents.txt` files which list what was archived prior to compression.
- If you prefer I can move the zip files to an external drive or cloud storage; tell me where and I will prepare an upload script.
