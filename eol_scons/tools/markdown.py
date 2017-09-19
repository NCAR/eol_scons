"""
Add a Markdown builder which automatically detects a default markdown
converter program but also allows overriding it with the MARKDOWN option.
If no default converter is found, print a warning but use 'markdown2' as a
fallback.

Use it like this:

    readme = env.Markdown("README.html", "README")
"""
from __future__ import print_function

import subprocess as sp

import SCons
from SCons.Script import Builder
from SCons.Script import Action

_options = None


def _detect(env):
    # If a default has been specified before loading this tool, the use it.
    # This way a particular command can be forced by the source tree but
    # overridden with the options.
    if env.get('MARKDOWN_DEFAULT'):
        return True
    for md in ['markdown2', 'markdown_py', 'markdown']:
        if env.Detect(md):
            env['MARKDOWN_DEFAULT'] = md
            return True
    env['MARKDOWN_DEFAULT'] = None
    return False


def MarkdownMessage(target, source, env):
    return env.subst("${SOURCE} % ${MARKDOWN_DICT} | "
                     "${MARKDOWN_COMMAND} > ${TARGET}",
                     source=source, target=target)


def MarkdownBuilder(target, source, env):
    # Do simple python string replacement on the contents.
    content = source[0].get_contents() % env.get('MARKDOWN_DICT', {})
    cmd = env.subst("${MARKDOWN_COMMAND} > ${TARGET}", target=target)
    mdp = sp.Popen(cmd, stdin=sp.PIPE, shell=True)
    mdp.stdin.write(content)
    mdp.stdin.close()
    return mdp.wait()


# The builder does not change with each environment, only the setting of
# the MARKDOWN command.
_builder = Builder(action=Action(MarkdownBuilder, MarkdownMessage,
                                 varlist=["MARKDOWN_COMMAND",
                                          "MARKDOWN_DICT"]))

def generate(env):
    if env['BUILDERS'].get('Markdown'):
        return
    # Use the option setting by default, but this will be replaced if the
    # option is not set.
    env['MARKDOWN_COMMAND'] = '${MARKDOWN}'
    found = _detect(env)
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add("MARKDOWN", "Command to convert markdown files.",
                     env.subst("${MARKDOWN_DEFAULT}"))
    _options.Update(env)
    if not found and not env.get('MARKDOWN'):
        print("*** No markdown converter command found.  "
              "Specify it with the MARKDOWN option, "
              "or install one of the packages "
              "python-markdown, discount, or python-markdown2.")
        env['MARKDOWN_COMMAND'] = 'markdown2'
    env['BUILDERS']['Markdown'] = _builder

def exists(env):
    return _detect(env)

