#!/bin/sh

set -e

echo "Adding libtools."
libtoolize --force --automake --ltdl

echo "Building macros."
ACLOCAL_FLAGS="-I config --output=config/aclocal.m4 $ACLOCAL_FLAGS"
aclocal $ACLOCAL_FLAGS

echo "Building config header."
autoheader

echo "Building makefiles."
automake --add-missing --foreign

echo "Building configure."
autoconf

echo 'run "configure; make"'
