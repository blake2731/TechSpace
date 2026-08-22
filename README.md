# DeskPilot

DeskPilot is a local Windows desktop utility for finding files fast, cleaning messy folders safely, finding duplicates, spotting large stale files, and launching common workspaces.

## Features

* Smart Organize previews files by category before moving anything.
* Undo Last Organize restores the most recent move operation.
* Duplicate Finder hashes files and groups exact duplicates.
* Large and Stale Files identifies files worth reviewing for storage cleanup.
* Quick Search recursively searches filenames from a chosen folder.
* Workspace Launcher saves frequently used folders and opens them instantly.
* Local only. No cloud service, account, telemetry, or paid API.

## Run on Windows

Install Python 3.11 or newer if needed, then double click `run_deskpilot.bat`.

DeskPilot never deletes files automatically. Smart Organize only moves files after showing a preview. Every organize operation writes an undo record under `%LOCALAPPDATA%\DeskPilot`.