"""
Utility functions to configure install modes, initially just for debugging.

The install mode is determined by the 'installmode' argument on the scons
command line. The ARGUMENTS dictionary is used instead of creating a Variable
to avoid cluttering the usage with something that will be used rarely and only
by developers.  This can be changed if practice suggests it is worth
documenting as a Variable.

The install modes are 'mock' and 'all'.  Use 'mock' mode to mock installer
commands instead of running the actual utilities, such as when a particular
installer command is not found or not supported on a particular platform. A
mocked command should create the targets so that dependent targets will be
built also.  This is useful beyond just using no_exec (-n) mode, since SCons
can check for things like consistency between File and Directory nodes. If
there are installer steps or utilities which work on multiple platforms, then
ideally they are run on each of those platforms rather than being mocked.

The 'all' mode indicates that installer nodes should be created for all
platforms rather than just the current platform.  'mock' implies 'all'.

This scons command creates installer nodes for all platforms, using defaults
for all the utility paths, but only echoes the commands using the no_exec
mode:

    scons installmode=all -n

This command also creates all installer nodes, but any installer nodes which
are built will be mocked:

    scons installmode=mock
"""

from SCons.Script import ARGUMENTS


MOCK = 'mock'
ALL = 'all'


def GetInstallMode():
    """
    Get the install mode from the environment.

    Returns the install mode as a string. If the install mode is not set,
    returns None.
    """
    mode = ARGUMENTS.get('installmode', None)
    if mode is not None and mode not in [MOCK, ALL]:
        raise ValueError(f'Invalid install mode: {mode}')
    return mode


def MockMode():
    """
    Return True if the install mode includes mock.  This is just more
    convenient than comparing the result of GetInstallMode to MOCK everywhere.
    """
    return GetInstallMode() == MOCK


def AllMode():
    """
    Check if the install mode is set to all.  Mock mode implies all.  Since
    some installer utilities naturally will not exist on the current platform,
    this mode implies that all installer utilities should be given default
    paths.
    """
    return GetInstallMode() in [MOCK, ALL]


def Command(cmd):
    """
    Given a command that would be run as part of creating an installer, return
    a command modified according to the current install mode. In mock mode,
    this means inserting mock: in front of the command.
    """
    if MockMode():
        if isinstance(cmd, str):
            return "echo mock: " + cmd
        elif isinstance(cmd, list):
            return ['echo', 'mock:'] + cmd
    return cmd


def MockEcho(message):
    """
    Echo a message according to the current install mode. In mock mode, this
    means prefixing the message with 'mock:' to make it clear that the
    message is being printed in mock mode and not as part of a real installer
    step.
    """
    if MockMode():
        print(f"mock: {message}")
