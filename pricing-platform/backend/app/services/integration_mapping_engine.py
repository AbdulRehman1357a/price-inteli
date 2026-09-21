import re
from decimal import Decimal, InvalidOperation
from typing import Any

from app.models.integration_mapping import IntegrationMapping


class TransformationError(Exception):
    """A transformation_rule couldn't be applied to a specific value —
    caught per-record by the caller so one bad row doesn't abort a sync.
    """


def apply_transformation(value: Any, rule: str | None) -> Any:
    """A small, fixed set of transforms — deliberately not a full
    expression language, matching the mapping UI's "Source Field ->
    Canonical Field -> Transformation" as a simple three-column table
    rather than a scripting surface. Unknown rules pass the value through
    unchanged rather than failing, since a typo'd rule shouldn't block an
    otherwise-valid mapping.
    """
    if value is None or rule in (None, "", "direct"):
        return value
    if rule == "uppercase":
        return str(value).upper()
    if rule == "lowercase":
        return str(value).lower()
    if rule == "trim":
        return str(value).strip()
    if rule.startswith("multiply:"):
        try:
            factor = Decimal(rule.split(":", 1)[1])
            return Decimal(str(value)) * factor
        except (InvalidOperation, ValueError) as exc:
            raise TransformationError(f"Could not apply {rule!r} to {value!r}.") from exc
    if rule.startswith("default:"):
        fallback = rule.split(":", 1)[1]
        return value if str(value).strip() else fallback
    return value


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def apply_validation(value: Any, rule: str | None, *, field_label: str) -> None:
    """The Field Mapping Engine's validation column (Phase 10 upgrade
    spec section 17) — a second, deliberately small mini-DSL alongside
    transformation_rule. Currently only "regex:<pattern>" is recognized;
    an unrecognized rule is a no-op rather than a failure, same
    backward-compatible philosophy as apply_transformation's unknown-rule
    passthrough (a typo'd rule shouldn't block an otherwise-valid mapping).
    """
    if value is None or not rule:
        return
    if rule.startswith("regex:"):
        pattern = rule.split(":", 1)[1]
        if re.fullmatch(pattern, str(value)) is None:
            raise TransformationError(f"{field_label!r} value {value!r} does not match pattern {pattern!r}.")


def map_record(raw_record: dict[str, Any], mappings: list[IntegrationMapping]) -> dict[str, Any]:
    """Applies one entity_type's mapping rules to one raw external record,
    producing a dict keyed by canonical_field — the input to a
    Canonical* Pydantic model (app/schemas/canonical.py).

    Order per field: fall back to default_value when the raw value is
    blank -> enforce required -> apply_transformation -> apply_validation.
    """
    result: dict[str, Any] = {}
    for mapping in mappings:
        raw_value = raw_record.get(mapping.source_field)
        if _is_blank(raw_value) and mapping.default_value is not None:
            raw_value = mapping.default_value
        if mapping.required and _is_blank(raw_value):
            raise TransformationError(f"{mapping.source_field!r} is required but was missing or blank.")

        value = apply_transformation(raw_value, mapping.transformation_rule)
        apply_validation(value, mapping.validation_rule, field_label=mapping.source_field)
        result[mapping.canonical_field] = value
    return result
