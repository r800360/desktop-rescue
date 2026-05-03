# Desktop Rescue

Desktop Rescue is a safe Windows Desktop organizer for people whose Desktop became a junk drawer.

It scans your Desktop, classifies items into useful categories, moves files and folders into a clean `_Desktop_Rescue` workspace, creates reports, keeps a manifest, and supports undo.

The app is intentionally conservative:

- Dry-run by default
- Never permanently deletes files
- Keeps shortcuts separate
- Skips system-protected Desktop items
- Creates timestamped reports
- Creates an undo manifest for every real run
- Can preserve "active" recent items on the Desktop
- Can be scheduled to run daily or weekly

## What it creates

After a real run, your Desktop will contain a folder like:

```text
_Desktop_Rescue/
  00_INBOX_Recent/
  01_Shortcuts/
  02_PDFs/
  03_School/
  04_Projects_Code/
  05_Archives_Zips_Tars/
  06_Images_Media/
  07_Notebooks_Data/
  08_Installers_Config/
  09_Apps_Tools/
  90_Old_Folders/
  99_Unsorted/
  _reports/
```

## Quick start

From PowerShell:

```powershell
cd C:\Users\bsach\Documents
mkdir desktop-rescue
cd desktop-rescue

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

Copy this project into that folder, then install it:

```powershell
pip install -e .
```

Preview what would happen:

```powershell
desktop-rescue plan --desktop "$env:USERPROFILE\Desktop"
```

Run for real:

```powershell
desktop-rescue run --desktop "$env:USERPROFILE\Desktop"
```

Undo the most recent run:

```powershell
desktop-rescue undo --desktop "$env:USERPROFILE\Desktop"
```

## Recommended first run for Rohan's current Desktop

Use this first:

```powershell
desktop-rescue plan --desktop "$env:USERPROFILE\Desktop" --recent-days 14
```

Then inspect:

```powershell
notepad "$env:USERPROFILE\Desktop\_Desktop_Rescue\_reports\latest_plan.txt"
```

Then run:

```powershell
desktop-rescue run --desktop "$env:USERPROFILE\Desktop" --recent-days 14
```

## Scheduling

After you trust the app, create a scheduled task that runs every night at 9:15 PM:

```powershell
$Project = "C:\Users\bsach\Documents\desktop-rescue"
$Python = "$Project\.venv\Scripts\python.exe"
$Action = New-ScheduledTaskAction -Execute $Python -Argument "-m desktop_rescue.cli run --desktop `"$env:USERPROFILE\Desktop`" --recent-days 7"
$Trigger = New-ScheduledTaskTrigger -Daily -At 9:15PM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "Desktop Rescue" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Organize Desktop safely with undo manifest"
```

## Commands

```powershell
desktop-rescue plan
desktop-rescue run
desktop-rescue undo
desktop-rescue status
```

## Safety model

Desktop Rescue avoids destructive cleanup. It only moves items into categorized folders. It does not delete anything.

A real run writes a manifest like:

```text
_Desktop_Rescue/_reports/manifest_2026-05-02_210000.json
```

Undo uses that manifest to move files back to their original paths.

## Customizing categories

Edit `src/desktop_rescue/rules.py`.

Important ideas:

- `.lnk` files go to `01_Shortcuts`
- PDFs and documents go to `02_PDFs`
- course/homework/project-looking names go to `03_School`
- source/project folders go to `04_Projects_Code`
- `.zip`, `.tar`, `.gz` go to `05_Archives_Zips_Tars`
- images and media go to `06_Images_Media`
- notebooks and data files go to `07_Notebooks_Data`
- config/build/install artifacts go to `08_Installers_Config`
- unknown old folders go to `90_Old_Folders`
- unknown items go to `99_Unsorted`

## Philosophy

The Desktop should become a launchpad, not a storage graveyard.

Good Desktop items:

- Shortcuts you actually launch
- A tiny inbox for current work
- A single organized rescue folder
- Nothing else
