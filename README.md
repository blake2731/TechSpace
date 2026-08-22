# DeskPilot

DeskPilot is a local Windows continuity and file attention assistant. It is designed to help you resume work quickly, notice files that deserve attention, and clean folders safely without becoming another bloated system utility suite.

## What makes it different

PowerToys already handles launchers, previews, renaming, window layouts, clipboard tools, and many other Windows power features. Everything is already excellent at indexed filename search. DeskPilot focuses instead on continuity and file hygiene.

## Features

* Today View shows the files you touched recently in the selected folder so you can quickly reconstruct what you were working on.
* Handoff Notes let you leave a local note for each folder or project describing what you were doing and what should happen next.
* Attention Queue surfaces files worth reviewing, including abandoned partial downloads, empty files, aging installers and archives, old screenshots, and cold files over 1 GB.
* Smart Organize previews files by category before moving anything.
* Undo Last Organize restores the most recent organize operation.
* Duplicate Finder hashes files and groups exact duplicates.
* Storage Review identifies large stale files worth reviewing.
* Quick Search recursively searches filenames inside a chosen folder.
* Workspaces saves frequently used folders and lets you switch DeskPilot directly into one.
* Local only. No cloud service, account, telemetry, or paid API.

## Safety model

DeskPilot does not automatically delete files. Attention Queue is review only. Smart Organize requires a preview and confirmation before moving files, and every organize operation writes an undo record under `%LOCALAPPDATA%\DeskPilot`.

## Run on Windows

Install Python 3.11 or newer if needed, then double click `run_deskpilot.bat`.

## Tests

The core behavior is covered by tests for categorization, safe organize previews, exact duplicate detection, filename search, recent activity ordering, attention detection, and folder summaries.
