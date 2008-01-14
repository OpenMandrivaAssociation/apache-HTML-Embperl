%define module HTML-Embperl
%define mod_conf 76_Embperl.conf

Summary:	Embperl is a framework for building web sites with Perl
Name:		apache-%{module}
Version:	2.2.0
Release:	%mkrel 4
License:	GPL
Group:		System/Servers
URL:		http://perl.apache.org/embperl/
Source0:	ftp://ftp.dev.ecos.de/pub/perl/embperl/Embperl-%{version}.tar.bz2
Source1:	%{mod_conf}
Patch0:		Embperl-2.09b-fix-CVS.patch
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= 2.2.0
Requires(pre):	apache >= 2.2.0
Requires:	apache-mod_perl >= 1:2.0.2
BuildRequires:	apache >= 2.2.0
BuildRequires:	apache-devel >= 2.2.0
BuildRequires:	apache-modules >= 2.2.0
BuildRequires:	apache-mod_perl >= 1:2.0.2
BuildRequires:	apache-mod_perl-devel >= 1:2.0.2
BuildRequires:	libxml2-devel
BuildRequires:	libxslt-devel
BuildRequires:	perl-Apache-Session
BuildRequires:	perl-Apache-SessionX 
BuildRequires:	perl-ExtUtils-XSBuilder
BuildRequires:	perl-HTML-Parser 
BuildRequires:	perl-Parse-RecDescent
BuildRequires:	perl-Tie-IxHash
BuildRequires:	perl-libwww-perl
BuildRequires:	perl-devel
BuildRequires:	file
BuildRoot:	%{_tmppath}/%{name}-%{version}-buildroot

%description
Embperl is a framework for building websites with Perl.

For the beginner it's an easy to setup and use way of embedding Perl code in
HTML pages. It delivers several features that ease the task of creating a
ebsites, including dynamic tables, formfield-processing,
escaping/unescaping, session handling, caching and more.

If your demands grow it gives you the power to make your Website
object-oriented and build it out of small reusable components. If you don't
like the idea of mixing up all your layout and code then Embperl also
supports separating it in different objects (e.g. creating an MVC
application). Of course Embperl doesn't tie you to HTML - it allows
components to be from different source formats (e.g. HTML, WML, XML, POD,
...) and if necessary transforms them (for example via XSLT) to other output
formats. This is achieved by dividing the output generation into small
steps, where each is processed by a plugable provider. Advanced users can
create their own syntax definitions (for example tag libraries) and extend
Embperl by writing their own providers and much more...

Embperl is a server-side tool, which means that it's browser-independent. It
can run in various ways: under mod_perl, as a CGI script, or offline.

%prep

%setup -q -n Embperl-%{version}

cp %{SOURCE1} %{mod_conf}

# fix strange perms
find . -type d -perm 0700 -exec chmod 755 {} \;
find . -type f -perm 0555 -exec chmod 755 {} \;
find . -type f -perm 0444 -exec chmod 644 {} \;

# strip away annoying ^M
find . -type f|xargs file|grep 'CRLF'|cut -d: -f1|xargs perl -p -i -e 's/\r//'
find . -type f|xargs file|grep 'text'|cut -d: -f1|xargs perl -p -i -e 's/\r//'

rm -f eg/x/config.htm

%patch0 -p1

perl -pi -e "s/\&lt;/\</;" eg/x/loop.htm

cat << EOF > eg/.htaccess
<Files ~ (\.htm)>
SetHandler perl-script
PerlResponseHandler Embperl
</Files>
Options +Indexes
EOF

find -type d|grep CVS|xargs rm -rf
find -type f|grep cvsignore|xargs rm -f

%build
# (oe) pull in the apr and apu headers where ever they may be
export APR_HEADERS="`apr-1-config --includes`"
export APU_HEADERS="`apu-1-config --includes`"
perl -pi -e "s|-I\\\$EPPATH \\\$i|-I\\\$EPPATH \\\$i $APR_HEADERS $APU_HEADERS|g" Makefile.PL

perl -pi -e "s/action_module/actions_module/;" Makefile.PL
perl xsbuilder/source_scan.pl
perl xsbuilder/xs_generate.pl

cat << EOF | perl Makefile.PL INSTALLDIRS=vendor OPTIMIZE="%{optflags} `apr-1-config --cppflags`" INC="-I%{_includedir}/apache -I%{_includedir}/apache/regex -I%{_includedir}/apache/os/unix $APR_HEADERS $APU_HEADERS -I%{_includedir}/libxml2 -I./xs" 
y
%{_includedir}/apache
y
%{_sbindir}/httpd
%{_libdir}/apache-extramodules
%{_libdir}/apache
.
EOF

make LD_RUN_PATH=""

# one test fails atm
#make test

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

install -d %{buildroot}%{_sysconfdir}/httpd/modules.d

eval `perl '-V:installarchlib'`
install -d %{buildroot}/$installarchlib
%makeinstall_std

%__os_install_post
find %{buildroot}%{_prefix} -type f -print | sed "s@^%{buildroot}@@g" | grep -v perllocal.pod > %{module}-%{version}-filelist

install -m0644 %{mod_conf} %{buildroot}%{_sysconfdir}/httpd/modules.d/%{mod_conf}

install -d %{buildroot}%{_var}/www/html/addon-modules
ln -s ../../../..%{_docdir}/%{name}-%{version} %{buildroot}%{_var}/www/html/addon-modules/%{name}-%{version}

rm -rf test/tmp/* 
rm -rf blib
mkdir -p blib/arch
pushd blib/arch
eval `perl '-V:vendorarch'`
ln -s ../../../../../..$vendorarch/auto/ .
popd

cd test
#chmod 755 tmp
find -type f|xargs perl -pi -e \
	"s|$RPM_BUILD_DIR/embperl|%{_docdir}/%{name}-%{version}|g;"
perl -pi -e 's/\015//;' conf/config.pl
cd ..
rm -f %{buildroot}$vendorarch/auto/Embperl/*.bs

%post
if [ -f %{_var}/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi

%postun
if [ "$1" = "0" ]; then
    if [ -f %{_var}/lock/subsys/httpd ]; then
	%{_initrddir}/httpd restart 1>&2
    fi
fi

%clean 
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc MANIFEST READM* eg test.pl test *.pod TODO blib
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/%{mod_conf}
%attr(0755,root,root) %{_bindir}/*
%{perl_vendorlib}/*
%{_mandir}/*/*
%{_var}/www/html/addon-modules/*
