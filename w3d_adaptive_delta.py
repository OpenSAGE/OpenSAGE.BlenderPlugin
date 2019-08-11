import os
import bpy
import bmesh
import math

def calculate_table():
    result = []

    # First 16 entries are exponents of 10
    for i in range(0,16):
        result.append(pow(10, i - 8.0))

    # Fill a precomputed sinus function
    for i in range(0,240):
        num = i / 240.0
        result.append(1.0 - math.sin(90.0 * num * math.pi / 180.0))

    return result

delta_table = calculate_table()

def decode(data, numFrames, scale):
    scaleFactor = 1.0

    if data.bitCount == 8:
        scaleFactor = 1.0 / 16.0

    result = [None] * numFrames
    result[0] = data.initialValue

    for i, deltaBlock in enumerate(data.deltaBlocks):
        blockIndex = deltaBlock.blockIndex
        blockScale = delta_table[blockIndex]
        deltaScale = blockScale * scale * scaleFactor

        vectorIndex = deltaBlock.vectorIndex

        deltas = get_deltas(deltaBlock, data.bitCount)

        for j, delta in enumerate(deltas):
            index = ((i / data.vectorLength) * 16) + j + 1
            if index >= numFrames:
                break

            value = result[index - 1][vectorIndex] + deltaScale * delta
            result[index] = result[index][vectorIndex] = value

            index+=1

    return result

def get_deltas(block, bits):
    deltas = [None] * 16

    for i, byte in enumerate(block.deltaBytes):
        if bits == 4:
            # Bitflip
            if byte & 8 != 0:
                deltas[i*2] = byte | 0xF0
            else:
                deltas[i*2] = byte & 0x0F
        elif bits == 8:
            # Bitflip
            if byte & 0x80 != 0:
                deltas[i*2] = byte & 0x7F
            else:
                deltas[i*2] = byte | 0x80

        else:
            print("Unsupported bit count: " + bits)

    return deltas
