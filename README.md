# Playwell-Py

![Playwell Version](https://img.shields.io/badge/playwell-v1-red)
![GitHub License](https://img.shields.io/github/license/ModestBitboard/playwell-py?logo=gplv3&logoColor=white)
![PyPI Version](https://img.shields.io/pypi/v/playwell?logo=pypi&logoColor=white)
![Python Version](https://img.shields.io/pypi/pyversions/playwell?logo=python&logoColor=white)


The official synchronous Python client SDK for [Playwell](https://github.com/ModestBitboard/playwell-server), a read-through caching REST API for LEGO kit metadata, cover artwork, and instruction manuals.

## Features

* **Synchronous:** Built on top of `httpx`. Works seamlessly in standard scripts, CLI tools, and desktop GUI applications.
* **Config-less Default:** Connects automatically to the public instance at `https://playwell.bitboard.ca`, with easy overrides for self-hosted servers.
* **Memory & Disk Streaming:** Load cover images and PDFs directly into RAM as raw `bytes` to avoid unnecessary disk I/O, or stream heavy manuals straight to disk.
* **Automatic Handshake Validation:** Verifies server reachability and API version compatibility on initialization. (Can be disabled)
* **Strongly Typed:** Returns clean `@dataclass` objects (`Kit`, `Instruction`, `ServerStatus`) with full IDE autocomplete and dedicated exception types.

## Installation

```bash
pip install playwell
```

## Quickstart

```python
from playwell import Playwell, PlaywellNotFoundError

# Connects to https://playwell.bitboard.ca by default
with Playwell() as pw:
    # Check server handshake & version info
    print(f"Connected to {pw.server_status.service} v{pw.server_status.system_version}")

    try:
        # Fetch kit metadata (triggers a server-side scrape if not yet cached)
        kit = pw.get_kit("71374")
        print(f"{kit.name} ({kit.theme}) - {kit.pieces} pieces")

        # List available instruction manuals for the kit
        manuals = pw.get_kit_instructions("71374")
        for manual in manuals:
            print(f" - [{manual.id}] {manual.description} ({manual.size_mb} MB)")

        # Stream the first PDF directly to disk
        if manuals:
            saved_path = pw.download_instruction_pdf(manuals[0].id, f"./{kit.id}_manual.pdf")
            print(f"Saved manual to {saved_path}")

    except PlaywellNotFoundError:
        print("Could not find that LEGO kit ID.")
```

## Configuration

You can point `Playwell` at a self-hosted server either by passing `base_url` directly or by setting the `PLAYWELL_SERVER_URL` environment variable:

```python
import os
from playwell import Playwell

# Option 1: Explicit argument
pw = Playwell(base_url="http://localhost:5346")

# Option 2: Environment variable
os.environ["PLAYWELL_SERVER_URL"] = "http://localhost:5346"
pw = Playwell()

# Option 3: Skip startup version handshake
pw = Playwell(verify_version=False)
```

## In-Memory & Raw Stream Assets

For GUI applications or web services that want to render artwork without creating temporary files, use the `get_*` binary methods to fetch raw `bytes` directly into RAM, or rely on `stream_*` methods to return a bytes iterator:

```python
import io
from playwell import Playwell

with Playwell() as pw:
    # Option 1. Fetch cover image bytes
    cover_bytes = pw.get_kit_cover("71374")
    
    # Option 2. Fetch cover image byte stream
    cover_stream = pw.stream_kit_cover("71374")
```

## API Reference

| Method                                 | Description                                                        | Return Type         |
|:---------------------------------------|:-------------------------------------------------------------------|:--------------------|
| `get_status()`                         | Fetches the latest server status handshake.                        | `ServerStatus`      |
| `get_kit(kit_id)`                      | Fetches full metadata for a LEGO kit ID.                           | `Kit`               |
| `search_kits(...)`                     | Searches cached kits by `search`, `name`, `theme`, or `age_group`. | `list[Kit]`         |
| `get_kit_instructions(kit_id)`         | Lists all instruction booklets for a kit ID.                       | `list[Instruction]` |
| `get_instruction(instruction_id)`      | Fetches metadata for a standalone instruction ID.                  | `Instruction`       |
| `search_instructions(description)`     | Searches cached instruction booklets by description.               | `list[Instruction]` |
| `get_kit_cover(kit_id)`                | Fetches kit box artwork into RAM.                                  | `bytes`             |
| `download_kit_cover(kit_id, path)`     | Streams kit box artwork directly to disk.                          | `Path`              |
| `stream_kit_cover(kit_id)`             | Yields byte chunks of kit box artwork.                             | `Iterator[bytes]`   |
| `get_instruction_cover(id)`            | Fetches booklet cover artwork into RAM.                            | `bytes`             |
| `download_instruction_cover(id, path)` | Streams booklet cover artwork directly to disk.                    | `Path`              |
| `stream_instruction_cover(id)`         | Yields byte chunks of booklet cover artwork.                       | `bytes`             |
| `get_instruction_pdf(id)`              | Fetches instruction manual PDF into RAM.                           | `bytes`             |
| `download_instruction_pdf(id, path)`   | Streams instruction manual PDF directly to disk.                   | `Path`              |
| `stream_instruction_pdf(id)`           | Yields byte chunks of instruction manual PDF.                      | `Iterator[bytes]`   |

## Exceptions

All SDK exceptions inherit from `PlaywellError`:

* `PlaywellConnectionError` - Network timeout or unreachable server.
* `PlaywellVersionError` - Server does not support the client's API version (`v1`).
* `PlaywellNotFoundError` - Requested kit or instruction ID returned HTTP 404.
* `PlaywellAPIError` - Unexpected 4xx or 5xx HTTP error response from the server.

## Related Projects

* [playwell-server](https://github.com/ModestBitboard/playwell-server) - The FastAPI backend server.
* [playwell-py](https://github.com/ModestBitboard/playwell-py) - The official Python SDK.
* [playwell-go](https://github.com/ModestBitboard/playwell-go) - The official Go SDK.

## License
Distributed under the GPLv3 License. See [LICENSE](https://github.com/ModestBitboard/Playwell-Py/blob/main/LICENSE) for more information.

## Support
If you liked this project, go ahead and give it a star! And if it really helped you out, consider sending me a tip.

> **BTC**: `bc1q8tmwuyxpgkuptwu3mn4ryaemp3umvwcc0e5nkk`

