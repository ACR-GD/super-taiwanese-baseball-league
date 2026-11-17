import os
import struct

def create_ips_patch(original_path, modified_path, patch_path):
    with open(original_path, 'rb') as f:
        orig = f.read()
    with open(modified_path, 'rb') as f:
        mod = f.read()

    max_len = max(len(orig), len(mod))
    # Pad if sizes differ
    orig_bytes = orig.ljust(max_len, b'\x00')
    mod_bytes = mod.ljust(max_len, b'\x00')

    # Find all differing byte indices
    diffs = [i for i in range(max_len) if orig_bytes[i] != mod_bytes[i]]
    if not diffs:
        print("No differences found between original and modified files.")
        return

    print(f"Total differing bytes: {len(diffs)}")

    # Group diffs into records (merge gaps <= 5 bytes)
    records = []
    start = diffs[0]
    end = diffs[0] + 1

    for d in diffs[1:]:
        if d - end <= 5 and (d - start) < 65535:
            end = d + 1
        else:
            records.append((start, end))
            start = d
            end = d + 1
    records.append((start, end))
    # A grown file whose tail matches the zero padding gets no record; write its last byte so
    # patchers extend the file to the full size.
    if len(mod) > len(orig) and records[-1][1] < len(mod):
        records.append((len(mod) - 1, len(mod)))

    # Split records larger than 65535 bytes (IPS max record length)
    split_records = []
    for s, e in records:
        while e - s > 65535:
            split_records.append((s, s + 65535))
            s += 65535
        split_records.append((s, e))

    print(f"Generated {len(split_records)} IPS records.")

    # Write IPS patch
    with open(patch_path, 'wb') as f:
        f.write(b'PATCH')
        for s, e in split_records:
            # 3-byte offset
            f.write(struct.pack('>I', s)[1:])
            # 2-byte length
            length = e - s
            f.write(struct.pack('>H', length))
            # payload
            f.write(mod_bytes[s:e])
        f.write(b'EOF')

    patch_size = os.path.getsize(patch_path)
    print(f"Successfully created IPS patch: {patch_path} ({patch_size} bytes)")

    # Self-test / Verification
    verify_ips_patch(orig, patch_path, mod)

def verify_ips_patch(orig_bytes, patch_path, expected_bytes):
    with open(patch_path, 'rb') as f:
        patch = f.read()

    assert patch.startswith(b'PATCH'), "Invalid IPS header"
    assert patch.endswith(b'EOF'), "Invalid IPS footer"

    patched = bytearray(orig_bytes)
    pos = 5
    while pos < len(patch) - 3:
        offset = (patch[pos] << 16) | (patch[pos+1] << 8) | patch[pos+2]
        pos += 3
        length = (patch[pos] << 8) | patch[pos+1]
        pos += 2
        if length > 0:
            data = patch[pos:pos+length]
            pos += length
            if offset + length > len(patched):
                patched.extend(b'\x00' * (offset + length - len(patched)))
            patched[offset:offset+length] = data
        else:
            # RLE record
            rle_len = (patch[pos] << 8) | patch[pos+1]
            pos += 2
            rle_val = patch[pos]
            pos += 1
            if offset + rle_len > len(patched):
                patched.extend(b'\x00' * (offset + rle_len - len(patched)))
            patched[offset:offset+rle_len] = bytes([rle_val]) * rle_len

    if patched == expected_bytes:
        print("VERIFICATION SUCCESS: Patched bytes match modified ROM exactly (100% bit-identical)!")
    else:
        raise AssertionError("VERIFICATION FAILED: Patched bytes differ from modified ROM!")
