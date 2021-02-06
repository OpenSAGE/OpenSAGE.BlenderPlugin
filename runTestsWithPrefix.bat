set /P PREFIX=Please enter prefix of tests to run: 

"C:\Program Files\Blender Foundation\Blender\blender.exe" --factory-startup -noaudio -b --python-exit-code 1 --python ./tests/runner.py -- --prefix %PREFIX%
Pause