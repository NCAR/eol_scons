# -*- python -*-
"""
SConscript tool which adds a pseudo-builder to embed a text file in C++
code.
"""

from __future__ import print_function
import re
import sys

try:
    from StringIO import StringIO
except:
    from io import StringIO

def _escape(text):
    """
    Escape double quotes and newlines, preserving whatever line endings are
    in the text file for the source code.  This function is
    platform-agnostic.  If the code needs certain line endings in the text,
    then the revision control system should make sure the text file gets
    those line endings.  This function always generates newline line
    endings for the source code, ie, between the line strings, since
    compilers don't care about whitespace.
    """
    # First, escape all double quotes.
    text = re.sub(r'"', r'\"', text)
    # Then, escape all carriage returns and newlines.
    text = re.sub(r'\r', r'\\r', text)
    text = re.sub(r'\n', r'\\n', text)
    # Finally, everywhere there's a newline, insert a line break with
    # quotes to end the previous line and begin the next line.
    text = re.sub(r'\\n', r'\\n"\n"', text)
    return '"' + text + '"'


def text2cc(text, vname):
    "Embed plain @p text in C++ source code with variable name @p vname."
    # intext = StringIO(text)
    # lines = intext.readlines()
    # intext.close()
    code = StringIO()
    code.write("/***** DO NOT EDIT *****/\n")
    code.write("const char* %s = \n" % (vname));
    code.write(_escape(text))
    code.write(";\n")
    text = code.getvalue()
    code.close()
    return text


def _embedded_text_emitter(target, source, env):
    if str(target[0]) == str(source[0]):
        target = [ str(source[0]) + '.cc' ]
    return target, source

def _embedded_text_builder(target, source, env):
    text = source[0].get_text_contents()
    with open(str(target[0]), "w") as outfile:
        outfile.write(text2cc(text, env['TEXT_DATA_VARIABLE_NAME']))

def _message(target, source, env):
    return "Embedding text file '%s' in '%s'" % (source[0], target[0])

_embedded_builder = None
_have_embedded_builder = False

def _get_builder():
    global _embedded_builder
    global _have_embedded_builder
    
    if not _have_embedded_builder:
        import SCons
        from SCons.Script import Builder
        from SCons.Script import Action
        etaction = Action(_embedded_text_builder, _message, 
                          varlist=['TEXT_DATA_VARIABLE_NAME'])
        _embedded_builder = Builder(action=etaction,
                                    emitter=_embedded_text_emitter)
        _have_embedded_builder = True
        
    return _embedded_builder

def _EmbedTextCC(env, target, source, variable):
    return env.EmbeddedTextCC(target, source, TEXT_DATA_VARIABLE_NAME = variable)

def generate(env):
    env['BUILDERS']['EmbeddedTextCC'] = _get_builder()
    env.SetDefault(TEXT_DATA_VARIABLE_NAME="EMBEDDED_TEXT_DATA")
    env.AddMethod(_EmbedTextCC, "EmbedTextCC")

def exists(env):
    return True


_example = """\
first "line"
second "line"
"""

_code = '/***** DO NOT EDIT *****/\n'
_code += 'const char* EXAMPLE = \n'
_code += '"first \\"line\\"\\n"\n"second \\"line\\"\\n"\n"";\n'

def test_text2cc():
    assert(_escape('hello world') == '"hello world"')
    assert(_escape('hello world\n') == '"hello world\\n"\n""')
    assert(_escape('hello world\r\n') == '"hello world\\r\\n"\n""')
    assert(_escape('hello\r\nworld\r\n') == '"hello\\r\\n"\n"world\\r\\n"\n""')

    code = text2cc(_example, "EXAMPLE")
    print(code)
    assert(code == _code)


if __name__ == "__main__":
    with open(sys.argv[1]) as tf:
        print(text2cc(tf.read(), "TEXT2CC"))
