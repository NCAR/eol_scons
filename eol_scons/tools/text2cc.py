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
    text = re.sub(r'"', r'\"', text)
    if (env['PLATFORM'] == "win32" or env['PLATFORM'] == "msys"):
    	text = re.sub(r'\r\n', r'\\n"\n"', text)
    else:
    	text = re.sub(r'\n', r'\\n"\n"', text)
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

    code = text2cc(_example, "EXAMPLE")
    print(code)
    assert(code == _code)
