
import typing
import time
import regex
from dataclasses import dataclass as dc

import lex
import error
import sym
from ctx import Ctx



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

    def compile(self, ctx):
        if self.iden in ctx.scope:
            ctx.builder.call()



@dc
class AstLitArray:
    elems : list["AstExpr"]

    def order(self):
        for i, elem in enumerate(self.elems):
            self.elems[i] = elem.order()

    @classmethod
    def parse(cls, stream):
        stream.expect('[') #]
        elems = []

        while stream.peek() != ']':
            elems.append(AstExpr.parse(stream))
            if stream.peek() == ',':
                stream.expect(',')
        stream.expect(']')

        return cls(elems)

@dc
class AstLitDict:
    def order(self): pass

    @classmethod
    def parse(cls, stream):
        stream.expect("{")
        stream.expect("}")

        return cls()

@dc
class AstIndexAccess:
    name : str
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



@dc
class AstLeaf:
    kind : str
    value : typing.Any

    def infer(self): pass
    def order(self):
        if self.kind in ('scope', 'index'):
            self.value.order()

        return self

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
                """
                leaf = int(stream.pop())
                kind = 'int'
                if stream.peekt().kind == 'dot':
                    stream.pop()
                    leaf += float(f"0.{stream.pop()}")
                    kind = 'float'
                
                value = obj.Value(leaf, kind)
                """

            case 'quote': 
                content = cls._parse_string(stream)
                return cls('string', content)
                
            case 'arrayopen': pass
                #value = AstLitArray.parse(stream)
            case 'blockopen': pass
                #value = AstLitDict.parse(stream)

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

    def compile(self, ctx):
        match self.kind:
            case 'string':
                label = ctx.fresh()
                ctx.emit(f"mov rax, {label}")
                ctx.strings[label] = self.value

            case 'scope':
                #self.value.compile(ctx)
                pass


            case x: print("todo impl leaf kind: ", self.kind)


@dc
class AstUn:
    op : str
    sub : AstLeaf

    def order(self): 
        return self

    def infer(self): pass

    @classmethod
    def parse(cls, stream):
        if stream.peek() not in sym.un_op:
            return AstLeaf.parse(stream)

        op = stream.pop()
        stream.space() #the spec makes no mention of unary operator separation 
        sub = AstLeaf.parse(stream)
        return cls(op, sub)

    def run(self, ctx):
        sub = self.sub.run(ctx)
        value = sub.content

        match self.op:
            case ';': res = not value
            case '-': res = -value

        return obj.Value(content=res, kind=sub.kind)

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


    def infer(self): pass
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





@dc
class AstIf:
    cond : AstExpr
    body : "AstStmt"

    def order(self): 
        self.cond = self.cond.order()
        self.body.order()
    def infer(self):
        self.body.infer()

    @classmethod
    def parse(cls, stream):
        if 'if' in deleted_features:
            error.error("Feature `if` has been deleted.")

        stream.expect('if')
        cond = AstExpr.parse(stream)
        body = AstStmt.parse(stream)
        return cls(cond, body)

    def run(self, ctx):
        cond = self.cond.run(ctx).content
        if cond not in (True, False):
            error.error(f"Indecisive condition: `{cond.render()}`")

        if cond:
            self.body.run(ctx)

@dc
class AstWhen:
    cond : AstExpr
    body : "AstStmt"

    def order(self): 
        self.cond = self.cond.order()
        self.body.order()
    def infer(self):
        self.body.infer()

    @classmethod
    def parse(cls, stream):
        if 'when' in deleted_features:
            error.error("Feature `when` has been deleted.")

        stream.expect('when')
        cond = AstExpr.parse(stream)
        body = AstStmt.parse(stream)
        return cls(cond, body)

    def run(self, ctx):
        for dep in self.cond.vars():
            if dep not in ctx.scope.when:
                ctx.scope.when[dep] = []

            ctx.scope.when[dep].append(self)

    def check(self, ctx):
        if self.cond.run(ctx).content:
            self.body.run(ctx)


@dc
class AstBlock:
    stmts : list["AstStmt"]

    stmt_alive : list[set] #which vars alive during statement
    stmt_dead  : list[set] #"-" dead "-"

    #declaration have to be executed as soon as their lifetime starts 
    decl_init  : dict[str, "AstDecl"]

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
        return cls(stmts, [], [], {})

    def order(self):
        for stmt in self.stmts:
            stmt.order()


    def infer(self):
        self.stmt_alive = [set() for _ in self.stmts]
        relevent_stmts = [
            stmt for stmt in self.stmts 
            if type(stmt.sub) is AstDecl and
            stmt.sub.lifetime is not None and
            stmt.sub.lifetype == 'stmt'
        ]

        for stmt in relevent_stmts:
            decl = stmt.sub
            self.decl_init[decl.name] = decl

        #compute which variables are alive during each statement
        for index, stmt in enumerate(self.stmts):
            if stmt not in relevent_stmts: continue
            decl = stmt.sub

            timetravel = decl.lifetime < 0
            offset_offset = (-1 if timetravel else 1)
            offset = offset_offset
            for _ in range(abs(decl.lifetime)):
                target = index + offset
                if abs(target) < len(self.stmt_alive):
                    self.stmt_alive[target].add(decl.name)
                offset += offset_offset

        #compute compliment (insert deep quote about yin and yang or smth)
        for index, stmt in enumerate(self.stmts):
            self.stmt_dead.append(set(
                varname for varname in [x.sub.name for x in relevent_stmts]
                if varname not in self.stmt_alive[index]
            ))

        #recursive infer
        for stmt in self.stmts:
            stmt.infer()

    def compile(self, ctx):
        for stmt in self.stmts:
            stmt.compile(ctx)



@dc
class AstClass:
    name : str
    body : "AstBlock"

    def order(self): self.body.order()
    def infer(self): self.body.infer()

    @classmethod
    def parse(cls, stream):
        if 'class' in deleted_features:
            error.error("Feature `class` has been deleted.")

        stream.pop() # `class` or `className`

        name = stream.pop()
        body = AstBlock.parse(stream)
        return cls(name, body)








@dc
class AstDecl:
    editable   : bool
    assignable : bool
    name : str 
    expr : AstExpr

    lifetime : int | None
    lifetype : typing.Literal['default', 'stmt', 'sec', 'infty'] 

    # how many exclaimation mark
    priority : int = 0


    def order(self): self.expr = self.expr.order()
    def infer(self): pass



    @classmethod
    def parse(cls, stream):
        first_storage_type = stream.pop()
        if stream.peek() not in ('const', 'var'):
            error.token(stream.pop(), "`const` / `var` not followed by `const` / `var`.")
        second_storage_type = stream.pop()

        assignable = {'const' : False, 'var' : True}[first_storage_type]
        editable   = {'const' : False, 'var' : True}[second_storage_type]

        # new for 2023!
        eternal = False
        if not assignable and not editable and stream.peek() == 'const':
            stream.expect('const')
            eternal = True
            
        name = stream.pop()

        lifetime = None
        lifetype = 'default'

        if stream.peekt().kind == 'lifeopen':
            lifetype = 'stmt'
            stream.expect('<')

            if stream.peek() == 'Infinity':
                stream.pop()
                lifetype = 'infty'

            sign = stream.peek() == '-'
            if sign: stream.expect('-')

            if stream.peek().isdigit():
                lifetime = int(stream.pop()) * (-1 if sign else 1)

            if stream.peek() == 's':
                stream.expect('s')
                lifetype = 'sec'

            stream.expect('>')

        #type annotation
        if stream.peek() == ':':
            stream.expect(':')
            word = stream.pop()

            reregegexx = regex.compile("Reg(ular)?[eE]x(p(ression)?)?")
            if not reregegexx.match(word):
                while stream.peek() != '=': stream.pop()
            else:
                stream.expect("<")
                while stream.pop() != '>': pass

        stream.expect('=')

        expr = AstExpr.parse(stream)
        return cls(
            editable=editable, 
            assignable=assignable, 
            name=name, 
            expr=expr, 
            lifetime=lifetime, 
            lifetype=lifetype
        )



    def run(self, ctx):
        init = self.expr.run(ctx)

        init.editable = self.editable
        init.assignable = self.assignable

        for name in self.names:
            # make priority is followed
            if name in ctx.scope:
                if ctx.scope[name].priority > self.priority:
                    return

            ctx.scope[name] = init
            ctx.scope[name].lifetime = self.lifetime
            ctx.scope[name].lifetype = self.lifetype
            ctx.scope[name].priority = self.priority

            # register local creation time
            ctx.scope[name].time_born = time.time()

            # upload variable to database if eternal
            if self.eternal: ctx.eternal_upload(name)
            
    def compile(self, ctx):
        init = self.expr.compile(ctx)
        ctx.scope[self.name] = init






@dc
class AstAssign:
    dst : "AstScopeAccess | AstIndexAccess"
    src : "AstExpr"

    def order(self): 
        self.dst.order()
        self.src = self.src.order()

    def infer(self): pass

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

@dc
class AstFuncDef:
    name : str
    params : list[str]
    body : AstBlock | AstExpr

    def order(self): 
        new = self.body.order()
        if type(self.body) is AstExpr:
            self.body = new

    def infer(self):
        self.body.infer()

    @classmethod
    def parse(cls, stream):
        if 'function' in deleted_features:
            error.error("Functions have been deleted.")

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
            

    def infer(self): self.sub.infer()
    def order(self): self.sub.order()

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

            case ('class', _) | ('className', _):
                sub = AstClass.parse(stream)
                need_eos = False

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
                sub = AstExpr.parse(stream)
    
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
        res = self.sub.compile(ctx)
        
        match self.eos:
            case "?": print("implemented debug");

        return res



    


@dc
class AstProg:
    body : AstBlock

    @classmethod
    def load(cls, src):
        stream = lex.tokenize(src)

        body = AstBlock.parse(stream, prog=True)
        body.order()
        body.infer()
        return cls(body)


    def compile(self):
        ctx = Ctx()
        
        ctx.header()
        self.body.compile(ctx)
        ctx.finalize()

        return ctx.output

            



