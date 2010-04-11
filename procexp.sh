#startup script for process explorer
PREFIX=$(pwd)
export PATH=$PREFIX/bin:$PREFIX/qt-453/bin:$PATH
export LD_LIBRARY_PATH=$PREFIX/lib:$PREFIX/qt-453/lib:$LD_LIBRARY_PATH
export QTDIR=$PREFIX/qt-453
export QTLIB=$PREFIX/qt-453/lib
export QTINC=$PREFIX/qt-453/include
$PREFIX/bin/python $PREFIX/procexp.py
