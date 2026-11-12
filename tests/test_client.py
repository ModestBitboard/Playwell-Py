import httpx
import pytest
from pathlib import Path
from playwell import (
    Playwell,
    PlaywellNotFoundError,
    PlaywellVersionError,
)


def mock_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path

    if path == "/":
        return httpx.Response(200, json={
            "status": "up",
            "service": "Playwell API",
            "description": "Test server",
            "developer": "Bitboard",
            "system_version": "1.0.2",
            "available_api_versions": ["v1"],
            "recommended_api_version": "v1",
            "source_code": "https://github.com",
            "container_registry": "ghcr.io/modestbitboard/playwell-server",
            "endpoints": {},
        })

    if path == "/v1/kits/71374":
        return httpx.Response(200, json={
            "id": "71374",
            "name": "Nintendo Entertainment System",
            "theme": "LEGO® Icons",
            "pieces": 2646,
            "year": 2020,
            "age_group": "18+",
            "is_cover_cached": True,
        })

    if path == "/v1/kits/999999":
        return httpx.Response(404, json={"detail": "Kit not found"})

    if path == "/v1/instructions/6345102/pdf":
        return httpx.Response(200, content=b"%PDF-1.4 fake pdf binary stream")

    return httpx.Response(404, json={"detail": "Not found"})


@pytest.fixture
def client():
    transport = httpx.MockTransport(mock_handler)
    with Playwell(base_url="http://testserver", transport=transport) as pw:
        yield pw


def test_handshake_and_status(client: Playwell):
    assert client.server_status.status == "up"
    assert client.server_status.system_version == "1.0.2"


def test_version_mismatch():
    def bad_version_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "status": "up",
            "service": "Playwell API",
            "description": "Test",
            "developer": "Bitboard",
            "system_version": "2.0.0",
            "available_api_versions": ["v2"],
            "recommended_api_version": "v2",
            "source_code": "https://github.com",
            "container_registry": "ghcr.io/modestbitboard/playwell-server",
            "endpoints": {},
        })

    transport = httpx.MockTransport(bad_version_handler)
    with pytest.raises(PlaywellVersionError):
        Playwell(base_url="http://testserver", transport=transport)


def test_get_kit_success(client: Playwell):
    kit = client.get_kit("71374")
    assert kit.id == "71374"
    assert kit.name == "Nintendo Entertainment System"
    assert kit.pieces == 2646


def test_get_kit_not_found(client: Playwell):
    with pytest.raises(PlaywellNotFoundError):
        client.get_kit("999999")


def test_binary_memory_and_disk_streams(client: Playwell, tmp_path: Path):
    # Test in-memory RAM fetch
    raw_bytes = client.get_instruction_pdf("6345102")
    assert raw_bytes.startswith(b"%PDF-1.4")

    # Test direct-to-disk streaming
    out_file = tmp_path / "nested" / "manual.pdf"
    saved_path = client.download_instruction_pdf("6345102", out_file)
    assert saved_path.exists()
    assert saved_path.read_bytes() == raw_bytes
