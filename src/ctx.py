
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

    return_label : str = ""

    def drop(self, ctx):
        for addr in self.vars.values():
            ctx.emit(f"mov rdi, [vars + {addr*WORD_SIZE}]")
            ctx.emit("call obj_dec")

    def new(self, name):
        if name not in self.vars:
            self.vars[name] = self.alloc
            self.alloc += 1
        return self.get(name)

    def get(self, name):
        if name not in self.vars:
            error.error(f"Variable `{name}` not declared.")
        return self.vars[name] * WORD_SIZE

    def save(self, ctx):
        for i in range(self.alloc):
            addr = i
            ctx.emit(f"push qword [vars + {addr}]")

    def restore(self, ctx):
        for i in range(self.alloc):
            addr = self.alloc - (i + 1)
            ctx.emit(f"pop qword [vars + {addr}]")

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

        self.emit("extrn obj_create")
        self.emit("extrn obj_inc")
        self.emit("extrn obj_dec")
        self.emit("extrn obj_dec_unwrap")

        self.emit("extrn util_create_string")

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






