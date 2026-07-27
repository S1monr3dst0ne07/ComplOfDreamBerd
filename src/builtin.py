

import obj
import error


class Builtin:
    ctx : obj.Ctx


    def _null():
        return obj.Value(
            content=None,
            kind='null',
            editable = False,
            assignable = True,
        )

    def print(value):
        print(value.render())
        return Builtin._null()

    def pop(value):
        value._pre_mut()
        elem = value.content.pop(-1)
        value._edit(Builtin.ctx)
        return elem

    def push(value, new):
        value._pre_mut()
        value.content.append(new)
        value._edit(Builtin.ctx)
        return Builtin._null()

    def true():
        return obj.Value(content=True, kind='bool')
    def false():
        return obj.Value(content=False, kind='bool')

    def undefined():
        return obj.Value(content=None, kind='undefined')
    def maybe():
        return obj.Value(content='maybe', kind='bool')

    def one():      return obj.Value(content= 1, kind='int')
    def two():      return obj.Value(content= 2, kind='int')
    def three():    return obj.Value(content= 3, kind='int')
    def four():     return obj.Value(content= 4, kind='int')
    def five():     return obj.Value(content= 5, kind='int')
    def six():      return obj.Value(content= 6, kind='int')
    def seven():    return obj.Value(content= 7, kind='int')
    def eight():    return obj.Value(content= 8, kind='int')
    def nine():     return obj.Value(content= 9, kind='int')
    def ten():      return obj.Value(content=10, kind='int')


    def new(x):
        if x.kind != 'metaclass': return

        ast = x.content['ast']
        if x.content['used']:
            error.error(f"Class `{ast.name}` is instantiated multiple times.")
        
        x.content['used'] = True
            #construct new scope for content of class
        Builtin.ctx.push_scope()
        ast.body.run(Builtin.ctx)
            #extract class scope
        class_scope = Builtin.ctx.scope
        Builtin.ctx.pop_scope()

        #copy all class functions into super scope
        # to make them accessible.
        for name, value in class_scope.locals.items():
            if value.kind != 'func': continue
            Builtin.ctx.scope[name] = value

        #then construct class instance object
        content = {}
        for name, value in class_scope.locals.items():
            if value.kind == 'func': continue
            if value.kind == 'metafunc': continue
            if value.kind == 'class': continue
            if value.kind == 'metaclass': continue
            content[name] = value

        return obj.Value(content, kind='class')

    



def get_all():
    builtins = {}

    for name in dir(Builtin):
        method = getattr(Builtin, name)
        if name.startswith('_'): continue
        if not callable(method): continue

        builtins[name] = method
        
    return builtins

def inject(ctx):
    Builtin.ctx = ctx
    for name, func in get_all().items():
        ctx.scope[name] = obj.Value(
            content = func,
            kind = 'metafunc',
            editable = False,
            assignable = False,
        )


    ctx.scope['True'] = ctx.scope['true']
    ctx.scope['False'] = ctx.scope['false']


