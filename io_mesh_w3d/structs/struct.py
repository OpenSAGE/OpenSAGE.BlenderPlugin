# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel


HEAD = 8  # 4(long = chunk_type) + 4 (long = chunk_size)


class Struct():
    def __init__(self, *argv, **argd):
        if argd:
            # Update by dictionary
            self.__dict__.update(argd)
