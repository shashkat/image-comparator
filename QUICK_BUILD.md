# Quick Build Reference

## TL;DR - Fastest Way to Build

### macOS/Linux:
```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Build
pyinstaller --windowed --name="ImageComparator" image_comparator_gui.py

# 3. Find your app
cd dist/ImageComparator
```

### Windows:
```cmd
REM 1. Install PyInstaller
pip install pyinstaller

REM 2. Build
pyinstaller --windowed --name="ImageComparator" image_comparator_gui.py

REM 3. Find your app
cd dist\ImageComparator
```

---

## Using the Build Scripts

### Automated Build (Recommended)

**macOS/Linux:**
```bash
chmod +x build.sh
./build.sh
```

**Windows:**
```cmd
build.bat
```

The scripts will:
- Check dependencies
- Clean old builds
- Ask which type of build you want
- Build the executable
- Show statistics

---

## Manual Commands

### Directory Bundle (Recommended)
**Fast startup, distribute as folder**

```bash
pyinstaller --windowed --name="ImageComparator" image_comparator_gui.py
```

**Output**: `dist/ImageComparator/` folder
**Distribute**: Zip the entire folder


### Single File
**Slow startup, single file distribution**

```bash
pyinstaller --onefile --windowed --name="ImageComparator" image_comparator_gui.py
```

**Output**: `dist/ImageComparator` (or `.exe` on Windows)
**Distribute**: Just the one file


### macOS .app Bundle
**Native macOS application**

```bash
pyinstaller --windowed --name="ImageComparator" \
    --osx-bundle-identifier=com.imagecomparator.app \
    image_comparator_gui.py
```

**Output**: `dist/ImageComparator.app`
**Distribute**: The .app file (can drag to Applications)

---

## File Sizes

Typical sizes:
- **Directory bundle**: 200-300 MB
- **Single file**: 250-400 MB (larger due to compression overhead)
- **With optimization**: 100-200 MB

---

## Common Issues

### Issue: "pyinstaller: command not found"
**Fix**: `pip install pyinstaller`

### Issue: "Module not found" when running built app
**Fix**: Add hidden imports:
```bash
pyinstaller --windowed --name="ImageComparator" \
    --hidden-import=PIL._tkinter_finder \
    --hidden-import=reportlab.pdfgen.canvas \
    image_comparator_gui.py
```

### Issue: App too large
**Fix**: Create minimal environment:
```bash
python -m venv minimal
source minimal/bin/activate
pip install matplotlib pillow pdf2image numpy reportlab
pyinstaller --windowed --name="ImageComparator" image_comparator_gui.py
```

---

## Distribution Checklist

Before sharing:
- ✅ Test on your machine
- ✅ Test on clean machine without Python
- ✅ Test all features work
- ✅ Include README for users
- ✅ Note poppler requirement for PDFs

---

## User Instructions

When distributing, tell users:

**For PDF support, they need poppler:**
- **macOS**: `brew install poppler`
- **Linux**: `sudo apt-get install poppler-utils`
- **Windows**: Download from https://github.com/oschwartz10612/poppler-windows/releases

**To run:**
- **Directory bundle**: Open folder, double-click `ImageComparator`
- **Single file**: Double-click `ImageComparator` or `ImageComparator.exe`
- **macOS .app**: Drag to Applications, then open

---

## Advanced: Smaller Builds

### Exclude unused packages
```bash
pyinstaller --windowed --name="ImageComparator" \
    --exclude-module=pytest \
    --exclude-module=scipy \
    --exclude-module=pandas \
    image_comparator_gui.py
```

### Use UPX compression
```bash
# Install UPX first (macOS: brew install upx)
pyinstaller --windowed --name="ImageComparator" --upx-dir=/usr/local/bin \
    image_comparator_gui.py
```

---

## Platform-Specific Notes

### macOS
- Built on macOS works on macOS only
- For distribution outside App Store, users may need to right-click → Open first time
- Consider code signing for better user experience

### Windows
- Built on Windows works on Windows only
- Antivirus may flag executable (false positive)
- Consider code signing for trust

### Linux
- Built on specific Linux works on similar Linux systems
- May need to build on oldest supported OS for compatibility
- AppImage format is another option for Linux

---

## Need Help?

See full guide: `PACKAGING_GUIDE.md`
