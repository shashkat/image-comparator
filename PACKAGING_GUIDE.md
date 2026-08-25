# Packaging Guide: Creating Standalone Executable

This guide shows you how to package the Image Grid Comparator into a standalone application that can run on other computers without requiring Python or dependencies to be installed.

## Table of Contents
1. [PyInstaller (Recommended)](#pyinstaller-recommended)
2. [py2app (macOS Only)](#py2app-macos-only)
3. [Nuitka (Advanced)](#nuitka-advanced)
4. [Comparison Table](#comparison-table)

---

## PyInstaller (Recommended)

**Best for**: Cross-platform distribution, easiest to use

### Installation

```bash
pip install pyinstaller
```

### Basic Usage

#### Option 1: Simple Single File (Slower startup)
```bash
pyinstaller --onefile --windowed --name="ImageComparator" image_comparator_gui.py
```

#### Option 2: Directory Bundle (Faster startup, RECOMMENDED)
```bash
pyinstaller --windowed --name="ImageComparator" image_comparator_gui.py
```

#### Option 3: With Custom Icon (macOS/Windows)
```bash
# macOS (.icns file)
pyinstaller --onefile --windowed --name="ImageComparator" \
    --icon=app_icon.icns image_comparator_gui.py

# Windows (.ico file)
pyinstaller --onefile --windowed --name="ImageComparator" \
    --icon=app_icon.ico image_comparator_gui.py
```

### Advanced PyInstaller Configuration

Create a file called `image_comparator.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['image_comparator_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PIL._tkinter_finder',
        'reportlab.pdfgen.canvas',
        'reportlab.lib.pagesizes',
        'pdf2image',
        'matplotlib.backends.backend_tkagg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ImageComparator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.icns',  # Optional: add your icon
)

# macOS: Create .app bundle
app = BUNDLE(
    exe,
    name='ImageComparator.app',
    icon='app_icon.icns',
    bundle_identifier='com.yourname.imagecomparator',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',
    },
)
```

Then build with:
```bash
pyinstaller image_comparator.spec
```

### Output Location

- **Single file mode**: `dist/ImageComparator` (or `.exe` on Windows)
- **Directory mode**: `dist/ImageComparator/` folder
- **macOS bundle**: `dist/ImageComparator.app`

### Common PyInstaller Issues & Solutions

#### Issue: "Module not found" errors
**Solution**: Add to `hiddenimports` in spec file:
```python
hiddenimports=[
    'PIL._tkinter_finder',
    'reportlab.pdfgen.canvas',
    'pdf2image',
    # Add any other missing modules here
],
```

#### Issue: App is too large (500MB+)
**Solution 1**: Use `--exclude-module` to remove unused packages:
```bash
pyinstaller --onefile --windowed \
    --exclude-module pytest \
    --exclude-module IPython \
    --exclude-module jupyter \
    image_comparator_gui.py
```

**Solution 2**: Create a minimal virtual environment:
```bash
python -m venv minimal_env
source minimal_env/bin/activate  # On Windows: minimal_env\Scripts\activate
pip install matplotlib pillow pdf2image numpy reportlab
pyinstaller --onefile --windowed image_comparator_gui.py
```

#### Issue: "poppler" not found for PDF support
**Solution**: 
- **macOS**: `brew install poppler`
- **Linux**: `sudo apt-get install poppler-utils`
- **Windows**: Download poppler, add to PATH, or include binaries:
```bash
pyinstaller --onefile --windowed \
    --add-binary "C:/path/to/poppler/bin;." \
    image_comparator_gui.py
```

---

## py2app (macOS Only)

**Best for**: Native macOS .app bundles with better integration

### Installation

```bash
pip install py2app
```

### Setup

Create `setup.py`:

```python
from setuptools import setup

APP = ['image_comparator_gui.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'matplotlib',
        'PIL',
        'pdf2image',
        'numpy',
        'reportlab',
        'tkinter',
    ],
    'includes': [
        'matplotlib.backends.backend_tkagg',
        'PIL._tkinter_finder',
    ],
    'excludes': [
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
    ],
    'iconfile': 'app_icon.icns',  # Optional
    'plist': {
        'CFBundleName': 'Image Comparator',
        'CFBundleDisplayName': 'Image Comparator',
        'CFBundleIdentifier': 'com.yourname.imagecomparator',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

### Build

```bash
# Development mode (faster, for testing)
python setup.py py2app -A

# Production mode (standalone)
python setup.py py2app
```

### Output

- Location: `dist/Image Comparator.app`
- Double-click to run like any macOS app
- Can drag to Applications folder

---

## Nuitka (Advanced)

**Best for**: Smaller file sizes, better performance, true compilation to C

### Installation

```bash
pip install nuitka
```

### Basic Build

```bash
python -m nuitka --standalone --onefile --enable-plugin=tk-inter \
    --enable-plugin=numpy --enable-plugin=matplotlib \
    --macos-create-app-bundle --macos-app-name="ImageComparator" \
    image_comparator_gui.py
```

### Pros & Cons

**Pros**:
- Smaller executables than PyInstaller
- Better performance (compiled to C)
- True compilation, not just packaging

**Cons**:
- Longer compilation time
- More complex troubleshooting
- Requires C compiler installed

---

## Comparison Table

| Feature | PyInstaller | py2app | Nuitka |
|---------|-------------|---------|--------|
| **Platforms** | Windows, macOS, Linux | macOS only | All platforms |
| **Ease of Use** | ⭐⭐⭐⭐⭐ Easy | ⭐⭐⭐⭐ Easy | ⭐⭐⭐ Moderate |
| **Build Speed** | ⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐ Fast | ⭐⭐ Slow |
| **File Size** | ~200-400MB | ~200-300MB | ~100-200MB |
| **Startup Speed** | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent |
| **Native Look** | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Native | ⭐⭐⭐⭐ Good |
| **Recommended For** | Most users | macOS distribution | Advanced users |

---

## Step-by-Step: Building with PyInstaller (Recommended)

### 1. Prepare Environment

```bash
# Create fresh virtual environment
python -m venv build_env
source build_env/bin/activate  # Windows: build_env\Scripts\activate

# Install dependencies
pip install matplotlib pillow pdf2image numpy reportlab pyinstaller

# Install system dependencies (macOS)
brew install poppler
```

### 2. Test Your Script

```bash
python image_comparator_gui.py
```

Make sure it works perfectly before building.

### 3. Build Executable

```bash
pyinstaller --windowed --name="ImageComparator" image_comparator_gui.py
```

### 4. Test the Executable

```bash
# Navigate to dist folder
cd dist/ImageComparator

# Run the app
./ImageComparator  # macOS/Linux
# or
ImageComparator.exe  # Windows
```

### 5. Distribute

**For Directory Bundle:**
- Zip the entire `dist/ImageComparator` folder
- Recipient extracts and runs the executable inside

**For Single File:**
- Just distribute the single executable file
- Slower startup but easier distribution

**For macOS .app:**
- Distribute `ImageComparator.app`
- Can be code-signed for macOS Gatekeeper

---

## Distribution Checklist

Before distributing your application:

- [ ] Test on a clean machine without Python installed
- [ ] Test all features (file selection, sync, viewing)
- [ ] Test with PDF and image files
- [ ] Check file size is reasonable (<500MB)
- [ ] Include README or instructions
- [ ] Consider code signing (macOS/Windows) for trust
- [ ] Test on target OS versions

---

## Reducing File Size

### Technique 1: Exclude Unused Packages

```bash
pyinstaller --onefile --windowed \
    --exclude-module pytest \
    --exclude-module IPython \
    --exclude-module scipy \
    --exclude-module pandas \
    image_comparator_gui.py
```

### Technique 2: Use UPX Compression

```bash
# Install UPX first
# macOS: brew install upx
# Linux: sudo apt-get install upx

pyinstaller --onefile --windowed --upx-dir=/usr/local/bin \
    image_comparator_gui.py
```

### Technique 3: Minimal Virtual Environment

```bash
python -m venv minimal
source minimal/bin/activate
pip install --no-cache-dir matplotlib pillow pdf2image numpy reportlab
pyinstaller --onefile --windowed image_comparator_gui.py
```

---

## Code Signing (Optional but Recommended)

### macOS

```bash
# After building with PyInstaller
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: Your Name" \
    dist/ImageComparator.app
```

### Windows

Use `signtool.exe` from Windows SDK:
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com \
    dist/ImageComparator.exe
```

---

## Troubleshooting Build Issues

### Problem: tkinter not found

**Solution**: Install system tkinter package:
```bash
# macOS: Usually included with Python
# Linux: sudo apt-get install python3-tk
# Windows: Reinstall Python with tkinter option checked
```

### Problem: Executable crashes on launch

**Solution**: Build with console enabled to see errors:
```bash
pyinstaller --onefile --name="ImageComparator" image_comparator_gui.py
# Note: removed --windowed flag
```

### Problem: "Module not found" in built app

**Solution**: Add to spec file's `hiddenimports` or use `--hidden-import`:
```bash
pyinstaller --onefile --windowed \
    --hidden-import=PIL._tkinter_finder \
    --hidden-import=reportlab.pdfgen.canvas \
    image_comparator_gui.py
```

---

## Recommended Approach

**For most users**: Use **PyInstaller with directory bundle**

```bash
pyinstaller --windowed --name="ImageComparator" image_comparator_gui.py
```

**Why?**
- Works cross-platform
- Fast startup
- Easy to troubleshoot
- Reasonable file size
- Simple distribution

**Then**: Zip the `dist/ImageComparator` folder and share!

---

## Next Steps

1. Choose your build method (recommend PyInstaller)
2. Install required tools
3. Test build locally
4. Test on clean machine
5. Distribute to users

Good luck! 🚀
