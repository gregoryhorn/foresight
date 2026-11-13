"""Portable safe error codes shared by adapters."""
class Fault(Exception):
    def __init__(self, code, status=400):
        self.code, self.status = code, status
        super().__init__(code)
