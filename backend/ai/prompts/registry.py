"""Prompt registry — versioned prompt library.

Prompts are stored as versioned templates with metadata.  Each
version is immutable once published.  New versions can be created
by incrementing the version number.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from string import Template
from typing import Any


@dataclass
class PromptVersion:
    version: int
    template: str
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    variables: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class Prompt:
    name: str
    description: str = ""
    category: str = "general"
    versions: list[PromptVersion] = field(default_factory=list)

    @property
    def latest(self) -> PromptVersion:
        if not self.versions:
            raise ValueError(f"Prompt '{self.name}' has no versions")
        return self.versions[-1]

    def get_version(self, version: int) -> PromptVersion | None:
        for v in self.versions:
            if v.version == version:
                return v
        return None

    def render(self, variables: dict[str, str] | None = None, version: int | None = None) -> str:
        pv = self.get_version(version) if version else self.latest
        if pv is None:
            raise ValueError(f"Version {version} not found for prompt '{self.name}'")
        tmpl = Template(pv.template)
        try:
            return tmpl.safe_substitute(**(variables or {}))
        except KeyError as exc:
            raise ValueError(f"Missing variable in prompt '{self.name}': {exc}") from exc


class PromptRegistry:
    def __init__(self) -> None:
        self._prompts: dict[str, Prompt] = {}

    def register(self, prompt: Prompt) -> None:
        if prompt.name in self._prompts:
            existing = self._prompts[prompt.name]
            existing.versions.extend(prompt.versions)
            existing.versions.sort(key=lambda v: v.version)
        else:
            self._prompts[prompt.name] = prompt

    def get(self, name: str) -> Prompt | None:
        return self._prompts.get(name)

    def render(
        self, name: str, variables: dict[str, str] | None = None, version: int | None = None
    ) -> str:
        prompt = self.get(name)
        if prompt is None:
            raise ValueError(f"Prompt '{name}' not found in registry")
        return prompt.render(variables, version)

    def list_names(self) -> list[str]:
        return sorted(self._prompts.keys())

    def list_by_category(self, category: str) -> list[Prompt]:
        return [p for p in self._prompts.values() if p.category == category]

    def add_version(
        self, name: str, template: str, description: str = "", **meta: Any
    ) -> PromptVersion:
        prompt = self.get(name)
        if prompt is None:
            prompt = Prompt(name=name)
            self._prompts[name] = prompt

        new_version = len(prompt.versions) + 1
        pv = PromptVersion(
            version=new_version,
            template=template,
            description=description,
            tags=meta.get("tags", []),
        )
        pv.variables = _extract_variables(template)
        prompt.versions.append(pv)
        return pv


def _extract_variables(template: str) -> list[str]:
    import re

    return sorted(set(re.findall(r"\$(\w+)", template)))
