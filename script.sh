rm -rf tmp

sudo apt-get install zip unzip
zip -r io_mesh_w3d.zip io_mesh_w3d
mkdir tmp && cd tmp
wget https://ftp.halifax.rwth-aachen.de/blender/release/Blender2.81/blender-2.81-linux-glibc217-x86_64.tar.bz2
tar jxf blender-2.81-linux-glibc217-x86_64.tar.bz2
mv blender-2.81-linux-glibc217-x86_64 blender
rm blender-2.81-linux-glibc217-x86_64.tar.bz2
cd blender
./blender --factory-startup -noaudio -b --python-exit-code 1 --python ../../ci_install.py
