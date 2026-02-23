"""RDFS-specific tests for JSON output and exit codes."""

import json
import tempfile
from pathlib import Path

import pytest

from pynmms.cli.main import main


@pytest.fixture
def rdfs_base_file():
    """Create an RDFS base file with Happy(alice) |~ Good(alice)."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({
            "language": ["Happy(alice)", "Good(alice)"],
            "consequences": [
                {"antecedent": ["Happy(alice)"], "consequent": ["Good(alice)"]}
            ],
            "individuals": ["alice"],
            "concepts": ["Good", "Happy"],
            "roles": [],
            "rdfs_schemas": [],
        }, f)
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def rdfs_empty_base():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    Path(path).unlink()
    yield path
    Path(path).unlink(missing_ok=True)


class TestRDFSExitCodes:
    def test_ask_rdfs_derivable_returns_0(self, rdfs_base_file):
        rc = main(["ask", "-b", rdfs_base_file, "--rdfs", "Happy(alice) => Good(alice)"])
        assert rc == 0

    def test_ask_rdfs_not_derivable_returns_2(self, rdfs_base_file):
        rc = main(["ask", "-b", rdfs_base_file, "--rdfs", "Happy(alice) => Sad(alice)"])
        assert rc == 2


class TestRDFSAskJSON:
    def test_ask_rdfs_json_derivable(self, rdfs_base_file, capsys):
        rc = main(["ask", "-b", rdfs_base_file, "--rdfs", "--json",
                    "Happy(alice) => Good(alice)"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "DERIVABLE"

    def test_ask_rdfs_json_not_derivable(self, rdfs_base_file, capsys):
        rc = main(["ask", "-b", rdfs_base_file, "--rdfs", "--json",
                    "Happy(alice) => Sad(alice)"])
        assert rc == 2
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "NOT_DERIVABLE"


class TestRDFSTellJSON:
    def test_tell_rdfs_json_atom(self, rdfs_empty_base, capsys):
        rc = main(["tell", "-b", rdfs_empty_base, "--create", "--rdfs", "--json",
                    "atom hasChild(alice,bob)"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["action"] == "added_atom"
        assert data["atom"] == "hasChild(alice,bob)"

    def test_tell_rdfs_json_consequence(self, rdfs_empty_base, capsys):
        rc = main(["tell", "-b", rdfs_empty_base, "--create", "--rdfs", "--json",
                    "Happy(alice) |~ Good(alice)"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["action"] == "added_consequence"


class TestRDFSBatch:
    def test_tell_rdfs_batch(self, rdfs_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write('atom Happy(alice) "Alice is happy"\n')
            f.write("atom hasChild(alice,bob)\n")
            f.write("Happy(alice) |~ Good(alice)\n")
            f.write("schema subClassOf Man Mortal\n")
            f.write("schema range hasChild Person\n")
            batch_path = f.name

        try:
            rc = main(["tell", "-b", rdfs_empty_base, "--create", "--rdfs",
                        "--batch", batch_path])
            assert rc == 0

            with open(rdfs_empty_base) as bf:
                data = json.load(bf)
            assert "Happy(alice)" in data["language"]
            assert "hasChild(alice,bob)" in data["language"]
            assert len(data["consequences"]) == 1
            assert len(data["rdfs_schemas"]) == 2
            assert data["annotations"]["Happy(alice)"] == "Alice is happy"
        finally:
            Path(batch_path).unlink(missing_ok=True)

    def test_tell_rdfs_batch_json(self, rdfs_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("atom Happy(alice)\n")
            f.write("Happy(alice) |~ Good(alice)\n")
            batch_path = f.name

        try:
            rc = main(["tell", "-b", rdfs_empty_base, "--create", "--rdfs",
                        "--json", "--batch", batch_path])
            assert rc == 0
            out = capsys.readouterr().out
            lines = [line for line in out.strip().split("\n") if line]
            assert len(lines) == 2
            assert json.loads(lines[0])["action"] == "added_atom"
            assert json.loads(lines[1])["action"] == "added_consequence"
        finally:
            Path(batch_path).unlink(missing_ok=True)


class TestRDFSAnnotations:
    def test_rdfs_annotation_round_trip(self, rdfs_empty_base):
        main(["tell", "-b", rdfs_empty_base, "--create", "--rdfs",
              'atom Happy(alice) "Alice is happy"'])

        with open(rdfs_empty_base) as f:
            data = json.load(f)
        assert data["annotations"]["Happy(alice)"] == "Alice is happy"

        from pynmms.rdfs.base import RDFSMaterialBase
        base = RDFSMaterialBase.from_file(rdfs_empty_base)
        assert base.annotations["Happy(alice)"] == "Alice is happy"


class TestRDFSSchemaAnnotations:
    def test_subclass_schema_annotation_json(self, rdfs_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("atom Man(socrates)\n")
            f.write('schema subClassOf Man Mortal "All men are mortal"\n')
            batch_path = f.name

        try:
            rc = main([
                "tell", "-b", rdfs_empty_base, "--create", "--rdfs", "--json",
                "--batch", batch_path,
            ])
            assert rc == 0
            out = capsys.readouterr().out
            lines = [line for line in out.strip().split("\n") if line]
            schema_line = json.loads(lines[1])
            assert schema_line["action"] == "registered_subClassOf_schema"
            assert schema_line["annotation"] == "All men are mortal"

            with open(rdfs_empty_base) as bf:
                data = json.load(bf)
            assert len(data["rdfs_schemas"]) == 1
            assert data["rdfs_schemas"][0]["annotation"] == "All men are mortal"
        finally:
            Path(batch_path).unlink(missing_ok=True)

    def test_range_schema_annotation_json(self, rdfs_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("atom hasChild(alice,bob)\n")
            f.write('schema range hasChild Person "Children are persons"\n')
            batch_path = f.name

        try:
            rc = main([
                "tell", "-b", rdfs_empty_base, "--create", "--rdfs", "--json",
                "--batch", batch_path,
            ])
            assert rc == 0
            out = capsys.readouterr().out
            lines = [line for line in out.strip().split("\n") if line]
            schema_line = json.loads(lines[1])
            assert schema_line["action"] == "registered_range_schema"
            assert schema_line["annotation"] == "Children are persons"

            with open(rdfs_empty_base) as bf:
                data = json.load(bf)
            assert data["rdfs_schemas"][0]["annotation"] == "Children are persons"
        finally:
            Path(batch_path).unlink(missing_ok=True)

    def test_schema_annotation_round_trip(self, rdfs_empty_base):
        """Save with annotation, load, verify annotation preserved."""
        from pynmms.rdfs.base import RDFSMaterialBase

        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass(
            "Man", "Mortal",
            annotation="All men are mortal",
        )
        base.to_file(rdfs_empty_base)

        restored = RDFSMaterialBase.from_file(rdfs_empty_base)
        assert len(restored._rdfs_schemas) == 1
        assert restored._rdfs_schemas[0][3] == "All men are mortal"

    def test_schema_without_annotation_omits_field(self, rdfs_empty_base):
        """Schema without annotation should not have 'annotation' key in JSON."""
        from pynmms.rdfs.base import RDFSMaterialBase

        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        base.to_file(rdfs_empty_base)

        with open(rdfs_empty_base) as f:
            data = json.load(f)
        assert "annotation" not in data["rdfs_schemas"][0]
