all: setup

setup:
	sudo python setup.py develop

test:
	python -m unittest discover tests '*tests.py'

