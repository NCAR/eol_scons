
import SCons.Warnings

_options = None

runtests = str('cd ${PYTHONTESTDIR} && ${PYTHON} ${PYTHONTESTSCRIPT} '
               '${PYTESTARGS} ${PYTESTS}')


def PythonTest(env, name, script, **kw):
    """
    Run the given test script with python, passing it PYTESTARGS and
    PYTESTS on the command line.  By default, it runs the script from the
    directory of the given environment, but that can be overridden by
    passing PYTHONTESTDIR in the keyword arguments.  The test script path
    is generated from the script argument relative to the test directory,
    unless an explicit path is passed in the PYTHONTESTSCRIPT keyword.

    This allows the builder to run test scripts in subdirectories as
    relative paths to the SConscript directory.  However, this approach was
    most useful for python test modules which used unittest.main(), and
    pytest makes that superfluous, so perhaps this builder should be
    deprecated in favor of using pytest.
    """
    # SCons.Warnings.warn(SCons.Warnings.DeprecatedWarning,
    #                     "*** PythonTest() builder is deprecated.  "
    #                     "Replace with PyTest() or another test builder.")
    testdir = env.Dir(kw.get('PYTHONTESTDIR', '.'))
    scriptpath = env.File(kw.get('PYTHONTESTSCRIPT', script)).get_path(testdir)
    target = env.Command(name, script, runtests,
                         PYTHONTESTSCRIPT=scriptpath,
                         PYTHONTESTDIR=testdir, **kw)
    env.Alias(name, target)
    return target



def PyTest(env, name, sources, **kw):
    """
    Run pytest, collecting tests from the source files.  To select only certain
    tests, add the -k option to PYTESTARGS.
    """
    target = env.Command(name, sources,
                         '${PYTEST} ${PYTESTARGS} ${SOURCES}', **kw)
    env.Alias(name, target)
    return target


def PyDotTest(env, name, sources, **kw):
    """
    Deprecated in favor of using pytest consistently.
    """
    SCons.Warnings.warn(SCons.Warnings.DeprecatedWarning,
                        "*** PyDotTest() is deprecated.  "
                        "Replace with PyTest().")
    return PyTest(env, name, sources, **kw)


def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add('PYTESTS',
                     "The python test names to run, defaults to all.",
                     "")
        _options.Add('PYTEST', "Name or path for pytest.", "pytest")
        _options.Add('PYTESTARGS',
                     "Arguments for python test script, such as -q -v or -d",
                     "-v")
    _options.Update(env)
    env.SetDefault(PYTHON='python')
    env.AddMethod(PythonTest, "PythonTest")
    env.AddMethod(PyDotTest, "PyDotTest")
    env.AddMethod(PyTest, "PyTest")
                   

def exists(env):
    return True
