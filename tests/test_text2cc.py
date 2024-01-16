# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import eol_scons.tools.text2cc as t2c


_example = """\
first "line"
second "line"
"""

_code = '/***** DO NOT EDIT *****/\n'
_code += 'const char* EXAMPLE = \n'
_code += '"first \\"line\\"\\n"\n"second \\"line\\"\\n"\n"";\n'


def test_text2cc():
    assert t2c._escape('hello world') == '"hello world"'
    assert t2c._escape('hello world\n') == '"hello world\\n"\n""'
    assert t2c._escape('hello world\r\n') == '"hello world\\r\\n"\n""'
    assert t2c._escape('hello\r\nworld\r\n') == '"hello\\r\\n"\n"world\\r\\n"\n""'

    code = t2c.text2cc(_example, "EXAMPLE")
    print(code)
    assert code == _code
