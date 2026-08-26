# image-comparator
Compare sets of images side by side with keyboard navigation.

### Getting started

- Clone the repo
- From repo root, run:
```sh
pyinstaller \
  --name ImageComparator \
  --windowed \
  --onefile \
  --clean \
  --noconfirm \
  --collect-all matplotlib \
  --collect-all PIL \
  --collect-all reportlab \
  --hidden-import=tkinter \
  --hidden-import=matplotlib.backends.backend_tkagg \
  src/image_comparator/app.py
```
- The distribution is now in the dist folder of the repo
