CPP_DIR = VideoReader

.PHONY: VideoReader

all: setup test

VideoReader:
	$(MAKE) -C $(CPP_DIR)

setup:
	mkdir -p ~/site-packages/
	export PYTHONPATH=$$PYTHONPATH:~/site-packages/
	python setup.py develop --install-dir=~/site-packages/

test:
	py.test

