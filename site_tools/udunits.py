import os


def generate(env):
    env.Append(LIBS=['udunits'])


def exists(env):
    return True

