#! /bin/bash

# Gateway script for CI functionality.

# TOPDIR is the path to the top of the rpmbuild output tree.  We have to set
# it here so that each step uses the same value.  Packages are written there
# after being built then pushed to the EOL package repository.

# If the Jenkins WORKSPACE environment variable is set, then use it to set
# TOPDIR.  Otherwise use the default that build_rpm.sh would use.
if [ -n "$WORKSPACE" ]; then
    export TOPDIR=$WORKSPACE/rpm_build
fi
if command -v rpmbuild >/dev/null 2>&1; then
    export TOPDIR=${TOPDIR:-$(rpmbuild --eval %_topdir)_$(hostname)}
fi

reposcripts="$HOME/eol-repo/scripts"
if [ ! -d "$reposcripts" ]; then
    echo "Not found: $reposcripts"
    exit 1
fi

echo WORKSPACE=$WORKSPACE
echo TOPDIR=$TOPDIR
echo reposcripts=$reposcripts


build_rpms()
{
    # Only clean the rpmbuild space if it's Jenkins, since otherwise it can be
    # the user's local rpmbuild space with unrelated packages, and we should
    # not go around removing them.
    if [ -n "$WORKSPACE" ]; then
        (set -x; rm -rf "$TOPDIR/RPMS"; rm -rf "$TOPDIR/SRPMS")
    fi
    # this conveniently creates a list of built rpm files in rpms.txt.
    (set -x; $reposcripts/build_rpm.sh rpm/eol_scons.spec snapshot)
}


dpkgdir=
codename=

get_dpkgdir() # codename
{
    if [ -n "$codename" ]; then
        return
    fi
    codename="$1"
    if [ -z "$codename" ]; then
        echo "Codename is required, eg bionic"
        exit 1
    fi
    # get architecture for current container or host
    dpkgarch="$(dpkg-architecture -qDEB_BUILD_ARCH)"
    dpkgdir="build/dpkg-$codename-$dpkgarch"
}


build_dpkg() # codename
{
    get_dpkgdir "$@"
    rm -rf ${dpkgdir}
    mkdir -p ${dpkgdir}
    # $reposcripts/build_dpkg.sh -d ${dpkgdir} ${dpkgarch}
    $reposcripts/build_dpkg.sh ${dpkgdir}
}


push_eol_repo()
{
    # upload packages using the eol-repo script in home directory
    $reposcripts/upload_packages.sh upload `cat rpms.txt`
}


method="${1:-help}"
shift

case "$method" in

    build_rpm|build_rpms)
        build_rpms "$@"
        ;;

    push_rpm|push_rpms)
        push_eol_repo
        ;;

    build_dpkg)
        build_dpkg "$@"
        ;;

    upload_dpkg)
        get_dpkgdir "$1"
        $reposcripts/upload_packages.sh codename="$codename" upload ${dpkgdir}
        ;;

    *)
        if [ "$method" != "help" ]; then
            echo Unknown command "$1".
        fi
        echo Available commands: build_rpms, push_rpms, build_dpkg, upload_dpkg.
        exit 1
        ;;

esac
