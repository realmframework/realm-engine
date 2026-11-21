"""Cross-platform native OS folder picker with UTF-8 safety, TopMost owner, and clean cancel."""

import os
import re
import subprocess
import sys
from pathlib import Path


def pick_native_folder(prompt: str = "Choose a folder") -> Path | None:
    """Open the native macOS/Windows/Linux folder picker without script interpolation."""
    safe = re.sub(r"[\r\n\x00]+", " ", prompt).strip() or "Choose a folder"
    try:
        if sys.platform == "darwin":
            cmd = [
                "osascript",
                "-e", "on run argv",
                "-e", "tell current application to activate",
                "-e", "POSIX path of (choose folder with prompt (item 1 of argv))",
                "-e", "end run",
                "--", safe,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, check=False)
            return Path(proc.stdout.strip()) if proc.returncode == 0 and proc.stdout.strip() else None
        if sys.platform == "win32":
            ps = (
                "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$owner=New-Object System.Windows.Forms.Form;$owner.TopMost=$true;$owner.StartPosition='CenterScreen';"
                "$d=New-Object System.Windows.Forms.FolderBrowserDialog;"
                "$d.Description=$env:REALM_PICKER_PROMPT;$d.UseDescriptionForTitle=$true;"
                "if($d.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK){Write-Output $d.SelectedPath};"
                "$owner.Dispose()"
            )
            flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-STA", "-Command", ps],
                env={**os.environ, "REALM_PICKER_PROMPT": safe},
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, creationflags=flags, check=False,
            )
            return Path(proc.stdout.strip()) if proc.returncode == 0 and proc.stdout.strip() else None
        for cmd in (
            ["zenity", "--file-selection", "--directory", f"--title={safe}"],
            ["kdialog", "--getexistingdirectory", str(Path.home()), "--title", safe],
        ):
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, check=False)
                return Path(proc.stdout.strip()) if proc.returncode == 0 and proc.stdout.strip() else None
            except FileNotFoundError:
                continue
    except (OSError, subprocess.SubprocessError):
        return None
    return None
