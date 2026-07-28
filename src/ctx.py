
from dataclasses import dataclass as dc
from dataclasses import field
import dataclasses
import typing
import copy

import error
import tree



@dc
class Ctx:
    scope   : dict[str, int] = field(default_factory=lambda: {})
    output  : str            = ""

    strings : dict[str, str] = field(default_factory=lambda: {})

    _fresh : int = 0

    def emit(self, line):
        self.output += line + '\n'

    def fresh(self):
        self._fresh += 1
        return f"__fresh_{self._fresh}"

    def lookup(self, name):
        print("impl ctx lookup")

    def alloc(self, name):
        print("impl ctx alloc")



    def header(self):
        self.emit("format ELF64")
        self.emit("public _start")

        self.emit("extrn outchar")
        self.emit("extrn print")
        self.emit("extrn create_object")

        self.emit("section '.text' executable")
        self.emit("_start:")
        self.emit("call main")
        self.emit("mov rax, 60")
        self.emit("mov rdi, 0")
        self.emit("syscall")


    def finalize(self):
        self.emit("section '.data' writeable")
        self.emit("__local_vars: dp 100")

        for label, content in self.strings.items():
            self.emit(f'{label}:\ndb "{content}", 0')






