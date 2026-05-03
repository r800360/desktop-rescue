from pathlib import Path
from desktop_rescue.rules import category_for

def test_shortcut():
    assert category_for(Path("Visual Studio Code.lnk")) == "01_Shortcuts"

def test_archive():
    assert category_for(Path("hw4_fin.tar")) == "05_Archives_Zips_Tars"

def test_school_pdf():
    assert category_for(Path("CSE_251U_Homework_1.pdf")) == "03_School"

def test_image():
    assert category_for(Path("image.png")) == "06_Images_Media"
