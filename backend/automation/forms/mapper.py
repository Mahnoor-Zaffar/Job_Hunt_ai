"""Intelligent Field Mapper — fuzzy-matches candidate field names to form fields.

Maps canonical field names (first_name, email) to form field identifiers
by matching against name, id, label, and placeholder attributes.
"""

from difflib import SequenceMatcher
from typing import Any

FIELD_ALIASES: dict[str, list[str]] = {
    "first_name": [
        "first_name",
        "firstname",
        "first-name",
        "given_name",
        "givenname",
        "applicant_name",
        "full_name",
        "name",
        "your_name",
        "fname",
        "fn",
        "first",
        "forename",
    ],
    "last_name": [
        "last_name",
        "lastname",
        "last-name",
        "family_name",
        "familyname",
        "surname",
        "lname",
        "ln",
        "last",
    ],
    "email": [
        "email",
        "email_address",
        "emailaddress",
        "e-mail",
        "e_mail",
        "contact_email",
        "user_email",
    ],
    "phone": [
        "phone",
        "phone_number",
        "phonenumber",
        "telephone",
        "tel",
        "mobile",
        "cell",
        "contact_number",
        "contact_phone",
    ],
    "location": [
        "location",
        "city",
        "country",
        "address",
        "residence",
        "region",
    ],
    "linkedin": ["linkedin", "linkedin_url", "linkedin_profile"],
    "website": ["website", "portfolio", "github", "personal_site", "url"],
    "cover_letter": [
        "cover_letter",
        "coverletter",
        "cover",
        "additional_information",
        "message",
        "why_do_you_want",
        "tell_us",
    ],
    "resume": ["resume", "cv", "resume_upload", "cv_upload", "attach_resume"],
    "experience": ["experience", "years_of_experience", "total_experience"],
    "education": ["education", "degree", "university", "school", "college"],
    "salary": [
        "salary",
        "expected_salary",
        "salary_expectation",
        "desired_salary",
        "compensation",
    ],
    "visa": ["visa", "work_authorization", "sponsorship", "eligible_to_work"],
    "start_date": ["start_date", "available_from", "availability", "notice_period"],
    "relocate": ["relocate", "relocation", "willing_to_relocate"],
    "gender": ["gender", "sex"],
    "race": ["race", "ethnicity"],
}


class FieldMapper:
    def best_match(self, canonical_key: str, fields: list[dict[str, Any]]) -> dict[str, Any] | None:
        aliases = FIELD_ALIASES.get(canonical_key, [canonical_key])
        best_score = 0.0
        best_field: dict[str, Any] | None = None

        name_set = {a.lower().replace("_", " ").replace("-", " ") for a in aliases}

        for field in fields:
            candidates = [
                (field.get("name") or "").lower(),
                (field.get("label") or "").lower(),
                (field.get("placeholder") or "").lower(),
                (field.get("id") or "").lower(),
            ]
            combined = " ".join(c for c in candidates if c)

            for alias in name_set:
                score = SequenceMatcher(None, alias, combined).ratio()
                if alias in combined:
                    score = max(score, 0.8)
                if score > best_score:
                    best_score = score
                    best_field = field

        if best_score < 0.3:
            return None

        return {
            "selector": self._build_selector(best_field) if best_field else "",
            "field": best_field,
            "score": round(best_score, 2),
        }

    def _build_selector(self, field: dict[str, Any]) -> str:
        name = field.get("name", "")
        field_id = field.get("id", "")
        if name:
            return f"[name='{name}'], #{name}"
        if field_id:
            return f"#{field_id}"
        return "input"
