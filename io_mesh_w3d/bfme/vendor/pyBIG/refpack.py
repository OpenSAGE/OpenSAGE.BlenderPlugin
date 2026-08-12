import logging
import struct


def has_refpack_header(data: bytes) -> bool:
    """Check if input data is refpack by checking the
    header. Data may be headerless refpack data, only way
    to really check is to attempt a decompress

    Params
    -------
    data: bytes
        Input data to check

    Returns
    --------
    bool
        True if data has the refpack header
    """
    if len(data) < 5:
        return False

    # Check 2-byte magic number
    marker = struct.unpack(">H", data[:2])[0]
    if marker != 0x10FB:
        return False

    # Read 3-byte uncompressed size
    size_bytes = data[2:5]
    unpacked_size = size_bytes[0] | (size_bytes[1] << 8) | (size_bytes[2] << 16)

    # Basic sanity check
    if unpacked_size == 0 or unpacked_size > 100_000_000:
        return False

    return True


def matchlen(s: bytes, d: bytes, maxmatch: int) -> int:
    current = 0
    while current < maxmatch and s[current] == d[current]:
        current += 1
    return current


def hash_bytes(data: bytes) -> int:
    return ((data[0] << 4) ^ (data[1] << 2) ^ (data[2])) & 0xFFFF


def compress(input_data: bytes) -> bytes:
    """Compress bytes to refpack format

    Params
    -------
    input_data: bytes
        Data to compress


    Returns
    --------
    bytes
        Compressed data
    """
    length = len(input_data)
    to = bytearray()

    # Add RefPack magic number (0x10FB) and uncompressed size (3 bytes LE)
    to += struct.pack(">H", 0x10FB)  # big-endian magic
    to += bytes([(length >> 16) & 0xFF, (length >> 8) & 0xFF, length & 0xFF])

    compressed = bytearray()

    run = 0
    cptr = 0
    rptr = 0

    hashtbl = [-1] * 65536
    link = [-1] * 131072

    while cptr < length:
        boffset = 0
        blen = 2
        bcost = 2
        mlen = min(length - cptr, 1028)
        if cptr + 2 >= length:
            mlen = 0

        if mlen >= 3:
            h = hash_bytes(input_data[cptr : cptr + 3])
            hoffset = hashtbl[h]
            minhoffset = max(cptr - 131071, 0)

            while hoffset >= minhoffset:
                tptr = hoffset
                if (
                    cptr + blen < length
                    and tptr + blen < length
                    and input_data[cptr + blen] == input_data[tptr + blen]
                ):
                    tlen = matchlen(input_data[cptr:], input_data[tptr:], mlen)
                    if tlen > blen:
                        toffset = (cptr - 1) - tptr
                        if toffset < 1024 and tlen <= 10:
                            tcost = 2
                        elif toffset < 16384 and tlen <= 67:
                            tcost = 3
                        else:
                            tcost = 4

                        if tlen - tcost + 4 > blen - bcost + 4:
                            blen = tlen
                            bcost = tcost
                            boffset = toffset
                            if blen >= 1028:
                                break
                hoffset = link[hoffset & 131071]

        if bcost >= blen:
            h = hash_bytes(input_data[cptr : cptr + 3]) if cptr + 2 < length else 0
            hoffset = cptr
            link[hoffset & 131071] = hashtbl[h]
            hashtbl[h] = hoffset

            run += 1
            cptr += 1
        else:
            while run > 3:
                tlen = min(112, run & ~3)
                run -= tlen
                compressed.append(0xE0 + (tlen >> 2) - 1)
                compressed += input_data[rptr : rptr + tlen]
                rptr += tlen

            if bcost == 2:
                compressed.append(((boffset >> 8) << 5) + ((blen - 3) << 2) + run)
                compressed.append(boffset & 0xFF)
            elif bcost == 3:
                compressed.append(0x80 + (blen - 4))
                compressed.append((run << 6) + (boffset >> 8))
                compressed.append(boffset & 0xFF)
            else:
                compressed.append(0xC0 + ((boffset >> 16) << 4) + (((blen - 5) >> 8) << 2) + run)
                compressed.append((boffset >> 8) & 0xFF)
                compressed.append(boffset & 0xFF)
                compressed.append((blen - 5) & 0xFF)

            if run:
                compressed += input_data[rptr : rptr + run]
                rptr += run
                run = 0

            for i in range(blen):
                if cptr + 2 < length:
                    h = hash_bytes(input_data[cptr : cptr + 3])
                    hoffset = cptr
                    link[hoffset & 131071] = hashtbl[h]
                    hashtbl[h] = hoffset
                cptr += 1

            rptr = cptr

    while run > 3:
        tlen = min(112, run & ~3)
        run -= tlen
        compressed.append(0xE0 + (tlen >> 2) - 1)
        compressed += input_data[rptr : rptr + tlen]
        rptr += tlen

    compressed.append(0xFC + run)
    if run:
        compressed += input_data[rptr : rptr + run]

    to += compressed
    return bytes(to)


def decompress(input_data: bytes, ignore_mismatch: bool = False) -> bytes:
    """Decompress refpack data. This expects the data to have a refpack header
    but will still attempt to decompress if it cannot find

    Params
    -------
    input_data: bytes
        The data to decompress
    ingore_mismatch: Optional[bool]
        If the data has a refpack header, the function will
        raise an error if the expected size is not the same
        as the decompressed size. You can use this to suppres it.

    Returns
    --------
    bytes
        The decompressed bytes
    """
    index = 0

    expected_size = None
    if len(input_data) >= 5:
        magic = struct.unpack(">H", input_data[:2])[0]
        if magic == 0x10FB:
            expected_size = (input_data[2] << 16) | (input_data[3] << 8) | input_data[4]
            input_data = input_data[5:]

    output = bytearray()

    while True:
        first = input_data[index]
        index += 1

        if not (first & 0x80):  # short ref
            second = input_data[index]
            index += 1
            run = first & 3
            output += input_data[index : index + run]
            index += run
            ref_offset = ((first & 0x60) << 3) + second
            ref = len(output) - 1 - ref_offset
            length_to_copy = ((first & 0x1C) >> 2) + 3
            for _ in range(length_to_copy):
                output.append(output[ref])
                ref += 1
            continue

        if not (first & 0x40):  # long ref
            second = input_data[index]
            third = input_data[index + 1]
            index += 2
            run = second >> 6
            output += input_data[index : index + run]
            index += run
            ref_offset = ((second & 0x3F) << 8) + third
            ref = len(output) - 1 - ref_offset
            length_to_copy = (first & 0x3F) + 4
            for _ in range(length_to_copy):
                output.append(output[ref])
                ref += 1
            continue

        if not (first & 0x20):  # very long ref
            second = input_data[index]
            third = input_data[index + 1]
            fourth = input_data[index + 2]
            index += 3
            run = first & 3
            output += input_data[index : index + run]
            index += run
            ref_offset = ((first & 0x10) >> 4 << 16) + (second << 8) + third
            ref = len(output) - 1 - ref_offset
            length_to_copy = (((first & 0x0C) >> 2) << 8) + fourth + 5
            for _ in range(length_to_copy):
                output.append(output[ref])
                ref += 1
            continue

        # literal or EOF
        run = ((first & 0x1F) << 2) + 4
        if run <= 112:
            output += input_data[index : index + run]
            index += run
            continue
        run = first & 3
        output += input_data[index : index + run]
        break

    if expected_size is not None and expected_size != len(output):
        if ignore_mismatch is True:
            logging.info("Decompress size mismatch")
        else:
            raise ValueError("Decompress size mismatch")

    return bytes(output)
