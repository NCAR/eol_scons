"""
Helper functions for the Qt tools, so they do not need to be duplicated across
Qt versions.
"""


def qualify_module_name(module, xprefix):
    """
    Convert the Qt module name to the version-qualified name.
    @param module: the Qt module name, like "QtCore"
    @param xprefix: the expected version prefix, like "Qt6"
    """
    if module.startswith('Qt') and not module.startswith(xprefix):
        module = xprefix + module[2:]
    return module


def replace_drive_specs(pathlist):
    """
    Modify the given list in place.  For each node in pathlist, if the node
    path starts with a drive specifier like C:, replace it with a string
    path with the drive specifier replaced with an absolute path like /c.
    This preserves any list elements as nodes if their path does not need
    to be fixed.  This was used for scons3.  Scons4 does not use it.
    Returns None.
    """
    for i, node in enumerate(pathlist):
        path = str(node)
        if path.startswith("C:"):
            pathlist[i] = path.replace('C:', '/c')
    return None
