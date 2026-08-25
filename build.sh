#!/bin/bash
# Build script for Image Comparator GUI
# This script automates the process of creating a standalone executable

set -e  # Exit on error

echo "=========================================="
echo "Image Comparator - Build Script"
echo "=========================================="
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "   For best results, create and activate a virtual environment first:"
    echo "   python -m venv build_env"
    echo "   source build_env/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Check if script exists
if [ ! -f "image_comparator_gui.py" ]; then
    echo "❌ Error: image_comparator_gui.py not found in current directory"
    exit 1
fi

echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec

echo ""
echo "Choose build type:"
echo "1) Directory bundle (recommended - faster startup)"
echo "2) Single file (slower startup, easier distribution)"
echo "3) macOS .app bundle (macOS only)"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🔨 Building directory bundle..."
        pyinstaller --windowed \
            --name="ImageComparator" \
            --hidden-import=PIL._tkinter_finder \
            --hidden-import=reportlab.pdfgen.canvas \
            --hidden-import=pdf2image \
            image_comparator_gui.py
        
        echo ""
        echo "✅ Build complete!"
        echo "📁 Location: dist/ImageComparator/"
        echo "📝 To distribute: Zip the entire 'dist/ImageComparator' folder"
        ;;
    
    2)
        echo ""
        echo "🔨 Building single file..."
        pyinstaller --onefile --windowed \
            --name="ImageComparator" \
            --hidden-import=PIL._tkinter_finder \
            --hidden-import=reportlab.pdfgen.canvas \
            --hidden-import=pdf2image \
            image_comparator_gui.py
        
        echo ""
        echo "✅ Build complete!"
        echo "📁 Location: dist/ImageComparator"
        echo "📝 To distribute: Share the single executable file"
        ;;
    
    3)
        if [[ "$OSTYPE" != "darwin"* ]]; then
            echo "❌ Error: macOS .app bundle can only be built on macOS"
            exit 1
        fi
        
        echo ""
        echo "🔨 Building macOS .app bundle..."
        pyinstaller --windowed \
            --name="ImageComparator" \
            --hidden-import=PIL._tkinter_finder \
            --hidden-import=reportlab.pdfgen.canvas \
            --hidden-import=pdf2image \
            --osx-bundle-identifier=com.imagecomparator.app \
            image_comparator_gui.py
        
        echo ""
        echo "✅ Build complete!"
        echo "📁 Location: dist/ImageComparator.app"
        echo "📝 To distribute: Share the .app file (can drag to Applications)"
        ;;
    
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🧪 Testing the build..."
if [ -f "dist/ImageComparator" ]; then
    echo "   Executable found: dist/ImageComparator"
elif [ -d "dist/ImageComparator" ]; then
    echo "   Bundle found: dist/ImageComparator/"
elif [ -d "dist/ImageComparator.app" ]; then
    echo "   macOS app found: dist/ImageComparator.app"
fi

echo ""
echo "📊 Build statistics:"
if [ -d "dist/ImageComparator" ]; then
    du -sh dist/ImageComparator
elif [ -f "dist/ImageComparator" ]; then
    du -sh dist/ImageComparator
elif [ -d "dist/ImageComparator.app" ]; then
    du -sh dist/ImageComparator.app
fi

echo ""
echo "=========================================="
echo "🎉 Build process complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test the executable on your machine"
echo "2. Test on a clean machine without Python"
echo "3. Distribute to users"
echo ""
echo "Note: Users will need poppler installed for PDF support:"
echo "  macOS: brew install poppler"
echo "  Linux: sudo apt-get install poppler-utils"
echo ""
