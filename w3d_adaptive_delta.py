import math
from mathutils import Quaternion

def fill_with_exponents_of_10(table):
    for i in range(16):
        table.append(pow(10, i - 8.0))


def fill_with_sinus_function(table):
    for i in range(240):
        num = i / 240.0
        table.append(1.0 - math.sin(90.0 * num * math.pi / 180.0))


def calculate_table():
    table = []
    fill_with_exponents_of_10(table)
    fill_with_sinus_function(table)
    return table


delta_table = calculate_table()


def to_signed(byte):
    if byte > 127:
        return (256-byte) * (-1)
    else:
        return byte


def get_deltas(block, numBits):
    deltas = [None] * 16

    for i, byte in enumerate(block.deltaBytes):
        index = i * 2
        if numBits == 4:
            deltas[index] = to_signed(byte)
            # Bitflip
            if (deltas[index] & 8) != 0:
                deltas[index] = to_signed(deltas[index] | 0xF0)
            else:
                deltas[index] = to_signed(deltas[index] & 0x0F)
            deltas[index + 1] = to_signed(byte >> 4)
        elif numBits == 8:
            # Bitflip
            if byte & 0x80 != 0:
                byte &= 0x7F
            else:
                byte |= 0x80
            deltas[i] = to_signed(byte)

    return deltas

    
def decode(data, channel, scale):
    scaleFactor = 1.0

    if data.bitCount == 8:
        scaleFactor = 1 / 16.0

    result = [None] * channel.numTimeCodes
    result[0] = data.initialValue

    for i, deltaBlock in enumerate(data.deltaBlocks):
        blockScale = delta_table[deltaBlock.blockIndex]
        deltaScale = blockScale * scale * scaleFactor

        vectorIndex = deltaBlock.vectorIndex
        deltas = get_deltas(deltaBlock, data.bitCount)

        for j, delta in enumerate(deltas):
            idx = int(math.floor((i / channel.vectorLen) * 16) + j + 1)
            if idx >= channel.numTimeCodes:
                break

            if channel.type == 6:
                index = (vectorIndex + 1) % 4 # access quat as xyzw instead of wxyz
                value = result[idx - 1][index] + deltaScale * delta
                if (result[idx] == None):
                    result[idx] = Quaternion()
                    result[idx].w = result[idx - 1].w
                    result[idx].x = result[idx - 1].x
                    result[idx].y = result[idx - 1].y
                    result[idx].z = result[idx - 1].z
                result[idx][index] = value
                
            else:
                result[idx] = result[idx - 1] + deltaScale * delta

    return result
