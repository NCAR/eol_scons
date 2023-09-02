#! /bin/bash

# Gateway script for CI functionality.

# TOPDIR is the path to the top of the rpmbuild output tree.  We have to set
# it here so that each step uses the same value.  Packages are written there
# after being built, then signed, then pushed to the EOL package repository.

# If the Jenkins WORKSPACE environment variable is set, then use it to set
# TOPDIR.  Otherwise use the default that build_rpm.sh would use.
if [ -n "$WORKSPACE" ]; then
    export TOPDIR=$WORKSPACE/rpm_build
fi
export TOPDIR=${TOPDIR:-$(rpmbuild --eval %_topdir)_$(hostname)}

# In EOL Jenkins, these are global properties set in Manage Jenkins ->
# Configure System.  Provide defaults here to test outside of Jenkins.
DEBIAN_REPOSITORY="${DEBIAN_REPOSITORY:-/net/ftp/pub/archive/software/debian}"
YUM_REPOSITORY="${YUM_REPOSITORY:-/net/www/docs/software/rpms}"
export DEBIAN_REPOSITORY YUM_REPOSITORY
export GPGKEY="NCAR EOL Software <eol-prog@eol.ucar.edu>"

echo WORKSPACE=$WORKSPACE
echo TOPDIR=$TOPDIR
echo DEBIAN_REPOSITORY=$DEBIAN_REPOSITORY
echo YUM_REPOSITORY=$YUM_REPOSITORY


build_rpms()
{
    # Only clean the rpmbuild space if it's Jenkins, since otherwise it can be
    # the user's local rpmbuild space with unrelated packages, and we should
    # not go around removing them.
    if [ -n "$WORKSPACE" ]; then
        (set -x; rm -rf "$TOPDIR/RPMS"; rm -rf "$TOPDIR/SRPMS")
    fi
    # this conveniently creates a list of built rpm files in rpms.txt.
    (set -x; scons build_rpm scripts/eol_scons.spec build)
}


sign_rpms()
{
    (set -x; exec rpm --addsign --define="%_gpg_name ${GPGKEY}" `cat rpms.txt`)
}


push_eol_repo()
{
    source $YUM_REPOSITORY/scripts/repo_funcs.sh
    move_rpms_to_eol_repo `cat rpms.txt`
    update_eol_repo $YUM_REPOSITORY
}


method="${1:-help}"
shift

case "$method" in

    build_rpms)
        build_rpms "$@"
        ;;

    sign_rpms)
        sign_rpms
        ;;

    push_rpms)
        push_eol_repo
        ;;

    *)
        if [ "$method" != "help" ]; then
            echo Unknown command "$1".
        fi
        echo Available commands: build_rpms, sign_rpms, push_rpms.
        exit 1
        ;;

esac
