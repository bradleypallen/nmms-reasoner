"""Tests for pynmms CLI --rdfs flag with tell, ask, and repl subcommands."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from pynmms.cli.main import main


class TestRDFSTellCommand:
    def test_tell_rdfs_creates_base(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        Path(path).unlink()

        result = main(["tell", "-b", path, "--create", "--rdfs", "Happy(alice) |~ Good(alice)"])
        assert result == 0

        with open(path) as f:
            data = json.load(f)
        assert "Happy(alice)" in data["language"]
        assert "Good(alice)" in data["language"]
        assert len(data["consequences"]) == 1
        assert "rdfs_schemas" in data

        Path(path).unlink()

    def test_tell_rdfs_atom(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        Path(path).unlink()

        result = main(["tell", "-b", path, "--create", "--rdfs", "atom hasChild(alice,bob)"])
        assert result == 0

        with open(path) as f:
            data = json.load(f)
        assert "hasChild(alice,bob)" in data["language"]
        assert "alice" in data["individuals"]
        assert "bob" in data["individuals"]
        assert "hasChild" in data["roles"]

        Path(path).unlink()

    def test_tell_rdfs_no_create_missing(self):
        result = main(["tell", "-b", "/nonexistent/rdfs_base.json", "--rdfs", "P(a) |~ Q(a)"])
        assert result == 1


class TestRDFSAskCommand:
    def test_ask_rdfs_derivable(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump({
                "language": ["Happy(alice)", "Good(alice)"],
                "consequences": [{"antecedent": ["Happy(alice)"], "consequent": ["Good(alice)"]}],
                "individuals": ["alice"],
                "concepts": ["Happy", "Good"],
                "roles": [],
                "rdfs_schemas": [],
            }, f)
            path = f.name

        result = main(["ask", "-b", path, "--rdfs", "Happy(alice) => Good(alice)"])
        assert result == 0

        Path(path).unlink()

    def test_ask_rdfs_not_derivable(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump({
                "language": ["Happy(alice)"],
                "consequences": [],
                "individuals": ["alice"],
                "concepts": ["Happy"],
                "roles": [],
                "rdfs_schemas": [],
            }, f)
            path = f.name

        result = main(["ask", "-b", path, "--rdfs", "Happy(alice) => Sad(alice)"])
        assert result == 2

        Path(path).unlink()

    def test_ask_rdfs_with_trace(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump({
                "language": ["Happy(alice)"],
                "consequences": [],
                "individuals": ["alice"],
                "concepts": ["Happy"],
                "roles": [],
                "rdfs_schemas": [],
            }, f)
            path = f.name

        result = main([
            "ask", "-b", path, "--rdfs", "--trace",
            "Happy(alice) => Happy(alice)",
        ])
        assert result == 0

        Path(path).unlink()


class TestRDFSReplCommand:
    def _run_repl(self, inputs, rdfs=True):
        """Run the REPL with the given inputs."""
        args = ["repl"]
        if rdfs:
            args.append("--rdfs")
        with patch("builtins.input", side_effect=inputs + ["quit"]):
            return main(args)

    def test_repl_rdfs_tell_and_ask(self):
        result = self._run_repl([
            "tell Happy(alice) |~ Good(alice)",
            "ask Happy(alice) => Good(alice)",
        ])
        assert result == 0

    def test_repl_rdfs_tell_atom(self):
        result = self._run_repl([
            "tell atom hasChild(alice,bob)",
            "show",
        ])
        assert result == 0

    def test_repl_rdfs_show_schemas(self):
        result = self._run_repl([
            "tell schema subClassOf Man Mortal",
            "show schemas",
        ])
        assert result == 0

    def test_repl_rdfs_show_individuals(self):
        result = self._run_repl([
            "tell atom Happy(alice)",
            "show individuals",
        ])
        assert result == 0

    def test_repl_rdfs_help(self):
        result = self._run_repl(["help"])
        assert result == 0

    def test_repl_rdfs_schema_range(self):
        result = self._run_repl([
            "tell schema range hasChild Person",
            "show schemas",
        ])
        assert result == 0

    def test_repl_rdfs_schema_domain(self):
        result = self._run_repl([
            "tell schema domain hasChild Parent",
            "show schemas",
        ])
        assert result == 0

    def test_repl_rdfs_schema_subproperty(self):
        result = self._run_repl([
            "tell schema subPropertyOf hasChild hasDescendant",
            "show schemas",
        ])
        assert result == 0

    def test_repl_rdfs_schema_with_annotation(self, capsys):
        result = self._run_repl([
            'tell schema subClassOf Man Mortal "All men are mortal"',
            "show schemas",
        ])
        assert result == 0
        out = capsys.readouterr().out
        assert "All men are mortal" in out
