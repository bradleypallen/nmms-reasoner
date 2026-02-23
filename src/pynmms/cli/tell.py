"""``pynmms tell`` subcommand — add atoms or consequences to a base."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from pynmms.base import MaterialBase
from pynmms.cli.exitcodes import EXIT_ERROR, EXIT_SUCCESS
from pynmms.cli.output import (
    emit_error,
    emit_json,
    tell_atom_response,
    tell_consequence_response,
)

logger = logging.getLogger(__name__)


def _parse_atom_with_annotation(rest: str) -> tuple[str, str | None]:
    """Parse ``atom_name`` or ``atom_name "description"`` after the ``atom`` keyword.

    Returns (atom_name, annotation_or_None).
    """
    rest = rest.strip()
    # Check for a quoted annotation
    # Find the first quote — everything before it is the atom name
    for quote_char in ('"', "'"):
        idx = rest.find(quote_char)
        if idx != -1:
            atom = rest[:idx].strip()
            # Extract the quoted string (find matching close quote)
            end_idx = rest.find(quote_char, idx + 1)
            if end_idx == -1:
                # Unmatched quote — treat the rest as annotation
                annotation = rest[idx + 1:].strip()
            else:
                annotation = rest[idx + 1:end_idx]
            return atom, annotation if annotation else None
    return rest, None


def _parse_tell_statement(
    statement: str,
) -> tuple[str, frozenset[str] | None, frozenset[str] | None, str | None]:
    """Parse a tell statement.

    Returns:
        ("atom", frozenset({name}), None, annotation_or_None) for ``atom X`` or ``atom X "desc"``
        ("consequence", antecedent, consequent, None) for ``A, B |~ C, D``
    """
    statement = statement.strip()

    if statement.lower().startswith("atom "):
        atom, annotation = _parse_atom_with_annotation(statement[5:])
        return ("atom", frozenset({atom}), None, annotation)

    if "|~" not in statement:
        raise ValueError(
            f"Invalid tell statement: {statement!r}. "
            f'Expected "atom X" or "A, B |~ C, D".'
        )

    parts = statement.split("|~", 1)
    antecedent_str = parts[0].strip()
    consequent_str = parts[1].strip()

    antecedent = frozenset(s.strip() for s in antecedent_str.split(",") if s.strip())
    consequent = frozenset(s.strip() for s in consequent_str.split(",") if s.strip())

    return ("consequence", antecedent, consequent, None)


def _process_tell_statement(
    statement: str,
    base: MaterialBase,
    base_path: Path,
    *,
    json_mode: bool = False,
    quiet: bool = False,
) -> int:
    """Process a single tell statement. Returns exit code."""
    try:
        kind, antecedent, consequent, annotation = _parse_tell_statement(statement)
    except ValueError as e:
        emit_error(str(e), json_mode=json_mode, quiet=quiet)
        return EXIT_ERROR

    if kind == "atom":
        assert antecedent is not None
        atom = next(iter(antecedent))
        base.add_atom(atom)
        if annotation:
            base.annotate(atom, annotation)
        if json_mode:
            emit_json(tell_atom_response(atom, str(base_path), annotation))
        elif not quiet:
            if annotation:
                print(f"Added atom: {atom} — {annotation}")
            else:
                print(f"Added atom: {atom}")
    else:
        assert antecedent is not None or consequent is not None
        ant = antecedent if antecedent else frozenset()
        con = consequent if consequent else frozenset()
        base.add_consequence(ant, con)
        if json_mode:
            emit_json(tell_consequence_response(ant, con, str(base_path)))
        elif not quiet:
            print(f"Added consequence: {set(ant)} |~ {set(con)}")

    return EXIT_SUCCESS


def run_tell(args: argparse.Namespace) -> int:
    """Execute the ``tell`` subcommand."""
    base_path = Path(args.base)
    rdfs_mode = getattr(args, "rdfs", False)
    json_mode = getattr(args, "json", False)
    quiet = getattr(args, "quiet", False)
    batch = getattr(args, "batch", None)
    base: MaterialBase

    if rdfs_mode:
        from pynmms.rdfs.base import RDFSMaterialBase

        if base_path.exists():
            base = RDFSMaterialBase.from_file(base_path)
        elif args.create:
            base = RDFSMaterialBase()
        else:
            msg = f"Base file {base_path} does not exist. Use --create to create it."
            emit_error(msg, json_mode=json_mode, quiet=quiet)
            return EXIT_ERROR
    else:
        if base_path.exists():
            base = MaterialBase.from_file(base_path)
        elif args.create:
            base = MaterialBase()
        else:
            msg = f"Base file {base_path} does not exist. Use --create to create it."
            emit_error(msg, json_mode=json_mode, quiet=quiet)
            return EXIT_ERROR

    # --- Batch mode ---
    if batch is not None:
        return _run_tell_batch(batch, base, base_path, rdfs_mode=rdfs_mode,
                               json_mode=json_mode, quiet=quiet)

    # --- Single statement ---
    statement = args.statement
    if statement is None:
        emit_error("No statement provided.", json_mode=json_mode, quiet=quiet)
        return EXIT_ERROR
    if statement == "-":
        statement = sys.stdin.readline().rstrip("\n")

    rc = _process_tell_statement(statement, base, base_path,
                                 json_mode=json_mode, quiet=quiet)
    if rc == EXIT_SUCCESS:
        base.to_file(base_path)
        logger.info("Saved base to %s", base_path)
    return rc


def _run_tell_batch(
    batch_source: str,
    base: MaterialBase,
    base_path: Path,
    *,
    rdfs_mode: bool = False,
    json_mode: bool = False,
    quiet: bool = False,
) -> int:
    """Process a batch file of tell statements."""
    if batch_source == "-":
        lines = sys.stdin.read().splitlines()
    else:
        try:
            with open(batch_source) as f:
                lines = f.read().splitlines()
        except OSError as e:
            emit_error(str(e), json_mode=json_mode, quiet=quiet)
            return EXIT_ERROR

    had_error = False
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # RDFS schema lines
        if rdfs_mode and line.startswith("schema "):
            from pynmms.rdfs.base import RDFSMaterialBase
            assert isinstance(base, RDFSMaterialBase)
            rc = _process_rdfs_schema_line(line, base, base_path,
                                           json_mode=json_mode, quiet=quiet)
            if rc != EXIT_SUCCESS:
                had_error = True
            continue

        rc = _process_tell_statement(line, base, base_path,
                                     json_mode=json_mode, quiet=quiet)
        if rc != EXIT_SUCCESS:
            had_error = True

    base.to_file(base_path)
    logger.info("Saved base to %s (batch)", base_path)
    return EXIT_ERROR if had_error else EXIT_SUCCESS


def _extract_trailing_annotation(text: str) -> tuple[str, str | None]:
    """Extract an optional trailing quoted annotation from *text*.

    Returns (remaining_text, annotation_or_None).
    """
    for quote_char in ('"', "'"):
        idx = text.find(quote_char)
        if idx != -1:
            end_idx = text.find(quote_char, idx + 1)
            if end_idx == -1:
                annotation = text[idx + 1:].strip()
            else:
                annotation = text[idx + 1:end_idx]
            remaining = text[:idx].strip()
            return remaining, annotation if annotation else None
    return text, None


def _process_rdfs_schema_line(
    line: str,
    base: object,
    base_path: Path,
    *,
    json_mode: bool = False,
    quiet: bool = False,
) -> int:
    """Process an RDFS schema line like ``schema subClassOf Man Mortal``."""
    from pynmms.cli.output import emit_json, tell_schema_response
    from pynmms.rdfs.base import RDFSMaterialBase

    assert isinstance(base, RDFSMaterialBase)

    # Extract optional trailing quoted annotation
    body, annotation = _extract_trailing_annotation(line)
    parts = body.split()

    try:
        if len(parts) >= 4 and parts[1] == "subClassOf":
            _, _, sub_concept, super_concept = parts[:4]
            base.register_subclass(sub_concept, super_concept, annotation=annotation)
            details = f"{{{sub_concept}(x)}} |~ {{{super_concept}(x)}}"
            if json_mode:
                emit_json(tell_schema_response(
                    "subClassOf", details, str(base_path), annotation=annotation))
            elif not quiet:
                msg = f"Registered subClassOf schema: {details}"
                if annotation:
                    msg += f" \u2014 {annotation}"
                print(msg)
            return EXIT_SUCCESS
        elif len(parts) >= 4 and parts[1] == "range":
            _, _, role, concept = parts[:4]
            base.register_range(role, concept, annotation=annotation)
            details = f"{{{role}(x,y)}} |~ {{{concept}(y)}}"
            if json_mode:
                emit_json(tell_schema_response(
                    "range", details, str(base_path), annotation=annotation))
            elif not quiet:
                msg = f"Registered range schema: {details}"
                if annotation:
                    msg += f" \u2014 {annotation}"
                print(msg)
            return EXIT_SUCCESS
        elif len(parts) >= 4 and parts[1] == "domain":
            _, _, role, concept = parts[:4]
            base.register_domain(role, concept, annotation=annotation)
            details = f"{{{role}(x,y)}} |~ {{{concept}(x)}}"
            if json_mode:
                emit_json(tell_schema_response(
                    "domain", details, str(base_path), annotation=annotation))
            elif not quiet:
                msg = f"Registered domain schema: {details}"
                if annotation:
                    msg += f" \u2014 {annotation}"
                print(msg)
            return EXIT_SUCCESS
        elif len(parts) >= 4 and parts[1] == "subPropertyOf":
            _, _, sub_role, super_role = parts[:4]
            base.register_subproperty(sub_role, super_role, annotation=annotation)
            details = f"{{{sub_role}(x,y)}} |~ {{{super_role}(x,y)}}"
            if json_mode:
                emit_json(tell_schema_response(
                    "subPropertyOf", details, str(base_path), annotation=annotation))
            elif not quiet:
                msg = f"Registered subPropertyOf schema: {details}"
                if annotation:
                    msg += f" \u2014 {annotation}"
                print(msg)
            return EXIT_SUCCESS
        else:
            emit_error(f"Invalid schema line: {line!r}", json_mode=json_mode, quiet=quiet)
            return EXIT_ERROR
    except (IndexError, ValueError) as e:
        emit_error(str(e), json_mode=json_mode, quiet=quiet)
        return EXIT_ERROR
