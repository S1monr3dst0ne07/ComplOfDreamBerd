
from dataclasses import dataclass as dc
from dataclasses import field
import dataclasses
import typing
import time
import datetime
import json
import copy

import error
import tree



@dc
class Value:
    content : typing.Any
    kind : str

    editable   : bool = True
    assignable : bool = True

    # properties inherted on tree.AstDecl.run
    # these need to be stored here to make json pickeling possible
    lifetime : int | None = None
    lifetype : typing.Literal['default', 'stmt', 'sec', 'infty'] = 'default'

    stmt_alive : bool = True # local statement aliveness (updated by tree.AstBlock on schedule pass)
    time_born : int = -1 #unix timestamp of last variable conception

    previous : "Value" = None

    # how many bangs on the decl statement
    priority : int = 0

    def __hash__(self):
        match self.content:
            case list(): return hash(tuple(self.content))
            case x:      return hash(self.content)

    def flat(self):
        subvalues = [self]
        match self.kind:
            case 'string': subvalues += [x.flat() for x in self.content]
            case 'array' | 'dict': subvalues += [x.flat() for x in self.content.values()]

        return subvalues

    def _edit(self, ctx):
        if not self.editable:
            error.error(f'Attempting to edit uneditable value: `{self.previous.render()}`')

    def _assign(self, ctx):
        if not self.assignable:
            error.error(f'Attempting to assign unassignable value: `{self.previous.render()}`')


    def alive(self):
        match self.lifetype:
            case 'default': return True
            case 'infty': return True # for ever and infinity
            case 'stmt': return self.stmt_alive
            case 'sec' :
                passed = time.time() - self.time_born
                return passed < self.lifetime

            case x:
                error.internal(f"Unknown lifetype: `{x}`")


    def render(self):
        match self.kind:
            case 'string':
                return ''.join(x.render() for x in self.content)
            case 'char':
                return self.content
            case 'null': return "NULL"
            case 'undefined': return "undefined"
            case 'int' | 'float' | 'bool':
                return str(self.content)
            case 'array':
                indices = sorted(self.content.keys())
                seg = []

                for x in indices:
                    seg.append(self.content[x].render())
                    seg.append(', ')

                seg.pop()
                return f"[{''.join(seg)}]"

            case 'dict':
                return str({ k.render() : v.render() for k, v in self.content.items()})

            case 'metaclass':
                return "<metaclass object>"
            case 'class':
                rendered = { k : v.render() for k, v in self.content.items()}
                return f"<class {rendered}>"

            case 'magictime':
                return str(datetime.datetime.fromtimestamp(
                    time.time() + (self.content / 1000) # ms to float secs
                ))

            case x:
                error.error(f"Unable to render type: `{x}`")



@dc
class Scope:
    locals : dict[str, Value] = field(default_factory=lambda: {})
    when   : dict[str, list["tree.AstWhen"]] = field(default_factory=lambda: {})

    def find_local_name_by_value(self, value):
        for name, supervalue in self.locals.items():
            for subvalue in supervalue.flat():
                if subvalue is value:
                    return name

    def copy(self):
        new = Scope()
        # the values in scope must be shallow copies to allow
        # passing and editing contains in different scopes.
        new.locals = { k : copy.copy(v) for k, v in self.locals.items() }
        new.when   = self.when.copy()
        return new


    def __getitem__(self, index):
        return self.locals[index]
    def __setitem__(self, index, new):
        self.locals[index] = new
    def __contains__(self, elem):
        return elem in self.locals



@dc
class Ctx:
    scope : Scope = field(default_factory=lambda: Scope())
    stack : list = field(default_factory=lambda: [])


    def push_scope(self):
        self.stack.append(self.scope.copy())

    def pop_scope(self):
        inner = self.scope
        self.scope = self.stack.pop()

        #copy global from inner to outer scope
        for name, value in inner.locals.items():
            if not name.startswith('g_'): continue
            self.scope[name] = value




