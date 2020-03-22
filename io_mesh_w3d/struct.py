# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel


class Struct:
    def __init__(self, *argv, **argd):
        if argd:
            self.__dict__.update(argd)
