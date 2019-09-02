# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel
# Last Modification 09.2019

# TODO: move this somewhere else?
HEAD = 8  # 4(long = chunk_type) + 4 (long = chunk_size)

class Struct():
    def __init__(self, *argv, **argd):
        if argd:
            # Update by dictionary
            self.__dict__.update(argd)
        else:
            # Update by position
            attrs = filter(lambda x: x[0:2] != "__", dir(self))
            for i, argv_ in enumerate(argv):
                setattr(self, attrs[i], argv_)