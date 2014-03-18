
def generate(env):
    if env['PLATFORM'] != 'darwin':
        env.Append (LIBS = ["boost_date_time"])
    else:
        env.Append (LIBS = ["boost_date_time-mt"])
    # If the boost libraries must be found in an alternative location, then
    # make sure the prefixoptions tool is loaded and OPT_PREFIX set.

def exists(env):
    return True

