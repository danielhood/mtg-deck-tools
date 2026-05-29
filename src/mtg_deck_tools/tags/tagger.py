"""Apply mechanic taxonomy matchers to cards."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Matcher:
    type: str
    pattern: str | None = None
    value: str | None = None
    compiled: re.Pattern[str] | None = None


@dataclass(frozen=True)
class TagDefinition:
    id: str
    layer: str
    description: str
    matchers: tuple[Matcher, ...]


@dataclass(frozen=True)
class TagAssignment:
    tag: str
    layer: str
    source: str


def load_taxonomy(path: Path) -> list[TagDefinition]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    tags: list[TagDefinition] = []
    for entry in data.get("tags", []):
        matchers: list[Matcher] = []
        for m in entry.get("matchers", []):
            mtype = m["type"]
            compiled = None
            pattern = m.get("pattern")
            if pattern and mtype in ("oracle_regex", "type_regex"):
                compiled = re.compile(pattern)
            matchers.append(
                Matcher(
                    type=mtype,
                    pattern=pattern,
                    value=m.get("value"),
                    compiled=compiled,
                )
            )
        tags.append(
            TagDefinition(
                id=entry["id"],
                layer=entry.get("layer", "theme"),
                description=entry.get("description", ""),
                matchers=tuple(matchers),
            )
        )
    return tags


class Tagger:
    def __init__(self, tags: list[TagDefinition]) -> None:
        self._tags = tags

    def tag_card(self, card: dict[str, Any]) -> list[TagAssignment]:
        type_line = card.get("type_line") or ""
        oracle_text = card.get("oracle_text") or ""
        keywords = [k.lower() for k in (card.get("keywords") or [])]
        assignments: list[TagAssignment] = []

        for tag_def in self._tags:
            for matcher in tag_def.matchers:
                if self._matches(matcher, type_line, oracle_text, keywords):
                    assignments.append(
                        TagAssignment(
                            tag=tag_def.id,
                            layer=tag_def.layer,
                            source=f"{matcher.type}:{tag_def.id}",
                        )
                    )
                    break
        return assignments

    @staticmethod
    def _matches(
        matcher: Matcher,
        type_line: str,
        oracle_text: str,
        keywords: list[str],
    ) -> bool:
        if matcher.type == "keyword" and matcher.value:
            return matcher.value.lower() in keywords
        if matcher.type == "type_regex" and matcher.compiled:
            return bool(matcher.compiled.search(type_line))
        if matcher.type == "oracle_regex" and matcher.compiled:
            return bool(matcher.compiled.search(oracle_text))
        return False
