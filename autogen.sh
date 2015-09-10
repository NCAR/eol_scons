#!/bin/sh

set -e

echo "Adding libtools."
libtoolize --force --automake

echo "Building macros."
ACLOCAL_AMFLAGS="-I config $ACLOCAL_AMFLAGS"
export ACLOCAL_AMFLAGS
aclocal $ACLOCAL_AMFLAGS

echo "Building config header."
autoheader

echo "Building makefiles."
automake -f --add-missing --foreign

echo "Building configure."
autoconf

echo 'run "configure; make"'
