Running
==========
Usage ./VideoPipeline.py config.yaml video.file

Model Directory Requirement
===========================
Models must be placed in the CWD for VideoPipeline with the following structure:
Eg. for washingDishing version 42 and 73, we expect to see the following files:

structSVM-data/datasets/washingDishes
structSVM-data/datasets/washingDishes/models
structSVM-data/datasets/washingDishes/models/classes.txt.codebook.0
structSVM-data/datasets/washingDishes/models/modelGraph.svg
structSVM-data/datasets/washingDishes/models/classes.txt.codebook.5
structSVM-data/datasets/washingDishes/models/train.txt
structSVM-data/datasets/washingDishes/models/svm_params.txt
structSVM-data/datasets/washingDishes/models/classes.txt
structSVM-data/datasets/washingDishes/models/classes.txt.codebook.10
structSVM-data/datasets/washingDishes/models/model.txt
structSVM-data/datasets/washingDishes/models/modelGraph.m
structSVM-data/datasets/washingDishes/models/test.results.txt
structSVM-data/datasets/washingDishes/models/test.txt
structSVM-data/datasets/washingDishes.42
structSVM-data/datasets/washingDishes.42/models
structSVM-data/datasets/washingDishes.42/models/classes.txt.codebook.0
structSVM-data/datasets/washingDishes.42/models/modelGraph.svg
structSVM-data/datasets/washingDishes.42/models/classes.txt.codebook.5
structSVM-data/datasets/washingDishes.42/models/train.txt
structSVM-data/datasets/washingDishes.42/models/svm_params.txt
structSVM-data/datasets/washingDishes.42/models/classes.txt
structSVM-data/datasets/washingDishes.42/models/classes.txt.codebook.10
structSVM-data/datasets/washingDishes.42/models/model.txt
structSVM-data/datasets/washingDishes.42/models/modelGraph.m
structSVM-data/datasets/washingDishes.42/models/test.results.txt
structSVM-data/datasets/washingDishes.42/models/test.txt
structSVM-data/datasets/washingDishes.73
structSVM-data/datasets/washingDishes.73/models
structSVM-data/datasets/washingDishes.73/models/classes.txt.codebook.0
structSVM-data/datasets/washingDishes.73/models/modelGraph.svg
structSVM-data/datasets/washingDishes.73/models/classes.txt.codebook.5
structSVM-data/datasets/washingDishes.73/models/train.txt
structSVM-data/datasets/washingDishes.73/models/svm_params.txt
structSVM-data/datasets/washingDishes.73/models/classes.txt
structSVM-data/datasets/washingDishes.73/models/classes.txt.codebook.10
structSVM-data/datasets/washingDishes.73/models/model.txt
structSVM-data/datasets/washingDishes.73/models/modelGraph.m
structSVM-data/datasets/washingDishes.73/models/test.results.txt
structSVM-data/datasets/washingDishes.73/models/test.txt

Config
======
config.yaml contains the plugins and the models that will be executed
Each ModelDetection config is listed as such

    ModelDetection0:
        defaultOrder     : 6
        threshold        : 0.6
        stronger         : 0.2
        weaker           : -0.2
        modelName        : "skiingBoarding"
        modelVersion     : 59

ModelDetection[0-1000] are checked

Plugins
=======
FrameExtraction, BlankDetection, SelectingSingleFrame, RemoveMultiModels, ModelDetection are run

Results
=======
Results are stored in <videoDir>/results/<PluginName>.json
Eg. BlankDetection.json, ModelDetection:washingDishes:73.json, ModelDetection:washingDishes:42.json, etc

Result Format for each Plugin File:
"FrameId": { "Score": "Value", "State": "Value" }, "FrameId1": { ... }, ....

Frames generated
================
Generated frames are in ppm format and are stored at <videoDir>/frames/<frame_id>/original.ppm
When features are extracted they are placed alongside the frame img with the .feat.bin extension


Libraries Required
==================
libzsvm.so from ImageClassifier.cpp
