
_options = None

runtests = 'cd ${SOURCE.dir} && python ${SOURCE.file} '
runtests += '${PYTESTARGS} ${PYTESTS}'


def PythonTest(env, name, script, **kw):
    target = env.Command(name, script, runtests, **kw)
    env.Alias(name, target)
    return target


# Run py.test on the source files.

def PyDotTest(env, name, sources, **kw):
    target = env.Command(name, sources,
                         'py.test ${PYTESTARGS} ${SOURCES}', **kw)
    env.Alias(name, target)
    return target


def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add ('PYTESTS',
                      "The python test names to run, defaults to all.",
                      "")
        _options.Add ('PYTESTARGS',
                      "Arguments for python test script, such as -q -v or -d",
                      "-v")
    _options.Update(env)
    env.AddMethod(PythonTest, "PythonTest")
    env.AddMethod(PyDotTest, "PyDotTest")
                   

def exists(env):
    return True
