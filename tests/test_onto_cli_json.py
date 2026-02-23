"""Onto-specific tests for JSON output and exit codes."""

import json
import tempfile
from pathlib import Path

import pytest

from pynmms.cli.main import main


@pytest.fixture
def onto_base_file():
    """Create an ontology base file with Happy(alice) |~ Good(alice)."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({
            "language": ["Happy(alice)", "Good(alice)"],
            "consequences": [
                {"antecedent": ["Happy(alice)"], "consequent": ["Good(alice)"]}
            ],
            "individuals": ["alice"],
            "concepts": ["Good", "Happy"],
            "roles": [],
            "onto_schemas": [],
        }, f)
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def onto_empty_base():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    Path(path).unlink()
    yield path
    Path(path).unlink(missing_ok=True)


class TestOntoExitCodes:
    def test_ask_onto_derivable_returns_0(self, onto_base_file):
        rc = main(["ask", "-b", onto_base_file, "--onto", "Happy(alice) => Good(alice)"])
        assert rc == 0

    def test_ask_onto_not_derivable_returns_2(self, onto_base_file):
        rc = main(["ask", "-b", onto_base_file, "--onto", "Happy(alice) => Sad(alice)"])
        assert rc == 2


class TestOntoAskJSON:
    def test_ask_onto_json_derivable(self, onto_base_file, capsys):
        rc = main(["ask", "-b", onto_base_file, "--onto", "--json",
                    "Happy(alice) => Good(alice)"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "DERIVABLE"

    def test_ask_onto_json_not_derivable(self, onto_base_file, capsys):
        rc = main(["ask", "-b", onto_base_file, "--onto", "--json",
                    "Happy(alice) => Sad(alice)"])
        assert rc == 2
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "NOT_DERIVABLE"


class TestOntoTellJSON:
    def test_tell_onto_json_atom(self, onto_empty_base, capsys):
        rc = main(["tell", "-b", onto_empty_base, "--create", "--onto", "--json",
                    "atom hasChild(alice,bob)"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["action"] == "added_atom"
        assert data["atom"] == "hasChild(alice,bob)"

    def test_tell_onto_json_consequence(self, onto_empty_base, capsys):
        rc = main(["tell", "-b", onto_empty_base, "--create", "--onto", "--json",
                    "Happy(alice) |~ Good(alice)"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["action"] == "added_consequence"


class TestOntoBatch:
    def test_tell_onto_batch(self, onto_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write('atom Happy(alice) "Alice is happy"\n')
            f.write("atom hasChild(alice,bob)\n")
            f.write("Happy(alice) |~ Good(alice)\n")
            f.write("schema subClassOf Man Mortal\n")
            f.write("schema range hasChild Person\n")
            batch_path = f.name

        try:
            rc = main(["tell", "-b", onto_empty_base, "--create", "--onto",
                        "--batch", batch_path])
            assert rc == 0

            with open(onto_empty_base) as bf:
                data = json.load(bf)
            assert "Happy(alice)" in data["language"]
            assert "hasChild(alice,bob)" in data["language"]
            assert len(data["consequences"]) == 1
            assert len(data["onto_schemas"]) == 2
            assert data["annotations"]["Happy(alice)"] == "Alice is happy"
        finally:
            Path(batch_path).unlink(missing_ok=True)

    def test_tell_onto_batch_json(self, onto_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("atom Happy(alice)\n")
            f.write("Happy(alice) |~ Good(alice)\n")
            batch_path = f.name

        try:
            rc = main(["tell", "-b", onto_empty_base, "--create", "--onto",
                        "--json", "--batch", batch_path])
            assert rc == 0
            out = capsys.readouterr().out
            lines = [line for line in out.strip().split("\n") if line]
            assert len(lines) == 2
            assert json.loads(lines[0])["action"] == "added_atom"
            assert json.loads(lines[1])["action"] == "added_consequence"
        finally:
            Path(batch_path).unlink(missing_ok=True)


class TestOntoBatchDisjoint:
    def test_tell_onto_batch_disjoint_with(self, onto_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("atom Man(socrates)\n")
            f.write("atom Woman(socrates)\n")
            f.write("schema disjointWith Man Woman\n")
            batch_path = f.name

        try:
            rc = main(["tell", "-b", onto_empty_base, "--create", "--onto",
                        "--batch", batch_path])
            assert rc == 0

            with open(onto_empty_base) as bf:
                data = json.load(bf)
            assert len(data["onto_schemas"]) == 1
            assert data["onto_schemas"][0]["type"] == "disjointWith"
        finally:
            Path(batch_path).unlink(missing_ok=True)

    def test_tell_onto_batch_disjoint_properties(self, onto_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("atom hasChild(alice,bob)\n")
            f.write("atom hasParent(alice,bob)\n")
            f.write("schema disjointProperties hasChild hasParent\n")
            batch_path = f.name

        try:
            rc = main(["tell", "-b", onto_empty_base, "--create", "--onto",
                        "--batch", batch_path])
            assert rc == 0

            with open(onto_empty_base) as bf:
                data = json.load(bf)
            assert len(data["onto_schemas"]) == 1
            assert data["onto_schemas"][0]["type"] == "disjointProperties"
        finally:
            Path(batch_path).unlink(missing_ok=True)

    def test_tell_onto_batch_disjoint_with_json(self, onto_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("atom Man(socrates)\n")
            f.write('schema disjointWith Man Woman "Disjoint concepts"\n')
            batch_path = f.name

        try:
            rc = main(["tell", "-b", onto_empty_base, "--create", "--onto",
                        "--json", "--batch", batch_path])
            assert rc == 0
            out = capsys.readouterr().out
            lines = [line for line in out.strip().split("\n") if line]
            schema_line = json.loads(lines[1])
            assert schema_line["action"] == "registered_disjointWith_schema"
            assert schema_line["annotation"] == "Disjoint concepts"
        finally:
            Path(batch_path).unlink(missing_ok=True)


class TestOntoAnnotations:
    def test_onto_annotation_round_trip(self, onto_empty_base):
        main(["tell", "-b", onto_empty_base, "--create", "--onto",
              'atom Happy(alice) "Alice is happy"'])

        with open(onto_empty_base) as f:
            data = json.load(f)
        assert data["annotations"]["Happy(alice)"] == "Alice is happy"

        from pynmms.onto.base import OntoMaterialBase
        base = OntoMaterialBase.from_file(onto_empty_base)
        assert base.annotations["Happy(alice)"] == "Alice is happy"


class TestOntoSchemaAnnotations:
    def test_subclass_schema_annotation_json(self, onto_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("atom Man(socrates)\n")
            f.write('schema subClassOf Man Mortal "All men are mortal"\n')
            batch_path = f.name

        try:
            rc = main([
                "tell", "-b", onto_empty_base, "--create", "--onto", "--json",
                "--batch", batch_path,
            ])
            assert rc == 0
            out = capsys.readouterr().out
            lines = [line for line in out.strip().split("\n") if line]
            schema_line = json.loads(lines[1])
            assert schema_line["action"] == "registered_subClassOf_schema"
            assert schema_line["annotation"] == "All men are mortal"

            with open(onto_empty_base) as bf:
                data = json.load(bf)
            assert len(data["onto_schemas"]) == 1
            assert data["onto_schemas"][0]["annotation"] == "All men are mortal"
        finally:
            Path(batch_path).unlink(missing_ok=True)

    def test_range_schema_annotation_json(self, onto_empty_base, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("atom hasChild(alice,bob)\n")
            f.write('schema range hasChild Person "Children are persons"\n')
            batch_path = f.name

        try:
            rc = main([
                "tell", "-b", onto_empty_base, "--create", "--onto", "--json",
                "--batch", batch_path,
            ])
            assert rc == 0
            out = capsys.readouterr().out
            lines = [line for line in out.strip().split("\n") if line]
            schema_line = json.loads(lines[1])
            assert schema_line["action"] == "registered_range_schema"
            assert schema_line["annotation"] == "Children are persons"

            with open(onto_empty_base) as bf:
                data = json.load(bf)
            assert data["onto_schemas"][0]["annotation"] == "Children are persons"
        finally:
            Path(batch_path).unlink(missing_ok=True)

    def test_schema_annotation_round_trip(self, onto_empty_base):
        """Save with annotation, load, verify annotation preserved."""
        from pynmms.onto.base import OntoMaterialBase

        base = OntoMaterialBase(language={"Man(socrates)"})
        base.register_subclass(
            "Man", "Mortal",
            annotation="All men are mortal",
        )
        base.to_file(onto_empty_base)

        restored = OntoMaterialBase.from_file(onto_empty_base)
        assert len(restored._onto_schemas) == 1
        assert restored._onto_schemas[0][3] == "All men are mortal"

    def test_schema_without_annotation_omits_field(self, onto_empty_base):
        """Schema without annotation should not have 'annotation' key in JSON."""
        from pynmms.onto.base import OntoMaterialBase

        base = OntoMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        base.to_file(onto_empty_base)

        with open(onto_empty_base) as f:
            data = json.load(f)
        assert "annotation" not in data["onto_schemas"][0]
