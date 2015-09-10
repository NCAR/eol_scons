#!/bin/sh

set -e

echo "Adding libtools."
libtoolize --force --automake

echo "Building macros."
# ACLOCAL_FLAGS="-I config --output=config/aclocal.m4 $ACLOCAL_FLAGS"
ACLOCAL_FLAGS="-I config $ACLOCAL_FLAGS"
aclocal $ACLOCAL_FLAGS

echo "Building config header."
autoheader

echo "Building makefiles."
automake -f --add-missing --foreign

echo "Building configure."
autoconf

echo 'run "configure; make"'
