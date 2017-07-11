"""
Incorporate the scons_to_ninja.py module from the Chromium source to
generate ninja build files.  Unlike the dump_trace.py tool and the external
scons2ninja script which uses it, this tool integrates with scons directly.
Even though scons_to_ninja.py was added to the eol_scons package for early
testing, it is not currently used by this tool.

The ideas in scons_to_ninja have been modified significantly for inclusion
this tool.  Instead of overloading PRINT_CMD_LINE_FUNC and letting scons
run with no_exec, this tool actually traverses the node tree and extracts
command strings where possible.  Nodes with builders which do not translate
to shell commands are built explicitly by scons after generating the ninja
file.  For example, files like version info files which can only be built
within scons are updated by scons.  After the ninja file has been generated
by scons, it should be possible to run ninja to build the rest of the
targets.

Alias nodes are translated to ninja phony rules.  Directory targets are not
added to the ninja build rules but are still traversed for file targets.

The examples below use the aeros source tree.

The SConstruct file must be modified slightly.  NinjaCheck() must be called
after all the SConscript files have been loaded, on any Environment to
which the ninja tool has been applied.  For example, it is safe to just add
this to the end of the SConstruct file, it just adds one more Environment
instance:

@code
ninja = Environment(tools = ['ninja'])
ninja.NinjaCheck()
@endcode

The call to NinjaCheck() is the hook to tell the ninja tool all the nodes
have been created. If ninja output is enabled, then it will write the ninja
file and modify BUILD_TARGETS to contain the scons-only nodes, if any.

Multiple ninja build files can be generated with scons.  The first example
below generates the default ninja build file for the default scons targets.

@code
scons ninja=build.ninja
ninja
@endcode

The next example builds a different ninja file for a specific scons target.
If aliases are passed as targets on the scons command line, then they will
be available as ninja (phony) targets.  Or specific files can be named as
ninja targets:

@code
scons ninja=all.ninja all
ninja -f all.ninja all
ninja -f all.ninja aeros/aeros
@endcode

Note that ninja seems to build up its cache of which targets have been
updated, seprate from scons, so the first ninja run may build everything
even if a scons build wouldn't.  Eventually they converge so that both know
all targets are up to date and neither rebuilds any targets, although ninja
is much faster at checking the dependencies, since they are "pre-computed"
and included explicitly in a single file.

Issues:

It may be necessary to build the whole project first to make sure certain
source and header files are generated, such as Qt uic and moc output files,
since include dependencies on those files do not yet translate into the
ninja dependencies.

Some eol_scons targets have complicated dependencies and use Value nodes
and Actions which run python function.  For example, many test targets do
not yet translate to ninja.  Doxyfile targets in theory should be built
from their Value nodes when scons is run, leaving just the doxygen commands
to be run in ninja rules, but in practice that does not work yet.  There
are extra dependencies which cause scons to build the documentation rather
than just the Doxyfiles.  This is probably not a big disadvantage, since
usually only the compile rules need to be run when doing interactive
development, and ninja speeds up the edit/compile cycle by avoiding the
scons startup time.  The developer must remember to re-run scons and
re-generate the ninja build file as needed, such as whenever header
dependencies or source file lists change, or when compiler flags need to
change.

Simple python function targets, like header files generated from the
svninfo and gitinfo tools, and source files generated with the text2cc
tool, work fine with ninja.  When generating a ninja file, SCons
automatically builds those nodes (if they are dependencies of the
command-line targets) to make sure they are updated.  Then the ninja rules
have all they need to run.

It should be possible to define an alias in a project's SConstruct file
which contains all the aliases and targets which work with ninja, while
separately specifying which explicit, minor targets must be built with
scons, such as Doxyfiles, uic, and moc files.  Perhaps this default ninja
configuration can be specified using the ninja tool interface, to be used
whenever the ninja output is enabled and no other targets are specified on
the command line.

The rerun tool can also be used to speed up the SCons edit and compile
cycle.  It works differently, in that it remembers a build failure from the
last scons and just reruns that one command until it succeeds.  This is
faster than a full SCons startup which requires reading all of the
SConscript files.  However, if the same target can be built by a ninja
rules file generated from scons, then ninja is still faster, even with many
more rules in the ninja build file.

Using ninja deliberately circumvents many of the consistency checks which
scons provides.  It is perhaps similar to running scons with the options
`--implicit-deps-unchanged --max-drift=1`.  If that loss of consistency is
acceptable, then ninja is still faster than running scons with those
options.
"""

import os
import SCons
from SCons.Variables import BoolVariable
import eol_scons.scons_to_ninja as sn

variables = None

CustomCommandPrinter = None

# This somewhat approximates the Entry inner function in
# SCons.Script.Main which generates nodes from a BUILD_TARGETS list
# which may contain strings.  We have to recreate it here because there
# is no easy way to get at that node list when this is called.

def Entry(x, fs):
    if isinstance(x, SCons.Node.Node):
        node = x
    else:
        node = None
        ltop = ''
        # Curdir becomes important when SCons is called with -u, -C,
        # or similar option that changes directory, and so the paths
        # of targets given on the command line need to be adjusted.
        curdir = os.path.join(os.getcwd(), str(ltop))
        for lookup in SCons.Node.arg2nodes_lookups:
            node = lookup(x, curdir=curdir)
            if node is not None:
                break
        if node is None:
            node = fs.Entry(x, directory=ltop, create=1)
    return node

# This is necessary to handle SCons's "variant dir" feature.  The filename
# associated with a Scons node can be ambiguous: it might come from the
# build dir or the source dir.
def GetRealNode(node):
  src = node.srcnode()
  if src.stat() is not None:
    return src
  return node


_ninja_header = """\
# Generated by eol_scons/tools/ninja.py

# Generic rule for handling any command.
rule cmd
  command = $cmd

"""

_ninja_alias = """
build %s: phony %s
"""

_ninja_cmd = """
build %s: cmd %s
  cmd = %s
"""


class NinjaNode(object):
    """
    Adapt a SCons Node with some methods and information necessary for
    generating ninja syntax from it.
    """
    ALIAS = "alias"
    DIRECTORY = "directory"
    VALUE = "value"
    FILE = "file"

    def __init__(self, node):
        self.node = node
        self.ntype = None
        self.assignType()

    def assignType(self):
        if self.isAlias():
            self.ntype = NinjaNode.ALIAS
        elif self.isDirectory():
            self.ntype = NinjaNode.DIRECTORY
        elif self.isValue():
            self.ntype = NinjaNode.VALUE
        else:
            self.ntype = NinjaNode.FILE

    def getType(self):
        return self.ntype

    def getNode(self):
        return self.node

    def isAlias(self):
        "Return true if this is a SCons Alias node."
        return isinstance(self.node, SCons.Node.Alias.Alias)

    def isDirectory(self):
        "Return true if this is a SCons Dir node."
        return isinstance(self.node, SCons.Node.FS.Dir)

    def isValue(self):
        return isinstance(self.node, SCons.Node.Python.Value)

    def isConfNode(self):
        "This is not as precise as it could be."
        # contains() is used instead of startswith() because variants might
        # put their temporary directory under the variant dir, eg,
        # build/.sconf_temp.  Maybe it would be enough to use get_dir() ==
        # ".sconf_temp", but more likely any path containing .sconf_temp is
        # a conf node.
        return ".sconf_temp" in self.node.get_path()

    def getRule(self):
        """
        Create the ninja rule for this node by converting actions to strings.
        """
        node = self.node
        depnodes = node.all_children()
        if self.isAlias():
            deps = [str(dep) for dep in depnodes]
            return _ninja_alias % (node.name, ' '.join(deps))

        dest_path = node.get_path()
        deps = [GetRealNode(dep).get_path() for dep in depnodes]
        executor = node.get_executor()
        if executor is None:
            print("ignoring node without executor: %s" % (str(node)))
            return ""
        actions = executor.get_action_list()
        env = node.get_env()
        from SCons.Subst import SUBST_RAW
        cmds = [env.subst(cmd, 0, executor=executor)
                for cmd in str(executor).splitlines()
                if not cmd.startswith('_checkMocIncluded')]
        return _ninja_cmd % (dest_path, ' '.join(deps), ' && '.join(cmds))


def WriteFile(dest_file, node_list):
    dest_temp = '%s.tmp' % dest_file
    ninja_fh = open(dest_temp, 'w')
    ninja_fh.write(_ninja_header)

    for node in node_list:
        nn = NinjaNode(node)
        ninja_fh.write(nn.getRule())

    # Make the result file visible atomically.
    os.rename(dest_temp, dest_file)


def SeparateNodes(env, targets, ninjanodes, sconsnodes):
    """
    Starting with the root targets, traverse the tree of dependency nodes
    separating them into filesystem nodes which can be built by ninja and
    those which can only be built within scons.

    Maybe this should be replaced with SCons.Node.Walker.
    """
    tree = targets[:]
    while tree:
        node = tree[0]
        del tree[0]
        nn = NinjaNode(node)
        if not node.has_builder() or node in ninjanodes or node in sconsnodes:
            continue
        depnodes = node.all_children()
        tree.extend(depnodes)
        # print("separating node %s with children: %s" %
        #       (str(node), " ".join([str(n) for n in depnodes])))
        if nn.isAlias():
            # Explicitly add Aliases to ninja nodes; they will be handled
            # specially in WriteFile()
            print("adding Alias node to ninja: %s" % (str(node)))
            ninjanodes.append(nn.getNode())
        elif nn.isDirectory():
            # Directory nodes have an implicit function builder, MkdirFunc,
            # but most of the time we don't really need to build them, we
            # just want to traverse them.  This means we can't use a
            # directory name as a kind of alias for all targets underneath
            # it.  If that's needed, then add an explicit Alias() for that
            # directory in scons, eg, env.Alias('dox', env.Dir("apidocs")).
            
            # print("traversing Directory node: %s" % (str(node)))
            # ninjanodes.append(node)
            pass
        elif nn.isConfNode():
            pass
        elif nn.isValue():
            print("building Value node with scons: %s" % (str(node)))
            sconsnodes.append(node)
        elif isinstance(node.builder.action, SCons.Action.FunctionAction):
            print("building function node with scons: %s" % (str(node))) 
            sconsnodes.append(node)
        else:
            ninjanodes.append(node)
    # print("SeparateNodes() finished.")
    return ninjanodes, sconsnodes


def generate(env):
    global variables
    if variables is None:
        variables = env.GlobalVariables()
        variables.AddVariables((
            'ninja', 'Write ninja build rules into the given file.', None))
    env.AddMethod(NinjaCheck)


def NinjaCheck(env):
    variables.Update(env)
    ninjapath = env.get('ninja')
    if not ninjapath:
        return

    print("Generating ninja file (%s) instead of running commands..." %
          (ninjapath))

    targets = SCons.Script.BUILD_TARGETS
    fs = SCons.Node.FS.get_default_fs()
    nodes = [_f for _f in map(lambda x: Entry(x, fs), targets) if _f]
    # nodes = [_f for _f in map(fs.Entry, targets) if _f]

    ninjanodes, sconsnodes = SeparateNodes(env, nodes, [], [])
    SCons.Script.BUILD_TARGETS[:] = sconsnodes
    WriteFile(ninjapath, ninjanodes)

  
# def generate(env):
#     global variables
#     if variables is None:
#         variables = env.GlobalVariables()
#         variables.AddVariables((
#             'generate_ninja', 'Write ninja build rules into the given file.', None))

#     variables.Update(env)
#     global CustomCommandPrinter
#     ninjapath = env.get('generate_ninja')
#     if ninjapath and not CustomCommandPrinter:
#         print("Generating ninja file (%s) instead of running commands..." %
#               (ninjapath))
#         sn.GenerateNinjaFile(env, dest_file=ninjapath)
#         CustomCommandPrinter = env['PRINT_CMD_LINE_FUNC']

#     elif ninjapath:

#         # The upstream scons_to_ninja.py module creates an inner function
#         # to append target nodes in a single Environment to a single list.
#         # However, we need to pull nodes from multiple environments.  So to
#         # avoid modifying the upstream source, we duplicate the
#         # per-Environment setup here, but we cache the CustomCommandPrinter
#         # function created by GenerateNinjaFile() so other environments can
#         # refer to it.
    
#         # Tell SCons not to run any commands, just report what would be run.
#         env.SetOption('no_exec', True)
#         # Tell SCons that everything needs rebuilding.
#         env.Decider(lambda dependency, target, prev_ni: True)
#         if CustomCommandPrinter != env.get('PRINT_CMD_LINE_FUNC'):
#             env.Append(PRINT_CMD_LINE_FUNC=CustomCommandPrinter)
  

def exists(env):
    return true

