from dataclasses import dataclass
from typing import Optional, Dict, List, Any

@dataclass
class ServerStatus:
    status: str
    service: str
    description: str
    developer: str
    system_version: str
    available_api_versions: List[str]
    recommended_api_version: str
    source_code: str
    container_registry: str
    endpoints: Dict[str, str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServerStatus":
        return cls(
            status=data["status"],
            service=data["service"],
            description=data["description"],
            developer=data["developer"],
            system_version=data["system_version"],
            available_api_versions=data["available_api_versions"],
            recommended_api_version=data["recommended_api_version"],
            source_code=data["source_code"],
            container_registry=data["container_registry"],
            endpoints=data.get("endpoints", {}),
        )

@dataclass
class Kit:
    id: str
    name: str
    theme: str
    pieces: Optional[int] = None
    year: Optional[int] = None
    age_group: Optional[str] = None
    cover_url: Optional[str] = None
    is_cover_cached: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Kit":
        return cls(
            id=data["id"],
            name=data["name"],
            theme=data["theme"],
            pieces=data.get("pieces"),
            year=data.get("year"),
            age_group=data.get("age_group"),
            cover_url=data.get("cover_url"),
            is_cover_cached=data.get("is_cover_cached", False),
        )

@dataclass
class Instruction:
    id: str
    kit_id: str
    description: str
    pdf_url: str
    size_mb: Optional[float] = None
    cover_url: Optional[str] = None
    is_pdf_cached: bool = False
    is_cover_cached: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Instruction":
        return cls(
            id=data["id"],
            kit_id=data["kit_id"],
            description=data["description"],
            pdf_url=data["pdf_url"],
            size_mb=data.get("size_mb"),
            cover_url=data.get("cover_url"),
            is_pdf_cached=data.get("is_pdf_cached", False),
            is_cover_cached=data.get("is_cover_cached", False),
        )
