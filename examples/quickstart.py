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
