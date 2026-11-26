import asyncio
import importlib
import runpy
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

MAIN_PATH = str(Path(__file__).resolve().parent.parent / "main.py")


def make_env(monkeypatch, model="test-model", api_key="test-key"):
    for name, value in (("CLAUDE_MODEL", model), ("ANTHROPIC_API_KEY", api_key)):
        if value:
            monkeypatch.setenv(name, value)
        else:
            monkeypatch.setenv(name, "")


def load_main(monkeypatch, **env):
    make_env(monkeypatch, **env)
    sys.modules.pop("main", None)
    return importlib.import_module("main")


def make_fake_client_class(created):
    class FakeClient:
        def __init__(self, command, args):
            self.command, self.args = command, args
            created.append(self)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

    return FakeClient


@pytest.fixture
def main_module(monkeypatch):
    return load_main(monkeypatch)


class TestModuleConfig:
    def test_it_fails_when_claude_model_is_empty(self, monkeypatch):
        with pytest.raises(AssertionError, match="CLAUDE_MODEL"):
            load_main(monkeypatch, model="")

    def test_it_fails_when_api_key_is_empty(self, monkeypatch):
        with pytest.raises(AssertionError, match="ANTHROPIC_API_KEY"):
            load_main(monkeypatch, api_key="")

    def test_it_loads_when_both_env_vars_are_set(self, main_module):
        assert main_module.claude_model == "test-model"


class TestRunReview:
    def test_it_prints_the_report(self, main_module, monkeypatch, capsys):
        agent = MagicMock()
        agent.review.return_value = "REPORT"
        monkeypatch.setattr(main_module, "Claude", MagicMock())
        monkeypatch.setattr(main_module, "CodeReviewAgent", lambda _c: agent)

        main_module.run_review("some_dir")

        agent.review.assert_called_once_with("some_dir")
        assert "REPORT" in capsys.readouterr().out

    def test_it_exits_with_message_when_review_raises_value_error(
        self, main_module, monkeypatch
    ):
        agent = MagicMock()
        agent.review.side_effect = ValueError("needs >= 7 files")
        monkeypatch.setattr(main_module, "Claude", MagicMock())
        monkeypatch.setattr(main_module, "CodeReviewAgent", lambda _c: agent)

        with pytest.raises(SystemExit) as exc:
            main_module.run_review("small_dir")

        assert "needs >= 7 files" in str(exc.value)


class TestMain:
    def _patch(self, main_module, monkeypatch):
        created = []
        cli = MagicMock(initialize=AsyncMock(), run=AsyncMock())
        monkeypatch.setattr(main_module, "Claude", MagicMock())
        monkeypatch.setattr(main_module, "MCPClient", make_fake_client_class(created))
        monkeypatch.setattr(main_module, "CliChat", MagicMock())
        monkeypatch.setattr(main_module, "CliApp", lambda _chat: cli)
        return created, cli

    def test_it_starts_only_the_doc_server_without_extra_scripts(
        self, main_module, monkeypatch
    ):
        monkeypatch.setattr(sys, "argv", ["main.py"])
        monkeypatch.setenv("USE_UV", "0")
        created, cli = self._patch(main_module, monkeypatch)

        asyncio.run(main_module.main())

        assert [(c.command, c.args) for c in created] == [
            ("python", ["mcp_server.py"])
        ]
        cli.initialize.assert_awaited_once()
        cli.run.assert_awaited_once()

    def test_it_uses_uv_for_doc_server_when_use_uv_is_set(
        self, main_module, monkeypatch
    ):
        monkeypatch.setattr(sys, "argv", ["main.py"])
        monkeypatch.setenv("USE_UV", "1")
        created, _ = self._patch(main_module, monkeypatch)

        asyncio.run(main_module.main())

        assert (created[0].command, created[0].args) == ("uv", ["run", "mcp_server.py"])

    def test_it_starts_one_extra_client_per_script_argument(
        self, main_module, monkeypatch
    ):
        monkeypatch.setattr(sys, "argv", ["main.py", "a.py", "b.py"])
        monkeypatch.setenv("USE_UV", "0")
        created, _ = self._patch(main_module, monkeypatch)

        asyncio.run(main_module.main())

        assert [c.args for c in created[1:]] == [["run", "a.py"], ["run", "b.py"]]


class TestEntrypoint:
    def _run(self, monkeypatch, argv):
        make_env(monkeypatch)
        monkeypatch.setattr(sys, "argv", argv)
        runpy.run_path(MAIN_PATH, run_name="__main__")

    def test_it_rejects_review_without_directory(self, monkeypatch):
        with pytest.raises(SystemExit) as exc:
            self._run(monkeypatch, ["main.py", "--review"])

        assert "Usage" in str(exc.value)

    def test_it_rejects_review_with_extra_arguments(self, monkeypatch):
        with pytest.raises(SystemExit) as exc:
            self._run(monkeypatch, ["main.py", "--review", "a", "b"])

        assert "Usage" in str(exc.value)

    def test_it_runs_review_and_exits_cleanly_with_directory(
        self, monkeypatch, capsys
    ):
        agent = MagicMock()
        agent.review.return_value = "REPORT"
        monkeypatch.setattr("core.claude.Claude", MagicMock())
        monkeypatch.setattr("core.code_review.CodeReviewAgent", lambda _c: agent)

        with pytest.raises(SystemExit) as exc:
            self._run(monkeypatch, ["main.py", "--review", "src"])

        assert exc.value.code == 0
        agent.review.assert_called_once_with("src")
        assert "REPORT" in capsys.readouterr().out
