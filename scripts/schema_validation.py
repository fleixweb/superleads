#!/usr/bin/env python3
"""Local JSON Schema validation with stable same-repository reference handling.

The runtime package contains the complete ``shared/schemas`` directory.  This
module resolves only that local collection: it never fetches remote schemas or
depends on a working-directory URI.  Modern environments use ``referencing``;
older supported environments validate an equivalent in-memory local bundle.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag


class SchemaResolutionError(ValueError):
    """A local schema reference cannot be resolved from the packaged files."""


def _documents(schema_dir: Path) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for path in sorted(schema_dir.glob("*.schema.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SchemaResolutionError(f"could not load local schema {path.name}: {exc}") from exc
        if not isinstance(document, dict):
            raise SchemaResolutionError(f"local schema {path.name} must be an object")
        documents[path.name] = document
    return documents


def _pointer_exists(document: dict[str, Any], fragment: str, reference: str, origin: str) -> None:
    if not fragment:
        return
    if not fragment.startswith("/"):
        raise SchemaResolutionError(f"unsupported local JSON Schema reference {reference!r} in {origin}")
    current: Any = document
    for token in fragment[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise SchemaResolutionError(f"could not resolve local JSON Schema reference {reference!r} in {origin}")


def _target_for_reference(
    reference: str,
    *,
    origin: str,
    documents: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    target, fragment = urldefrag(reference)
    target_name = origin if not target else Path(target).name
    if target_name not in documents:
        raise SchemaResolutionError(f"local JSON Schema reference {reference!r} in {origin} is not packaged")
    _pointer_exists(documents[target_name], fragment, reference, origin)
    return target_name, fragment


def _rewrite_references(
    value: Any,
    *,
    origin: str,
    root_name: str,
    documents: dict[str, dict[str, Any]],
) -> Any:
    if isinstance(value, list):
        return [
            _rewrite_references(item, origin=origin, root_name=root_name, documents=documents)
            for item in value
        ]
    if not isinstance(value, dict):
        return value
    rewritten: dict[str, Any] = {}
    for key, item in value.items():
        if key == "$ref" and isinstance(item, str):
            target_name, fragment = _target_for_reference(item, origin=origin, documents=documents)
            if target_name == root_name:
                rewritten[key] = f"#{fragment}" if fragment else "#"
            else:
                rewritten[key] = f"#/$defs/_superleads_local_schemas/{target_name}{fragment}"
        else:
            rewritten[key] = _rewrite_references(item, origin=origin, root_name=root_name, documents=documents)
    return rewritten


def _bundled_schema(schema_path: Path) -> dict[str, Any]:
    schema_path = schema_path.resolve()
    documents = _documents(schema_path.parent)
    root_name = schema_path.name
    if root_name not in documents:
        raise SchemaResolutionError(f"local schema {root_name} is not available")
    root = _rewrite_references(deepcopy(documents[root_name]), origin=root_name, root_name=root_name, documents=documents)
    root_defs = root.get("$defs")
    if not isinstance(root_defs, dict):
        root_defs = {}
        root["$defs"] = root_defs
    bundled: dict[str, Any] = {}
    for name, document in documents.items():
        if name == root_name:
            continue
        local = deepcopy(document)
        # Embedded resources must not reset the local reference base with their
        # original $id. Their refs are rewritten to the bundle paths below.
        local.pop("$id", None)
        local.pop("$schema", None)
        bundled[name] = _rewrite_references(local, origin=name, root_name=root_name, documents=documents)
    root_defs["_superleads_local_schemas"] = bundled
    return root


def _modern_validator(schema_path: Path) -> Any:
    """Build a Draft 2020-12 validator backed by a local referencing registry."""
    import jsonschema  # type: ignore
    from referencing import Registry, Resource  # type: ignore
    from referencing.jsonschema import DRAFT202012  # type: ignore

    documents = _documents(schema_path.parent)
    root = documents.get(schema_path.name)
    if root is None:
        raise SchemaResolutionError(f"local schema {schema_path.name} is not available")
    registry = Registry()
    for name, document in documents.items():
        resource = Resource.from_contents(document, default_specification=DRAFT202012)
        registry = registry.with_resource((schema_path.parent / name).resolve().as_uri(), resource)
        schema_id = document.get("$id")
        if isinstance(schema_id, str) and schema_id:
            registry = registry.with_resource(schema_id, resource)
    try:
        return jsonschema.Draft202012Validator(root, registry=registry)
    except Exception as exc:
        raise SchemaResolutionError(f"could not initialize local schema registry for {schema_path.name}: {exc}") from exc


def _validator(schema_path: Path) -> Any:
    try:
        return _modern_validator(schema_path)
    except ModuleNotFoundError as exc:
        if exc.name != "referencing":
            raise
    except ImportError:
        pass
    try:
        import jsonschema  # type: ignore
    except ImportError as exc:
        raise SchemaResolutionError(
            f"jsonschema is unavailable: {exc}; prepare the supported dependencies from the bundled requirements.txt "
            "before deterministic validation, or follow the no-script path and mark 本环境未运行确定性校验; "
            "do not modify the user's system environment, install packages globally, or borrow another application's interpreter"
        ) from exc
    # jsonschema <= 4.10 predates ``referencing.Registry``. The bundle makes
    # every external repository reference a verified local pointer, avoiding
    # the deprecated RefResolver and working-directory-dependent URI stores.
    try:
        return jsonschema.Draft202012Validator(_bundled_schema(schema_path))
    except SchemaResolutionError:
        raise
    except Exception as exc:
        raise SchemaResolutionError(f"could not initialize local schema bundle for {schema_path.name}: {exc}") from exc


def _error_path(error: Any) -> str:
    parts = list(getattr(error, "absolute_path", ()))
    return "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in parts).lstrip(".") or "$"


def schema_validation_errors(instance: Any, schema_path: str | Path) -> list[dict[str, Any]]:
    """Return deterministic local-schema errors or raise a resolution failure."""
    resolved_path = Path(schema_path).resolve()
    validator = _validator(resolved_path)
    try:
        errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    except Exception as exc:
        raise SchemaResolutionError(f"schema validation could not resolve a local reference for {resolved_path.name}: {exc}") from exc
    return [
        {
            "kind": "schema_validation_failed",
            "path": _error_path(error),
            "message": error.message,
            "validator": getattr(error, "validator", None),
        }
        for error in errors
    ]
