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


def set_deltas(delta_bytes, num_bits):
    result = [None] * num_bits * 2

    if num_bits == 4:
        for i in range(int(len(delta_bytes) / 2)):
            lower = delta_bytes[i * 2]
            # Bitflip
            if lower < 0:
                lower += 16
            upper = delta_bytes[i * 2 + 1]
            result[i] = (upper << 4) | lower
    else:
        for i, byte in enumerate(delta_bytes):
            # Bitflip
            byte -= 128
            if byte < -127:
                byte += 256
            result[i] = byte
    return result


def decode(channel):
    data = channel.data.data
    scale = channel.data.scale

    scale_factor = 1.0
    if data.bit_count == 8:
        scale_factor /= 16.0

    result = [None] * channel.num_time_codes
    result[0] = data.initial_value

    for i, delta_block in enumerate(data.delta_blocks):
        delta_scale = scale * scale_factor * DELTA_TABLE[delta_block.block_index]
        deltas = get_deltas(delta_block.delta_bytes, data.bit_count)

        for j, delta in enumerate(deltas):
            idx = int(i / channel.vector_len) * 16 + j + 1
            if idx >= channel.num_time_codes:
                break

            if channel.channel_type == 6:
                # shift from wxyz to xyzw
                index = (delta_block.vector_index + 1) % 4
                value = result[idx - 1][index] + delta_scale * delta
                if result[idx] is None:
                    result[idx] = result[idx - 1].copy()
                result[idx][index] = value
            else:
                result[idx] = result[idx - 1] + delta_scale * delta
    return result


def encode(channel, num_bits):
    scale_factor = 1.0
    if num_bits == 8:
        scale_factor /= 16.0

    scale = 0.07435  # how to get this ???

    num_time_codes = len(channel.data) - 1  # minus initial value
    num_delta_blocks = int(num_time_codes / 16) + 1
    deltas = [0x00] * (num_delta_blocks * 16)

    default_value = None

    for i, value in enumerate(channel.data):
        if i == 0:
            default_value = value
            continue

        block_index = 33  # how to get this one?

        old = default_value
        # if i > 1:
        #    channel.data[i - 1]
        delta = value - old
        delta /= (scale_factor * scale * DELTA_TABLE[block_index])

        delta = int(delta)
        # print("delta: " + str(delta) + " index: " + str(block_index))
        deltas[i - 1] = delta

    deltas = set_deltas(deltas, num_bits)
    return deltas
