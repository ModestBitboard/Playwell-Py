import os
import httpx
from pathlib import Path
from typing import Optional, Dict, List, Any, Iterator, Union

from playwell.exceptions import (
    PlaywellConnectionError,
    PlaywellError,
    PlaywellVersionError,
    PlaywellNotFoundError,
    PlaywellAPIError,
)
from playwell.models import (
    ServerStatus,
    Kit,
    Instruction,
)

DEFAULT_SERVER_URL = "https://playwell.bitboard.ca"

class Playwell:
    def __init__(
            self,
            base_url: Optional[str] = None,
            timeout: float = 15.0,
            verify_version: bool = True,
            transport: Optional[httpx.BaseTransport] = None,
    ):
        resolved_url = base_url or os.getenv('PLAYWELL_SERVER_URL') or DEFAULT_SERVER_URL
        self.base_url = resolved_url.rstrip('/')
        self.api_version = "v1"
        self._server_status: Optional[ServerStatus] = None

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"User-Agent": "playwell-py/1.0.0"},  # remember to adjust version number for each release!
            follow_redirects=True,
            transport=transport,
        )

        if verify_version:
            self._check_compatibility()


    # --- META ---

    @property
    def server_status(self) -> ServerStatus:
        """Returns the cached ServerStatus, fetching it automatically if not yet populated."""
        if self._server_status is None:
            return self.get_status()
        return self._server_status

    def get_status(self) -> ServerStatus:
        """Fetches the latest server status handshake and updates self.server_status."""
        try:
            response = self._client.get("/")
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PlaywellConnectionError(
                f"Failed to connect to Playwell server at {self.base_url}: {exc}"
            ) from exc

        try:
            status = ServerStatus.from_dict(data)
        except KeyError as exc:
            raise PlaywellError(
                f"Invalid handshake response from server: {self.base_url}. Is this a Playwell server?"
            ) from exc

        self._server_status = status
        return status

    def _check_compatibility(self):
        """Verifies server connection and checks if API version is supported."""
        try:
            status = self.get_status()
        except PlaywellConnectionError:
            self.close()
            raise

        if self.api_version not in status.available_api_versions:
            self.close()
            raise PlaywellVersionError(
                f"Server at {self.base_url} does not support API '{self.api_version}'. "
                f"Supported versions: {', '.join(status.available_api_versions)}"
            )

    def close(self) -> None:
        """Closes the underlying HTTP connection pool."""
        self._client.close()


    # --- ENTER/EXIT ---

    def __enter__(self) -> "Playwell":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


    # --- HELPERS ---

    def _get_json(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> dict:
        """
        Internal helper for GET requests expecting JSON payloads.
        Strips None values from query params. and maps HTTP errors to SDK exceptions.
        """
        clean_params = {k: v for k, v in params.items() if v is not None} if params else None
        url = f"/{self.api_version}/{endpoint.lstrip('/')}"

        try:
            response = self._client.get(url, params=clean_params)
        except httpx.RequestError as exc:
            raise PlaywellConnectionError(f"Network error communicating with {self.base_url}: {exc}") from exc

        if response.status_code == 404:
            detail = response.json().get("detail", "Resource Not Found.")
            raise PlaywellNotFoundError(detail)

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise PlaywellAPIError(response.status_code, detail)

        return response.json()

    def _stream_bytes(self, endpoint: str, chunk_size: int = 8192) -> Iterator[bytes]:
        """
        Internal generator that yields raw byte chunks from a binary endpoint.
        """
        url = f"/{self.api_version}/{endpoint.lstrip('/')}"

        try:
            with self._client.stream("GET", url) as response:
                if response.status_code == 404:
                    response.read()
                    detail = response.json().get("detail", "Asset not found.")
                    raise PlaywellNotFoundError(detail)

                if response.status_code >= 400:
                    response.read()
                    try:
                        detail = response.json().get("detail", response.text)
                    except ValueError:
                        detail = response.text
                    raise PlaywellAPIError(response.status_code, detail)

                for chunk in response.iter_bytes(chunk_size=chunk_size):
                    yield chunk

        except httpx.RequestError as exc:
            raise PlaywellConnectionError(
                f"Network error streaming asset from {self.base_url}: {exc}"
            ) from exc

    def _get_bytes(self, endpoint: str) -> bytes:
        """Fetches a binary asset from endpoint."""
        return b"".join(self._stream_bytes(endpoint))

    def _download_file(self, endpoint: str, dest_path: Union[str, Path]) -> Path:
        """Streams a binary asset directly to disk without buffering the whole file in memory."""
        target = Path(dest_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        with target.open(mode="wb") as f:
            for chunk in self._stream_bytes(endpoint):
                f.write(chunk)

        return target


    # --- DATA ENDPOINTS ---

    def get_kit(self, kit_id: str) -> Kit:
        """Fetches metadata for a specific LEGO kit ID (scrapes server-side if uncached)."""
        data = self._get_json(f"kits/{kit_id}")
        return Kit.from_dict(data)

    def search_kits(
        self,
        search: Optional[str] = None,
        name: Optional[str] = None,
        theme: Optional[str] = None,
        age_group: Optional[str] = None,
    ) -> List[Kit]:
        """Queries kits matching the provided filter criteria."""
        params = {
            "search": search,
            "name": name,
            "theme": theme,
            "age_group": age_group,
        }
        data = self._get_json("kits", params=params)
        return [Kit.from_dict(item) for item in data]

    def get_kit_instructions(self, kit_id: str) -> List[Instruction]:
        """Lists all instruction booklets associated with a specific kit ID."""
        data = self._get_json(f"kits/{kit_id}/instructions")
        return [Instruction.from_dict(item) for item in data]

    def get_instruction(self, instruction_id: str) -> Instruction:
        """Fetches metadata for a standalone instruction manual ID."""
        data = self._get_json(f"instructions/{instruction_id}")
        return Instruction.from_dict(data)

    def search_instructions(self, description: Optional[str] = None) -> List[Instruction]:
        """Searches instruction booklets by description."""
        data = self._get_json("instructions", params={"description": description})
        return [Instruction.from_dict(item) for item in data]


    # --- BINARY ENDPOINTS -> MEM ---

    def get_kit_cover(self, kit_id: str) -> bytes:
        """Fetches the kit's cover image and returns it as a byte array."""
        return self._get_bytes(f"kits/{kit_id}/cover")

    def get_instruction_cover(self, instruction_id: str) -> bytes:
        """Fetches the instruction's cover image and returns it as a byte array."""
        return self._get_bytes(f"instructions/{instruction_id}/cover")

    def get_instruction_pdf(self, instruction_id: str) -> bytes:
        """Fetches the instruction's PDF and returns it as a byte array."""
        return self._get_bytes(f"instructions/{instruction_id}/pdf")


    # --- BINARY ENDPOINTS -> I/O ---

    def download_kit_cover(self, kit_id: str, dest_path: Union[str, Path]) -> Path:
        """Streams the kit's cover image to a file."""
        return self._download_file(f"kits/{kit_id}/cover", dest_path)

    def download_instruction_cover(self, instruction_id: str, dest_path: Union[str, Path]) -> Path:
        """Streams the instruction's cover image to a file."""
        return self._download_file(f"instructions/{instruction_id}/cover", dest_path)

    def download_instruction_pdf(self, instruction_id: str, dest_path: Union[str, Path]) -> Path:
        """Streams the instruction's PDF to a file."""
        return self._download_file(f"instructions/{instruction_id}/pdf", dest_path)


    # --- BINARY ENDPOINT [MISC] ---
    def stream_instruction_pdf(self, instruction_id: str, chunk_size: int = 8192) -> Iterator[bytes]:
        """Yields raw byte chunks of an instruction PDF for custom streaming pipelines."""
        return self._stream_bytes(f"instructions/{instruction_id}/pdf", chunk_size=chunk_size)
