
_options = None

def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add('POSTGRES_DIR',
"""Set the POSTGRES installation directory.
If set, the pq library and headers will be expected in POSTGRES_DIR/lib and
POSTGRES_DIR/include.  Otherwise the default is to use the system location.
""", None)
    _options.Update(env)
    env.Append(DEPLOY_SHARED_LIBS='pq')
    if env.get('POSTGRES_DIR'):
        env.AppendUnique(LIBPATH = "$POSTGRES_DIR/lib")
        env.AppendUnique(CPPPATH = "$POSTGRES_DIR/include")
    env.Append(LIBS=['pq',])

def exists(env):
    return True

