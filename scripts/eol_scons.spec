%define __python /usr/bin/python3

Name: eol_scons
Version: 4.2.5
Release: %{releasenum}%{?dist}
Summary: EOL SCons tools
License: MIT
Group: System Environment/Daemons
URL: https://github.com/NCAR/eol_scons
Vendor: UCAR
BuildArch: noarch

Requires: scons-python3
BuildRequires: python3-devel scons-python3
Source: %{name}-%{version}.tar.gz

%description
Tools and extensions to SCons to build NCAR/EOL software.

%prep
%setup

%build

%install
rm -rf $RPM_BUILD_ROOT
scons --install-sandbox %{buildroot} PREFIX=/usr/share/scons/site_scons install

%files
/usr/share/scons/site_scons/eol_scons

%changelog
* Thu Dec 14 2023 Gary Granger <granger@ucar.edu> - 4.2.5-1
- build v4.2.5

* Sat Sep 02 2023 Gary Granger <granger@ucar.edu> - 4.2.4-1
- build v4.2.4

* Thu Dec 15 2022 Gary Granger <granger@ucar.edu> - 4.2.3-1
- build 4.2.3

* Sat Dec 10 2022 Gary Granger <granger@ucar.edu> - 4.2.2-1
- build v4.2.2

* Tue Aug 30 2022 Gary Granger <granger@ucar.edu> - 4.2.1-1
- build v4.2.1

* Sat Aug 27 2022 Gary Granger <granger@ucar.edu> - 4.2-1
- build v4.2

* Fri Aug 26 2022 Gary Granger <granger@ucar.edu> - 4.2~alpha2-1
- build v4.2-alpha2

