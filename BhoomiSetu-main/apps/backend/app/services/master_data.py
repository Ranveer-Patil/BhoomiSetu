import re

PROJECT_TYPES = ("Highway", "Railway", "Irrigation", "Industrial", "Urban", "Other")
DOCUMENT_TYPES = {
    "land_record": ["owner_name", "khasra_survey_number", "area_hectares"],
    "sale_deed": ["owner_name", "khasra_survey_number", "document_date"],
    "identity_proof": ["owner_name"],
    "award_notice": ["khasra_survey_number", "document_date"],
    "other": ["document_type"],
}
GRIEVANCE_CATEGORIES = ("compensation", "ownership", "measurement", "rehabilitation", "process")


def validate_survey_number(value: str) -> str:
    value = value.strip()
    # Unicode letters/digits support local scripts; this is not cadastral verification.
    if not re.fullmatch(r"[\w]+(?:[ ./-][\w]+)*", value) or len(value) > 100:
        raise ValueError("Use letters or numbers separated by spaces, slash, dot or hyphen")
    return value


def missing_document_fields(document_type: str, fields: dict) -> list[str]:
    return [name for name in DOCUMENT_TYPES[document_type] if fields.get(name) in (None, "")]
