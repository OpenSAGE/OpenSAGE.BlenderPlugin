# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

import math
from mathutils import Quaternion

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
        elif num_bits == 8:
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
            if lower < 0:
                lower += 16
            upper = bytes[i * 2 + 1]
            result[i] = (upper << 4) | lower
    elif num_bits == 8:
        for i in range(len(bytes)):
            byte = bytes[i]
            byte -= 128
            if byte < -127:
                byte += 256
            result[i] = byte
    return result


def decode(channel):
    data = channel.data.data
    scale = channel.data.scale

    scaleFactor = 1.0
    if data.bit_count == 8:
        scaleFactor /= 16.0

    result = [None] * channel.num_time_codes
    result[0] = data.initial_value

    for i, delta_block in enumerate(data.delta_blocks):
        deltaScale = scale * scaleFactor * DELTA_TABLE[delta_block.block_index]
        deltas = get_deltas(delta_block.delta_bytes, data.bit_count)

        for j, delta in enumerate(deltas):
            idx = int(i / channel.vector_len) * 16 + j + 1
            if idx >= channel.num_time_codes:
                break

            if channel.type == 6:
                index = (delta_block.vector_index + 1) % 4
                value = result[idx - 1][index] + deltaScale * delta
                if result[idx] is None:
                    result[idx] = result[idx - 1].copy()
                result[idx][index] = value
            else:
                result[idx] = result[idx - 1] + deltaScale * delta
    return result


def encode(channel, num_bits):
    delta_type = 1
    scaleFactor = 1.0

    if num_bits == 8:
        delta_type = 2
        scaleFactor /= 16.0

    num_time_codes = len(channel.data)

    #delta_data = AdaptiveDeltaData(
    #        initial_value=channel.data[0],
    #        delta_blocks=[],
    #        bit_count=num_bits)

    #animationChannel = AdaptiveDeltaMotionAnimationChannel(
    #    scale=0.0,
    #    data=delta_data)

    #output = MotionChannel(
    #    delta_type=delta_type,
    #    vector_len=channel.vector_len,
    #    type=channel.type,
    #    pivot=channel.pivot,
    #    num_time_codes=num_time_codes,
    #    data=animationChannel)

    #16 delta bytes
    num_delta_blocks = (num_time_codes - (num_bits * 2) - 1) / 16
    delta_blocks = []
    print(num_delta_blocks)

    #TODO

    return delta_blocks