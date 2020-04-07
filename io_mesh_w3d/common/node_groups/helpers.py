# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel

def addInputInt(group, name, default=0, min=0, max=255):
    group.inputs.new('NodeSocketInt', name)
    group.inputs[name].default_value = default
    group.inputs[name].min_value = min
    group.inputs[name].max_value = max
