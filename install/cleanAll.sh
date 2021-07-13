#!/bin/bash
cd "${0%/*}" || exit 1    # run from this directory
eval "$(conda shell.bash hook)"

conda activate puma

# clean inside install folder
rm -rf cmake-build-release
rm -rf cmake-build-debug
rm $CONDA_PREFIX/bin/puma*
rm $CONDA_PREFIX/lib/libPuMA*
rm $CONDA_PREFIX/lib/libTexGenCore*
rm -rf TexGen/bin
rm -rf miniconda
cd ..

# clean pumapy
python setup.py clean

# clean root
find ../ -name '*~' -ls -delete

# clean initproject
rm -rf cpp/initproject/build

# clean GUI
cd gui/build
rm -f *.o
rm -f pumaGUI
rm -f Makefile
