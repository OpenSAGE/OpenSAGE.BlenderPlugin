# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import math


def fill_with_exponents_of_10(table):
    for i in range(16):
        table.append(pow(10, i - 8))


def fill_with_sinus_function(table):
    for i in range(240):
        num = i / 240.0
        table.append(1.0 - math.sin(90.0 * num * math.pi / 180.0))


def calculate_table():
    table = []
    fill_with_exponents_of_10(table)
    fill_with_sinus_function(table)
    return table


DELTA_TABLE = calculate_table()


def get_deltas(delta_bytes, num_bits):
    deltas = [None] * 16

    for i, byte in enumerate(delta_bytes):
        if num_bits == 4:
            index = i * 2
            lower = byte & 0x0F
            upper = byte >> 4
            # Bitflip
            if lower >= 8:
                lower -= 16

            deltas[index] = lower
            deltas[index + 1] = upper
        else:
            # Bitflip
            byte += 128
            if byte >= 128:
                byte -= 256
            deltas[i] = byte
    return deltas


def set_deltas(bytes, num_bits):
    result = [None] * num_bits * 2

    if num_bits == 4:
        for i in range(int(len(bytes) / 2)):
            lower = bytes[i * 2]
            # Bitflip
            if lower < 0:
                lower += 16
            upper = bytes[i * 2 + 1]
            result[i] = (upper << 4) | lower
    else:
        for i in range(len(bytes)):
            byte = bytes[i]
            # Bitflip
            byte -= 128
            if byte < -127:
                byte += 256
            result[i] = byte
    return result


def decode(channel):
    data = channel.data.data
    scale = channel.data.scale

    print(f'scale: {scale}')

    scale_factor = 1.0
    if data.bit_count == 8:
        scale_factor /= 16.0

    result = [None] * channel.num_time_codes
    result[0] = data.initial_value
    print(f'initial: {data.initial_value}')

    for i, delta_block in enumerate(data.delta_blocks):
        print(f'block index: {delta_block.block_index}')
        delta_scale = scale * scale_factor * DELTA_TABLE[delta_block.block_index]
        print('delta bytes:')
        for bytee in delta_block.delta_bytes:
            print(bytee)
        deltas = get_deltas(delta_block.delta_bytes, data.bit_count)
        print('deltas:')
        for delt in deltas:
            print(delt)
        print(f'delta_scale: {delta_scale}')
        for j, delta in enumerate(deltas):
            idx = int(i / channel.vector_len) * 16 + j + 1
            print(f'idx: {idx}')
            if idx >= channel.num_time_codes:
                break
            print(f'channel type: {channel.type}')
            if channel.type == 6:
                # shift from wxyz to xyzw
                index = (delta_block.vector_index + 1) % 4
                value = result[idx - 1][index] + delta_scale * delta
                if result[idx] is None:
                    result[idx] = result[idx - 1].copy()
                result[idx][index] = value
            else:
                print(f'old: {result[idx - 1]}')
                print(f'delta: {delta}')
                result[idx] = result[idx - 1] + delta_scale * delta
                print(f'new: {result[idx]}')
    return result


def encode(channel, num_bits):
    scale_factor = 1.0
    if num_bits == 8:
        scale_factor /= 16.0

    scale = 0.07435  # how to get this? -> hardcoded for now

    num_time_codes = len(channel.data) - 1  # minus initial value
    print(f'time codes: {num_time_codes}')
    num_delta_blocks = int(num_time_codes / 16) + 1
    print(f'delta blocks: {num_delta_blocks}')
    deltas = [0x00] * (num_delta_blocks * 16)
    print(f'num deltas: {len(deltas)}')

    default_value = None
    old = None

    #  4.3611, 4.6524
    for i, value in enumerate(channel.data):
        print(f'i: {i}')
        print(f'value: {value}')
        if i == 0:
            default_value = value # 4.3611 passt
            old = default_value
            print(f'default_value: {default_value}')
            continue

        block_index = 33  # how to get this one?
        delta_scale = scale * scale_factor * DELTA_TABLE[block_index] # 0.06609 passt
        print(f'delta_scale: {delta_scale}')

        delta = round((value - old) / delta_scale)
        print(f'delta: {delta}') # should be 4
        deltas[i - 1] = delta 
        old = value

    print(f'deltas: {deltas}')
    deltas = set_deltas(deltas, num_bits)
    print(f'len deltas: {len(deltas)}')
    return deltas
