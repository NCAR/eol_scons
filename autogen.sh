#!/bin/sh

set -ex

libtoolize --force --automake
aclocal -I config
autoheader
automake -f --add-missing --foreign
autoconf

set +x
echo 'run "configure; make"'
