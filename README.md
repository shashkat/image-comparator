# image-comparator
Compare sets of images side by side with keyboard navigation.

### Getting started

- Ensure that pipx is installed. Depending on your platform, run one of the following in terminal:
	- macOS
		```sh
		brew install pipx
		```
	- Windows
		```
		py -m pip install --user pipx
		```
	- Ubuntu/Debian
		```
		sudo apt install pipx
		```

- Install image-comparator using pipx:
	- Try this (this will try to use an already existing python installation):
	```sh
	pipx install image-comparator
	```
	- If above command doesn't work, try this (this will install a standalone python installation automatically, hence may take a few minutes to complete):
	```sh
	pipx install image-comparator --python 3.12 --fetch-python=missing
	```

- Now you can simply use the tool by running:
	```sh
	image-comparator
	```

- If want to uninstall, simply run:
	```
	pipx uninstall image-comparator
	```



