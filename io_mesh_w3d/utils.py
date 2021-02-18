# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel


class ReportHelper():
    def info(self, msg):
        print(f'INFO: {msg}')
        self.report({'INFO'}, str(msg))

    def warning(self, msg):
        print(f'WARNING: {msg}')
        self.report({'WARNING'}, str(msg))

    def error(self, msg):
        print(f'ERROR: {msg}')
        self.report({'ERROR'}, str(msg))
