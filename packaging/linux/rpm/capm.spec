Name: capm
Version: 1.3.2
Release: 1%{?dist}
Summary: CAPM 民航旅客运输量预测系统
License: GPLv3
URL: https://github.com/wb2951516-collab/civil-aviation-prediction
BuildArch: x86_64

Requires: glibc

%description
CAPM 民航旅客运输量预测系统

%prep

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/capm
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications

install -m 0755 %{_sourcedir}/capm %{buildroot}/opt/capm/capm
install -m 0755 %{_sourcedir}/capm %{buildroot}/usr/bin/capm
install -m 0644 %{_sourcedir}/capm.desktop %{buildroot}/usr/share/applications/capm.desktop

%files
/opt/capm/capm
/usr/bin/capm
/usr/share/applications/capm.desktop

%changelog
