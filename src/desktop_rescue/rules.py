from __future__ import annotations

from pathlib import Path

RESCUE_ROOT_NAME = "_Desktop_Rescue"

# Keep these lowercase because core.py compares against path.name.lower()
SKIP_NAMES = {
    RESCUE_ROOT_NAME.lower(),
    "desktop.ini",
    "thumbs.db",
    "$recycle.bin",
}

SHORTCUT_EXTS = {".lnk", ".url"}
PDF_DOC_EXTS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".md", ".html", ".htm"}
ARCHIVE_EXTS = {".zip", ".tar", ".gz", ".tgz", ".7z", ".rar"}
IMAGE_MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov", ".avi", ".mkv"}
NOTEBOOK_DATA_EXTS = {".ipynb", ".csv", ".json", ".h5", ".hdf5", ".pkl", ".npy", ".npz"}
INSTALL_CONFIG_EXTS = {".qpf", ".qsf", ".hex", ".jar", ".exe", ".msi"}

SCHOOL_KEYWORDS = {
    "cse", "ece", "math", "hw", "homework", "assignment", "pa", "quiz",
    "final", "midterm", "lecture", "notes", "report", "submission",
    "sachdeva", "rohan", "dmp", "resume", "cv", "aisc", "tesc"
}

PROJECT_KEYWORDS = {
    "monorepo", "ros", "ros2", "robot", "slam", "tock", "openthread",
    "waver", "libtock", "quadcopter", "website", "sticker", "code",
    "build", "src", "db", "digital", "tech-lab", "splagen", "dft",
    "social-habits"
}

TOOLS_KEYWORDS = {
    "vscode", "visual studio code", "cursor", "pycharm", "arduino", "quartus",
    "postman", "matlab", "git bash", "slack", "discord", "zoom", "edge",
    "chrome", "norton", "vlc", "winscp", "putty", "j-link", "nrf", "fusion",
    "wiztree", "notepad++", "roblox"
}

def normalized_name(path: Path) -> str:
    return path.name.lower().replace("_", " ").replace("-", " ")

def has_any(text: str, words: set[str]) -> bool:
    return any(word in text for word in words)

def category_for(path: Path, is_recent: bool = False) -> str:
    name = normalized_name(path)
    ext = path.suffix.lower()

    if is_recent and path.name.lower() not in SKIP_NAMES:
        return "00_INBOX_Recent"

    if ext in SHORTCUT_EXTS:
        return "01_Shortcuts"

    if has_any(name, TOOLS_KEYWORDS):
        return "09_Apps_Tools"

    if ext in ARCHIVE_EXTS:
        return "05_Archives_Zips_Tars"

    if ext in IMAGE_MEDIA_EXTS:
        return "06_Images_Media"

    if ext in NOTEBOOK_DATA_EXTS:
        return "07_Notebooks_Data"

    if ext in INSTALL_CONFIG_EXTS:
        return "08_Installers_Config"

    if ext in PDF_DOC_EXTS:
        if has_any(name, SCHOOL_KEYWORDS):
            return "03_School"
        return "02_PDFs"

    if path.is_dir():
        if has_any(name, PROJECT_KEYWORDS):
            return "04_Projects_Code"
        if has_any(name, SCHOOL_KEYWORDS):
            return "03_School"
        if name in {"build", "install", "log", "temp", "db"}:
            return "08_Installers_Config"
        return "90_Old_Folders"

    return "99_Unsorted"