# This file is part of the Linux Process Explorer
# See www.sourceforge.net/projects/procexp
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA


#startup script for process explorer
PREFIX=$(pwd)
export PATH=$PREFIX/bin:$PREFIX/qt-453/bin:$PATH
export LD_LIBRARY_PATH=$PREFIX/lib:$PREFIX/qt-453/lib:$LD_LIBRARY_PATH
export QTDIR=$PREFIX/qt-453
export QTLIB=$PREFIX/qt-453/lib
export QTINC=$PREFIX/qt-453/include
$PREFIX/bin/python $PREFIX/procexp.py
