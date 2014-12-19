# -*- python -*-
#
# SConscript tool which adds a pseudo-builder to embed a text file in C++
# code.

_text2cc = r"""cat $SOURCE | (echo '/***** DO NOT EDIT *****/' && echo 'const char* $TEXT_DATA_VARIABLE_NAME = ' && sed -e 's/\"/\\\"/g' -e 's/^/\"/g' -e 's/$$/\\n"/' && echo ';') > $TARGET"""


def _EmbedTextCC(env, target, source, variable):
    env.Command(target, source, _text2cc, TEXT_DATA_VARIABLE_NAME = variable)

def generate(env):
    env.AddMethod(_EmbedTextCC, "EmbedTextCC")

def exists(env):
    return True
