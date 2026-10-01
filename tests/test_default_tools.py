# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import eol_scons.hooks.default as default_hook
from SCons.Script import Environment
from SCons.Tool import Tool


def fake_default_tools(monkeypatch, tool_list):
    "Monkeypatch the default tool list for PLATFORM=test."
    # FakeTool.created = []
    # monkeypatch.setattr(default_hook.SCons.Tool, 'Tool', FakeTool)
    monkeypatch.setattr(default_hook.SCons.Tool, 'tool_list',
                        lambda platform, env: tool_list)
    monkeypatch.setattr(default_hook, '_default_tool_list', None)


def test_default_hook_instantiates_tool_names(monkeypatch):
    tool_names = ['cc', 'link']
    fake_default_tools(monkeypatch, tool_names)
    env = Environment()
    tools = default_hook._load_default_tool_list(env)
    assert all(isinstance(tool, Tool) for tool in tools)
    assert [str(tool) for tool in tools] == tool_names


def test_default_hook_reuses_tool_instances(monkeypatch):
    tool_instances = [Tool('cc'), Tool('link')]
    fake_default_tools(monkeypatch, tool_instances)
    env = Environment()
    tools = default_hook._load_default_tool_list(env)
    assert tools == tool_instances
