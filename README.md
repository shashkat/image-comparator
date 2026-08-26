# image-comparator
Compare sets of images side by side with keyboard navigation.

### Getting started

- Clone the repo and enter directory
	```sh
	git clone https://github.com/shashkat/image-comparator.git
	cd image-comparator
	```
- Create new conda env
	```sh
	conda create -n ic python=3.12
	conda activate ic
	```
- Install using pip
	```sh
	pip install .
	```
- run image-comparator
	```sh
	image-comparator
	```

### Integrating new changes
- Make the desired changes to the code.
- Test the changes locally by running `python app.py` in the appropriate env.
- If satisfied, commit and push to github.
- Then, decide if you want the changes to be reflected in the standalone MacOS application too right now?
	- If no, then nothing else needs to be done.
	- If yes, then do the following:
		- Reinstall image-comparator in development mode using pip in appropriate env (either existing one, previously used for this purpose, or a new one): `pip install -e .`
		- install pyinstaller if not already installed: `pip install pyinstaller`
		- Run pyinstaller to bundle the code into a .app file. This creates the distribution in a folder called `dist`. Note that you might need to modify the dependencies if changes required new dependencies.
			```sh
			pyinstaller \
				--name ImageComparator \
				--windowed \
				--onedir \
				--clean \
				--noconfirm \
				--collect-all matplotlib \
				--collect-all PIL \
				--collect-all reportlab \
				--hidden-import=tkinter \
				--hidden-import=matplotlib.backends.backend_tkagg \
				src/image_comparator/app.py
			```
		- Now run the following 
			``` sh
			codesign --deep --force --options runtime --sign "Apple Development: apple_email (developer_team_id)" /path/to/image-comparator/dist/ImageComparator.app

			ditto -c -k --sequesterRsrc --keepParent /path/to/image-comparator/dist/ImageComparator.app /path/to/image-comparator/dist/ImageComparator.zip

			# this requires having a paid apple developer progam id. Without this, the end user will have to go to settings and allow MacOS to open the file
			# xcrun notarytool submit /path/to/image-comparator/dist/ImageComparator.zip --apple-id "apple_email" --team-id "developer_team_id" --wait
			```
