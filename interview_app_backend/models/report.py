from dataclasses import dataclass, field


@dataclass(slots=True)
class Report:
    title: str = ""
    content: str = ""
    filename: str = ""
    mime_type: str = "application/json"
    sections: list[str] = field(default_factory=list)
