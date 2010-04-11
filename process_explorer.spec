Summary: %{_projectname}
Name: %{_projectname}
Version: %{_versionprefix} 
Release: %_svnversion
Vendor: Carl Wolff
License: GPL
Group: System Environment/Libraries
BuildRoot: %{_builddir}
Packager: Carl.Wolff


#Requires: GAIUS_prerequisites >= 2.0

#No automatic dependency stuff
Autoprov: 0
Autoreq: 0

#No automatic bytecompile and packaging stuff
%define __os_install_post %{nil}

%description
This package contains a process explorer.

###############################################################################
%prep
#No preparation needed to create this RPM


###############################################################################
%build
#No build needed to create this RPM

###############################################################################
%install
# Copy all relevant files
if [[ ! -d $RPM_BUILD_ROOT ]]; then
  mkdir $RPM_BUILD_ROOT
fi
if [[ ! -d $RPM_BUILD_ROOT/opt ]]; then
  mkdir $RPM_BUILD_ROOT/opt
fi
if [[ ! -d $RPM_BUILD_ROOT/opt/%{_projectname}-%{version}-%{release} ]]; then
  mkdir $RPM_BUILD_ROOT/opt/%{_projectname}-%{version}-%{release}
fi

#delete old RPM files, if exist
rm -f ../../*.rpm

#unpack prerequisites for the process explorer
curdir=`pwd`
cd ../..
tar -xf localsmall.tar.gz
cd $curdir

for file in ../../* ; do
  if [ "$file" != "../../rpm" ] && [ "$file" != "../../localsmall.tar.gz" ] && [ "$file" != "../../make_rpm.py" ] && [ "$file" != "../../process_explorer.spec" ] ; then 
    cp -a $file $RPM_BUILD_ROOT/opt/%{_projectname}-%{version}-%{release}
    echo $file
    echo "-----"
  fi
done

rm -rf ../../bin
rm -rf ../../lib
rm -rf ../../qt-453


###############################################################################
%clean
#No clean after creating this RPM

###############################################################################
%files
/opt/%{_projectname}-%{version}-%{release}

###############################################################################
%pre
# Executed before installation on target, nothing to prepare before installing


###############################################################################
%post

#install startup script

cat > /opt/%{_projectname}-%{version}-%{release}/processexplorer.sh << __EOF
#startup script for process explorer
PREFIX=/opt/%{_projectname}-%{version}-%{release}
export PATH=\$PREFIX/bin:\$PREFIX/qt-453/bin:\$PATH
export LD_LIBRARY_PATH=\$PREFIX/lib:\$PREFIX/qt-453/lib:\$LD_LIBRARY_PATH
export QTDIR=\$PREFIX/qt-453
export QTLIB=\$PREFIX/qt-453/lib
export QTINC=\$PREFIX/qt-453/include
\$PREFIX/bin/python /opt/%{_projectname}-%{version}-%{release}/procexp.py
__EOF

chmod +x /opt/%{_projectname}-%{version}-%{release}/processexplorer.sh
ln -s /opt/%{_projectname}-%{version}-%{release}/processexplorer.sh /usr/bin/procexp

###############################################################################
%postun
#No actions needed after the RPM is uninstalled from the target system
rm -rf /opt/%{_projectname}-%{version}-%{release}
rm -f /usr/bin/procexp
