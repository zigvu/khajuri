#!/bin/bash

echo "Usage: make_all.sh <numOfCores>"

make clean
make protoc

# make all
# if multiple cores supplied, then use them in make
if [ $# -eq 0 ]
	then
		make all
else
	make all "-j$1"
fi
