
from dataclasses import dataclass as dc
from dataclasses import field
import dataclasses
import typing
import copy

import error
import tree


WORD_SIZE = 8

@dc
class Scope:
    vars  : dict[str, int] = field(default_factory=lambda: {})
    alloc : int = 0

    def drop(self, ctx):
        for addr in self.vars.values():
            ctx.emit(f"mov rdi, [vars + {addr}]")
            ctx.emit("call dec_object")

    def new(self, name):
        if name not in self.vars:
            self.vars[name] = self.alloc
            self.alloc += 1
        return self.vars[name] * WORD_SIZE

@dc
class Ctx:
    scope   : Scope          = field(default_factory=lambda: Scope())
    stack   : list[Scope]    = field(default_factory=lambda: [])
    output  : str            = ""

    strings : dict[str, str] = field(default_factory=lambda: {})

    _fresh : int = 0

    def push_scope(self):
        self.stack.append(self.scope)
        self.scope = Scope()

    def pop_scope(self):
        self.scope.drop(self)
        self.scope = self.stack.pop()

    def emit(self, line):
        self.output += line + '\n'

    def fresh(self):
        self._fresh += 1
        return f"__fresh_{self._fresh}"

    def header(self):
        self.emit("format ELF64")
        self.emit("public _start")

        self.emit("extrn outchar")
        self.emit("extrn print")
        self.emit("extrn create_object")
        self.emit("extrn inc_object")
        self.emit("extrn dec_object")
        self.emit("extrn dec_unwrap_object")

        self.emit("extrn debug_get_obj_count")

        self.emit("section '.text' executable")
        self.emit("_start:")
        self.emit("call main")

        self.emit("call debug_get_obj_count")
        self.emit("mov rdi, rax")
        self.emit("mov rax, 60")
        self.emit("syscall")


    def finalize(self):
        self.emit("section '.data' writeable")
        self.emit("vars: dp 100")

        for label, content in self.strings.items():
            self.emit(f'{label}:\ndb "{content}", 0')






