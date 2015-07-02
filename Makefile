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
	python -m unittest discover tests '*tests.py'

clean:
	echo 'Cleaning .pyc files'
	find . -name '*.pyc' | xargs rm
	echo 'Cleaning install directory ~/site-packages/'
	rm -rf ~/site-packages/
