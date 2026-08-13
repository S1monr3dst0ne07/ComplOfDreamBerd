
import typing
import time
import regex
from dataclasses import dataclass as dc

import lex
import error
import sym
from ctx import Ctx
import binding



# function calls and Variable accesses cannot be differentiated at parse-time.
# hence they both are unified under the AstScopeAccess node type.
# `iden` and `subj` cannot be expression here because it makes it impossible to parse.
# you can't know, for example, how to parse the following if you assume function references can be expression:
# ` 1 + a 1, 2, 3`
# is it `(1 + a)(1, 2, 3)` or `1 + a(1, 2, 3)`?
# hence this implement assumes function references cannot be expressions.
# it would parse the upper expression as such:
# `1 + a(1, 2, 3)`

@dc
class AstScopeAccess:
    iden : str #variable / function name
    subj : str | None # optional subject prefix
    params : list[typing.Any]

    def order(self):
        for i, param in enumerate(self.params):
            self.params[i] = param.order()


    def _can_param_token(stream):
        match stream.peekt().kind:
            case 'numb' | 'iden' | 'quote':
                return True

            case _:
                return False

    @classmethod
    def parse(cls, stream):
        iden = stream.pop()
        params = []

        # syntax sugar for `subj.verb(obj...)` => `verb(subj, obj...)`
        subj = None
        if stream.peek() == '.':
            stream.expect('.')
            subj, iden = iden, stream.pop()

        #if stream.peek().isdigit() or stream.peekt().content not in (sym.op + sym.un_op + sym.block):
        if cls._can_param_token(stream):
            # this check is needed to prevent `x + 5` from
            # being parsed as `x(+) 5`

            while stream.peekt().kind not in ('eos', 'debug'):
                params.append(AstExpr.parse(stream))
                if stream.peek() != ',': break
                stream.expect(',')

        return cls(iden, subj, params)

    def _var_lookup(self, ctx, iden):
        if iden in ctx.eternal: return ctx.eternal[iden]

        if iden not in ctx.scope:
            error.error(f"Identifier `{iden}` does not exist in scope.")
    
        var = ctx.scope[iden]
        if not var.alive():
            error.error(f"Trying to access variable `{iden}` but it's dead :(") #)
    
        return ctx.scope[iden]

    def _check_string_without_quote(self, ctx):
        return (self.iden not in ctx.eternal and self.iden not in ctx.scope)

    def _process_string_without_quote(self, ctx):
        segments = [self.iden] + [x.run(ctx).render() for x in self.params]
        return obj.Value(content=[
            obj.Value(content=char, kind='char')
            for char in " ".join(segments) 
                #space information is lost during parsing.
                #retaining it would require so, so, so much work.
                #plus the example don't show multi-space quoteless strings,
                # so what do i care.
        ], kind='string')



    def vars(self):
        return [self.iden] + [x.vars() for x in self.params]

    def _compile_call(self, ctx):
        ctx.scope.save(ctx)

        #load paramters
        for param in self.params[::-1]:
            param.compile(ctx)
            ctx.emit("push rax")
            
        #copy into passing regs
        for reg in binding.ABI[:len(self.params)]:
            ctx.emit(f"pop {reg}")

        ctx.emit(f"call {self.iden}")
        ctx.scope.restore(ctx)

    def _compile_var(self, ctx):
        # a new value reference is created
        addr = ctx.scope.get(self.iden)
        ctx.emit(f"mov rdi, [vars + {addr}]")
        ctx.emit("push rdi")
        ctx.emit("call obj_inc")
        ctx.emit("pop rax")

    def compile(self, ctx):
        if self.iden not in ctx.scope.vars:
            self._compile_call(ctx)

        else:
            self._compile_var(ctx)

    def store(self, ctx):
        if self.iden not in ctx.scope.vars:
            error.error(f"Storing into undeclared variable `{self.iden}`")

        addr = ctx.scope.get(self.iden)
        ctx.emit(f"push qword [vars + {addr}]")
        ctx.emit(f"mov [vars + {addr}], rax")
        ctx.emit(f"pop rdi")
        ctx.emit("call obj_dec")



@dc
class AstLitArray:
    @staticmethod
    def parse(stream):
        stream.expect('[')
        stream.expect(']')

@dc
class AstLitDict:
    @staticmethod
    def parse(stream):
        stream.expect("{")
        stream.expect("}")

@dc
class AstIndexAccess:
    name  : "str"
    index : "AstExpr"

    def order(self):
        self.index = self.index.order()

    @classmethod
    def parse(cls, stream):
        name = stream.pop()

        stream.expect('[') #]
        index = AstExpr.parse(stream)
        stream.expect(']')

        return cls(name, index)

    def store(self, ctx):
        ctx.emit("push rax")
        self.index.compile(ctx)
        ctx.emit(f"pop {binding.ABI[2]}") 
        ctx.emit(f"mov {binding.ABI[1]}, rax")
        addr = ctx.scope.get(self.name)
        ctx.emit(f"mov {binding.ABI[0]}, [vars + {addr}]")
        ctx.emit("call util_set_ht")

    def compile(self, ctx):
        self.index.compile(ctx)
        ctx.emit(f"mov {binding.ABI[1]}, rax")
        addr = ctx.scope.get(self.name)
        ctx.emit(f"mov {binding.ABI[0]}, [vars + {addr}]")
        ctx.emit("call util_get_ht")





@dc
class AstLeaf:
    kind : int # binding.KIND
    value : typing.Any

    def order(self):
        if self.kind in ('scope', 'index'):
            self.value.order()

        return self

    def collect(self, ctx): pass

    @staticmethod
    def _compute_quote_size(token):
        size = 0
        for char in token.content:
            if char == "'": size += 1
            if char == '"': size += 2

        return size

    @classmethod
    def _parse_string(cls, stream):
        token = stream.popt()
        size = cls._compute_quote_size(token)

        string_segments = []
        while cls._compute_quote_size(stream.peekt()) != size:
            string_segments.append(stream.pop()) 
            string_segments.append(" " * stream.space())
        stream.pop() #discard closing quote

        return "".join(string_segments)

    @classmethod
    def parse(cls, stream):
        match stream.peekt().kind:
            case 'numb':
                value = int(stream.pop())
                return cls('int', value)

            case 'quote': 
                content = cls._parse_string(stream)
                return cls('string', content)
                
            case 'arrayopen':
                AstLitArray.parse(stream)
                return cls('array', 0)

            case 'blockopen':
                AstLitDict.parse(stream)
                return cls('dict', 0)

            case 'iden' | 'sym': 
                if stream.lookhead(2)[1].kind == 'arrayopen':
                    return cls('index', AstIndexAccess.parse(stream))
                else:
                    return cls('scope', AstScopeAccess.parse(stream))

            case x: error.error(f"Unknown leaf kind: {stream.popt()}")

    def vars(self):
        if type(self.value) is obj.Value:
            return []

        return self.value.vars()

    def _create_object(self, ctx, kind):
        # create actual runtime object from rax
        ctx.emit(f"mov rdi, {kind}")
        ctx.emit(f"mov rsi, rax")
        ctx.emit("call obj_create")

    def compile(self, ctx):
        match self.kind:
            case 'string':
                label = ctx.fresh()
                ctx.emit(f"mov rdi, {label}")
                ctx.emit("call util_create_string")

                ctx.strings[label] = self.value

            case 'int':
                ctx.emit(f"mov rax, {self.value}")
                self._create_object(ctx, binding.KIND.INT)

            case 'scope':
                self.value.compile(ctx)

            case 'dict':
                ctx.emit("call ht_create")
                self._create_object(ctx, binding.KIND.DICT)

            case 'index':
                self.value.compile(ctx)


            case x: print("todo impl leaf kind: ", self.kind)


@dc
class AstUn:
    op : str
    sub : AstLeaf

    def order(self): 
        return self


    @classmethod
    def parse(cls, stream):
        if stream.peek() not in sym.un_op:
            return AstLeaf.parse(stream)

        op = stream.pop()
        stream.space() #the spec makes no mention of unary operator separation 
        sub = AstLeaf.parse(stream)
        return cls(op, sub)


    def vars(self):
        return self.sub.vars()



@dc
class AstExpr:
    space : int 
        # how much whitespace surround the operators? 
        # used for graph rewriting

    op : str
    left  : "AstExpr | AstUn | AstLeaf"
    right : "AstExpr | AstUn | AstLeaf"

    def extract(self, parent):
        if type(self.right) is not AstExpr: return (self, parent)

        other = self.right.extract(self)
        return other if other[0].space > self.space else (self, parent)


    def order(self):
        # after parsing, the expression tree is maximally unballanced,
        # meaning it looks like this:
        #   ()
        #  / ()
        #   / \...
        # we extract the node with least precedence,
        #  then pivot it and make it the new root node.
        #  this process is repeated recursively until 
        #  the tree is balanced based on the precedence.

        new, parent = self.extract(None)
        old = self

        if new != old:
            # you can work these operations out on paper if you think about it really really hard.
            # i'm not even gonna try and explain them.
            # rest assured, they balance the tree.
            orphan = new.left
            new.left = old
            parent.right = orphan

        #now recurse
        new.left.order()
        new.right.order()

        return new

    @classmethod
    def parse(cls, stream):
        left = AstUn.parse(stream)
        left_space = stream.space()

        if stream.peek() not in sym.op:
            return left

        op = stream.pop()
        right_space = stream.space()
        right = AstExpr.parse(stream)

        return cls(
            max(left_space, right_space),
            left = left,
            right = right,
            op = op
        )


    def vars(self):
        return self.left.vars() + self.right.vars()

    def compile(self, ctx):
        self.right.compile(ctx)
        ctx.emit("push rax")
        self.left.compile(ctx)
        ctx.emit("mov rsi, rax")
        ctx.emit("pop rdi")

        match self.op:
            case '+':   kind = binding.OP.PLUS
            case '-':   kind = binding.OP.MINUS
            case '*':   kind = binding.OP.TIMES
            case '===': kind = binding.OP.EQUAL
            case ';==': kind = binding.OP.INEQUAL

            case x: print(f"impl op: {x}")

        ctx.emit(f"mov rdx, {kind}")
        ctx.emit("call util_operate")



@dc
class AstIf:
    cond : AstExpr
    body : "AstStmt"

    def order(self): 
        self.cond = self.cond.order()
        self.body.order()

    def collect(self, ctx):
        self.body.collect(ctx)

    @classmethod
    def parse(cls, stream):
        stream.expect('if')
        cond = AstExpr.parse(stream)
        body = AstStmt.parse(stream)
        return cls(cond, body)

    def compile(self, ctx):
        skip_label = ctx.fresh()

        self.cond.compile(ctx)
        ctx.emit("mov rdi, rax")
        ctx.emit("call obj_dec_unwrap")
        ctx.emit("cmp rax, 0")
        ctx.emit(f"je {skip_label}")

        self.body.compile(ctx)

        ctx.emit(f"{skip_label}:")



@dc
class AstBlock:
    stmts : list["AstStmt"]

    class BlockClose: pass

    @classmethod
    def parse(cls, stream, prog=False):
        if not prog: stream.expect('{') #}

        stmts = []
        while stream.has():
            sub = AstStmt.parse(stream)
            if sub == cls.BlockClose: break
            stmts.append(sub)

        if not prog: stream.expect('}')
        return cls(stmts)

    def order(self):
        for stmt in self.stmts:
            stmt.order()

    def compile(self, ctx):
        for stmt in self.stmts:
            stmt.compile(ctx)

    def collect(self, ctx): 
        for stmt in self.stmts:
            stmt.collect(ctx)


@dc
class AstDecl:
    name : str 
    expr : AstExpr

    def order(self): self.expr = self.expr.order()

    @classmethod
    def parse(cls, stream):
        stream.pop() #first   storage classifier
        stream.pop() #seconed storage classifier
            
        name = stream.pop()

        if stream.peekt().kind == 'lifeopen':
            error.error('lifetimes not supported. send patches.')
        if stream.peek() == ':':
            error.error('type annotations not supported. send patches.')

        stream.expect('=')

        expr = AstExpr.parse(stream)

        return cls(
            name=name, 
            expr=expr, 
        )

    def collect(self, ctx):
        if self.name in ctx.scope.vars:
            error.error("Variable `{self.name}` declared multiple times.")

        ctx.scope.new(self.name)
            
    def compile(self, ctx):
        self.expr.compile(ctx)
        addr = ctx.scope.get(self.name)
        ctx.emit(f"mov [vars + {addr}], rax")






@dc
class AstAssign:
    dst : "AstScopeAccess | AstIndexAccess"
    src : "AstExpr"

    def collect(self, ctx): pass

    def order(self): 
        self.dst.order()
        self.src = self.src.order()

    @classmethod
    def parse(cls, stream):
        dst = AstScopeAccess.parse(stream)
        stream.expect('=')
        src = AstExpr.parse(stream)

        return cls(dst, src)

    @classmethod
    def parse_index_access(cls, stream):
        dst = AstIndexAccess.parse(stream)

        # for `array[index]?`
        if stream.peek() != '=':
            return dst

        stream.expect('=')
        src = AstExpr.parse(stream)

        return cls(dst, src)

    def compile(self, ctx):
        self.src.compile(ctx)
        self.dst.store(ctx)

@dc
class AstFuncDef:
    name : str
    params : list[str]
    body : AstBlock | AstExpr

    def order(self): 
        new = self.body.order()
        if type(self.body) is AstExpr:
            self.body = new

    @classmethod
    def parse(cls, stream):
        stream.pop()
        name = stream.pop()

        params = []
        while stream.peek() != '=':
            params.append(stream.pop())
            if stream.peek() == ',':
                stream.expect(',')
        stream.expect('=')
        stream.expect('>')

        if stream.peek() == '{': #}
            body = AstBlock.parse(stream)
        else:
            body = AstExpr.parse(stream)

        return cls(name, params, body)

    def compile(self, ctx):
        ctx.emit(f"{self.name}:")

        ctx.push_scope()
        for i, param_name in enumerate(self.params):
            addr = ctx.scope.new(param_name)
            reg = binding.ABI[i]
            ctx.emit(f"mov [vars + {addr}], {reg}")

        self.body.collect(ctx)
        for local_name in ctx.scope.vars:
            if local_name in self.params: continue
            addr = ctx.scope.get(local_name)

            # !! THIS IS REALLY REALLY IMPORTANT !!
            # this is called base-initialization.
            # if a variable is declare-initialized conditionally
            # this needs to be detectable by the runtime.
            ctx.emit(f"mov qword [vars + {addr}], 0")

        ctx.scope.return_label = ctx.fresh()

        ctx.emit("; body start")
        self.body.compile(ctx)
        ctx.emit("; body end")

        if type(self.body) is AstBlock:
            # if the function falls through,
            # return a undefined object.
            ctx.emit(f"mov rdi, {binding.KIND.UNDEFINED}")
            ctx.emit(f"mov rsi, {0xDEADBEEF}")
            ctx.emit("call obj_create")

        ctx.emit(f"{ctx.scope.return_label}:")
        ctx.emit("push rax")
        ctx.pop_scope()
        ctx.emit("pop rax")
        ctx.emit("ret")


@dc
class AstInline:
    expr : AstExpr

    def collect(self, ctx): pass

    @classmethod
    def parse(cls, stream):
        return cls(AstExpr.parse(stream))

    def order(self):
        self.expr = self.expr.order()

    def compile(self, ctx):
        self.expr.compile(ctx)

        # inline expression need to 
        # drop their return objects.
        # otherwise memory leak.

        ctx.emit("mov rdi, rax")
        ctx.emit("call obj_dec")

@dc
class AstReturn:
    expr : AstExpr

    def collect(self, ctx): pass

    @classmethod
    def parse(cls, stream):
        stream.expect('return')
        return cls(AstExpr.parse(stream))

    def order(self):
        self.expr = self.expr.order()

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(f"jmp {ctx.scope.return_label}")

@dc
class AstStmt:
    sub : typing.Any
    eos : str

    def _is_func_keyword(word):
        i = 0
        for char in 'function':
            if word[i] == char:
                i += 1

            if len(word) == i:
                return True

        return False
            

    def order(self): self.sub.order()

    def collect(self, ctx):
        self.sub.collect(ctx)

    @classmethod
    def parse(cls, stream):
        indent = stream.space()
        if indent % 3 != 0:
            error.token(stream.peekt(), "Invalid indentation. All indents must be 3 spaces long.")

        need_eos = True
        first, second = stream.lookhead(2)
        match first.content, second.content:
            case '}', _: return AstBlock.BlockClose
            case '{', _:  #}
                sub = AstBlock.parse(stream)
                need_eos = False
            case 'if', _: 
                sub = AstIf.parse(stream)
                need_eos = False
            case 'when', _:
                sub = AstWhen.parse(stream)
                need_eos = type(sub) is AstExpr
            case 'return', _:
                sub = AstReturn.parse(stream)

            case _, '[': #]
                sub = AstAssign.parse_index_access(stream)

            case _, '=':
                sub = AstAssign.parse(stream)

            case x, name if cls._is_func_keyword(x) and name.isalpha():
                sub = AstFuncDef.parse(stream)
                need_eos = type(sub.body) is AstExpr

            case x, y if all(i in ('const', 'var') for i in (x, y)):
                sub = AstDecl.parse(stream)

            case x:
                sub = AstInline.parse(stream)
    
        eos = None
        if need_eos:
            token = stream.popt()
            eos = token.content
            if token.kind not in ('eos', 'debug'):
                error.token(token, "End of line is not `!` or `?`.")

        if type(sub) is AstDecl:
            sub.priority = eos.count('!') - eos.count('¡')

        stream.space()
        return cls(sub, eos)

    def compile(self, ctx):
        
        match self.eos:
            case "?": 
                if type(self.sub) is AstInline:
                    self.sub = self.sub.expr

                ctx.push_scope()
                self.sub.compile(ctx)
                ctx.emit("mov rdi, rax")
                ctx.emit("call print")
                ctx.emit("mov rdi, rax")
                ctx.emit("call obj_dec")
                ctx.pop_scope()

            case _:
                self.sub.compile(ctx)
    


@dc
class AstProg:
    body : AstBlock

    @classmethod
    def load(cls, src):
        stream = lex.tokenize(src)

        body = AstBlock.parse(stream, prog=True)
        body.order()
        return cls(body)


    def compile(self):
        ctx = Ctx()

        ctx.header()
        self.body.compile(ctx)
        ctx.finalize()

        return ctx.output

            



