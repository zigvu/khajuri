cd ~/khajuri
valgrind --tool=memcheck --leak-check=full --show-reachable=yes ~/khajuri/VideoPipeline.py ~/khajuri/config.yaml ~/3/Timers.mp4  > output.txt 2>&1
