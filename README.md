Installing
==========
- make all  -  setup and run tests
- make test -  only test
- make setup - only setup
- make VideoReader - setup VideoReader

Binaries
==========
- Binaries are registered which you can call from the prompt:
- $> processvideo config.yaml videoFileName baseDbFolder jsonFolder
- $> postprocess config.yaml jsonFolder
- $> generatecellmap config.yaml frame.width frame.height
- $> modelperformance csv_folder score_threshold count_threshold class_mapping output_folder [ patchImageFolder ]

Model Directory Requirement
===========================
Model files are separately trained in https://github.com/zigvu/chia


Config
======
Sample config.yaml at tests/config.yaml
