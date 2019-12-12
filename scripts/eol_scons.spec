%define name eol_scons

Summary: EOL SCons tools
Name: %{name}
Version: %{version}
Release: %{release}
License: GPL
Group: System Environment/Daemons
Url: http://www.eol.ucar.edu/
Packager: Gordon Maclean <maclean@ucar.edu>
Vendor: UCAR
BuildArch: noarch

%if 0%{?rhel} < 8
Requires: scons
BuildRequires: python-devel
%else
Requires: python3-scons
BuildRequires: python36-devel
%endif

Source: %{name}-%{version}.tar.gz

%description
EOL SCons tools

%prep
%setup -n eol_scons

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/usr/share/scons/site_scons/eol_scons
cp -r . $RPM_BUILD_ROOT/usr/share/scons/site_scons/eol_scons

%clean
rm -rf $RPM_BUILD_ROOT

%files
/usr/share/scons/site_scons/eol_scons

%changelog
