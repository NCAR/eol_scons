# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import eol_scons.hooks.default as default_hook


class FakeEnvironment(dict):
    def __init__(self):
        super().__init__(PLATFORM='test')


class FakeTool:
    created = []

    def __init__(self, name):
        self.name = name
        self.created.append(self)

    def __call__(self, env):
        env.setdefault('applied', []).append(self)


def run_default_tools(monkeypatch, tool_list):
    FakeTool.created = []
    monkeypatch.setattr(default_hook.SCons.Tool, 'Tool', FakeTool)
    monkeypatch.setattr(default_hook.SCons.Tool, 'tool_list',
                        lambda platform, env: tool_list)
    monkeypatch.setattr(default_hook, '_default_tool_list', None)
    return FakeTool.created


def test_default_hook_instantiates_tool_names(monkeypatch):
    tool_names = ['cc', 'link']
    created = run_default_tools(monkeypatch, tool_names)
    env = FakeEnvironment()

    default_hook._apply_default_tool(env)

    assert [tool.name for tool in created] == tool_names
    assert env['applied'] == created


def test_default_hook_reuses_tool_instances(monkeypatch):
    tools = [FakeTool('cc'), FakeTool('link')]
    run_default_tools(monkeypatch, tools)
    env = FakeEnvironment()

    default_hook._apply_default_tool(env)

    assert env['applied'] == tools