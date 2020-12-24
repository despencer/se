import logging
import re
import makefuncs as mf

def parse(filename):
    parser = MakeParser()
    return parser.parsefile(filename)

class MakeParser:

    def __init__(self):
        logging.info('-'*80)
        logging.info('Makefile parsing started')
        self.tokens = [ ("-include", lambda s, x: s.parse_include(x, True)),
                        ("include", lambda s, x: s.parse_include(x, False)) ]
        self.context = []
        self.allvars = {}
        self.recursions = set()

    def parsefile(self, filename):
        logging.info('Parsing %s', filename)
        self.context.append(MakeParserContext(filename))
        self.lane = MakeLane(self.context[-1])
        mflist = self.get_variable("MAKEFILE_LIST")
        mflist.values.append( (filename, self.lane) )
        with open(filename) as f:
            lines = f.readlines()
        concat = ''
        for i, l in enumerate(lines):
            if l[-1] == '\n':
                l = l[:-1]
            if filter_empty (l):
                continue
            if l[-1] == '\\':
                concat = concat + l[:-1]
                continue
            self.context[-1].line = l
            self.context[-1].istr = i+1
            self.parse_line (concat + l)
            concat = ''
        if len(concat) > 0:
            parse_line (self, concat)
        for v in self.recursions:
            self.expand_variable_keep(v)
        return MakeData (self.allvars)

    def parse_line (self, line):
        if self.parse_tokens(line):
            pass
        elif self.parse_setting_or_target (line):
            pass
        else:
            logging.error("Can't select at %s: %s", self.context[-1].istr, line)

    def parse_tokens (self, line):
        for tk in self.tokens:
           if line.lstrip().startswith(tk[0]):
               tk[1](self, line)
               return True
        return False

    def parse_setting_or_target (self, line):
        ieq = line.find('=')
        icol = line.find(':')
        if ieq >= 0 and icol >= 0:
            if line[icol:icol+2] == ':=' or line[icol:icol+3] == ':==' :
                self.parse_setting (line)
            else:
                logging.error('Mixed variable and rule line: %s', line)
        elif ieq >= 0:
            self.parse_setting (line)
        elif icol >= 0:
            self.parse_target (line)
        else:
            return False
        return True

    def parse_setting (self, line):
        logging.debug('Processing setting %s', line)
        goon = True
        (varname, line) = parse_variable(line)
        if varname == None:
            goon = False
            logging.error('Bad variable name at %s %s', self.context[-1].istr, line)
        if goon:
            (setfunc, line) = self.get_setting_type(line.lstrip())
            if setfunc == None:
                goon = False
                logging.error('Bad setting type at %s %s', self.context[-1].istr, line)
        if goon:
            setfunc(varname, line.lstrip())

    def get_setting_type (self, line):
        for st in [ ('?=', self.parse_default_setting),
                    ('=',  self.parse_recursive_expansion),
                    (':=', self.parse_simple_expansion),
                    ('::=', self.parse_simple_expansion),
                    ('+=', self.parse_addition)  ]:
            if line.startswith(st[0]):
                return (st[1], line[len(st[0]):])
        return (None, line)

    def parse_default_setting(self, varname, value):
        logging.debug('Default %s to %s', varname, value)
        if varname not in self.allvars:
            var = self.get_variable(varname)
            parambranch = MakeLaneBranch (self.lane, self.context[-1], "{0:s} is defined as a parameter".format(varname))
            paramvalue = ("#par({0:s})".format(varname), parambranch)
            var.values.append(paramvalue)
            defbranch = MakeLaneBranch (self.lane, self.context[-1], "{0:s} is not defined as a parameter".format(varname))
            defvalue = (value, defbranch)
            var.values.append(defvalue)
            self.recursions.add(var)

    def parse_recursive_expansion(self, varname, value):
        logging.debug('Recursive %s to %s', varname, value)
        var = self.get_variable(varname)
        var.values.clear()
        var.values.append( (value, self.lane) )
        self.recursions.add(var)

    def parse_simple_expansion (self, varname, value):
        logging.debug('Simple %s to %s', varname, value)
        var = self.get_variable(varname)
        self.recursions.discard(var)
        self.expand_variable_overwrite(var, value)

    def parse_addition (self, varname, value):
        logging.debug('Addition \"%s\" with \"%s\"', varname, value)
        if varname not in self.allvars:
            self.parse_recursive_expansion(varname, value)
        else:
            var = self.allvars[varname]
            if var in self.recursions:
                oldval = var.values
                var.values = list( map ( lambda x: (x[0]+value, x[1]), oldval) )
            else:
                values = list(var.values)
                var.values.clear()
                for (preval , lane) in values:
                    expansion = self.expand_value(preval + value, [ varname ] )
                    if len(expansion) == 0:
                        var.values.append( (preval + value, lane) )
                    else:
                        for (expvalue, explane) in expansion:
                            var.values.append( (expvalue, MakeLaneJoin(lane, explane, self.context[-1]) ) )
        logging.debug('Addition \"%s\" processed"', varname)

    def get_variable(self, varname):
        if varname not in self.allvars:
            var = MakeVariable(varname)
            self.allvars[varname] = var
            return var
        else:
            return self.allvars[varname]

    def expand_variable_overwrite(self, var, value):
        expansion = self.expand_value(value, [ var.name ])
        var.values.clear()
        if len(expansion) == 0:
            logging.debug('Variable %s simple set to %s', var.name, value)
            var.values.append( (value, self.lane) )
        else:
            logging.debug('Variable %s simple set to %s', var.name, expansion)
            var.values.extend(expansion)

    def expand_variable_keep(self, var):
        values = list(var.values)
        var.values.clear()
        for (value , lane) in values:
            expansion = self.expand_value(value, [ var.name ])
            if len(expansion) == 0:
                var.values.append( (value, lane) )
            else:
                for (expvalue, explane) in expansion:
                    var.values.append( (expvalue, MakeLaneJoin(lane, explane, self.context[-1]) ) )

    def expand_value(self, value, varstack):
        logging.debug('Expanding value \"%s\, varstack=%s"', value, varstack)
        step = self.expand_value_step(value, varstack)
        if len(step) == 0:
            return []
        total = []
        for (expvalue, explane) in step:
            again = self.expand_value(expvalue, varstack)
            if len(again) == 0:
                total.append( (expvalue, explane) )
            else:
                for (avalue, alane) in again:
                    total.append( (avalue, MakeLaneJoin(explane, alane, self.context[-1]) ) )
        return total

    # if no expansion returns []
    def expand_value_step(self, value, varstack):
        logging.debug('Expanding value stepping \"%s\", varstack=%s', value, varstack)
        i = value.find('$(')
        if i < 0 :
            return []
        pre = value[:i]
        (varname, value) = parse_variable(value[i+2:])
        if len(value) == 0:
            logging.error('Unexpected value end at %s', self.context[-1].istr )
        elif value[0] == ' ':
            return self.expand_function_call(varname, value[1:], varstack)
        elif value[0] == ')':
            if varname in self.allvars:
                if len(self.allvars[varname].values) > 0:
                    total = []
                    logging.debug('Going recursive for \"%s\" of %s, varstack %s', varname, self.allvars[varname].values, varstack)
                    for (expval,explane) in self.allvars[varname].values:
                        recurs = []
                        if self.allvars[varname] in self.recursions:
                            if varname in varstack:
                                logging.error('Unfinite recursion found for variable %s', varname )
                            else:
                                varstack.append(varname)
                                recurs = self.expand_value(expval, varstack)
                                varstack.pop()
                        if len(recurs) == 0:
                            total.append( (pre + expval + value[1:], explane) )
                        else:
                            total.extend( map( lambda x: (pre + x[0] + value[1:] , MakeLaneJoin(explane, x[1], self.context[-1])) , recurs ))
                    logging.debug('Back from recursive for \"%s\", varstack %s', varname,  varstack)
                    return total
            else:
                logging.warning('Undefined variable %s', varname)
            return [ ( pre + value[1:] , self.lane ) ]
        else:
            logging.error('Unexpected symbol \"%s\" at %s, value=\"%s\"', value[0], self.context[-1].istr, value )
        return []

    def expand_function_call(self, funcname, value, varstack):
        logging.debug('Expand function \"%s\" with \"%s\"', funcname, value)
        calls = [ MakeFunctionCall(value, self.lane) ]
        icurr = 0
        while icurr < len(calls):
            (ipos, symb) = parse_func_token(calls[icurr].line)
            logging.debug('Get symbol \"%s\" at %s', symb, ipos)
            if symb == '$':
                calls.extend( calls[icurr].addvalue( calls[icurr].line[:ipos], self.expand_value(calls[icurr].line[ipos:], varstack), self.context[-1]) )
            elif symb == ',':
                calls[icurr].makeargument(ipos)
            else:
                calls[icurr].makeargument(ipos)
                icurr = icurr + 1
        return list ( map( lambda x: x.makecall(funcname, self.context[-1]) , calls) )

    def parse_target (self, line):
        logging.debug('Processing target %s', line)

    def parse_include (self, line, silent):
        logging.debug('Processing (silent=%s) include %s', silent, line)

class MakeParserContext:
    def __init__(self, f):
        self.filename = f
        self.istr = 0

class MakeLane:
    def __init__(self, context):
        self.filename = context.filename
        self.istr = context.istr

    def __eq__(self, other):
        if isinstance(other, MakeLane):
            return filename == other.filename and istr == other.istr
        return false

class MakeLaneBranch (MakeLane):
    def __init__(self, parent, context, condition):
        MakeLane.__init__(self, context)
        self.parent = parent
        self.condition = condition

class MakeLaneJoin (MakeLane):
    def __init__(self, parent1, parent2, context):
        MakeLane.__init__(self, context)
        self.parent1 = parent1
        self.parent2 = parent2

class MakeVariable:
    def __init__(self, n):
        self.name = n
        self.values = []         # (value, lane)

    def formatverbose(self):
        ret = self.name + "\n"
        for v in self.values:
            ret = ret + "    {0:s}@{1:d} = '{2:s}'\n".format(v[1].filename, v[1].istr, v[0])
        return ret

class MakeFunctionCall:
    def __init__(self, line, lane):
        self.lane = lane
        self.line = line
        self.callargs = []
        self.funcs = mf.allfuncs()

    def addvalue(self, prefix, expands, context):
        orglane = self.lane
        self.lane = MakeLaneJoin(orglane, expands[0][1], context)
        self.line = prefix + expands[0][0]
        newcalls = []
        for (eline, elane) in expands[1:]:
            nc = MakeFunctionCall( prefix + eline, MakeLaneJoin(orglane, elane, context) )
            nc.callargs = list(self.callargs)
            newcalls.append( nc )
        return newcalls

    def makeargument(self, ipos):
        self.callargs.append( self.line[:ipos].replace('$$', '$') )
        self.line = self.line[ipos+1:]

    def makecall(self, funcname, context):
        logging.debug('Make call \"%s\" with %s arguments', funcname, len(self.callargs))
        for a in self.callargs:
            logging.debug('Make call argument \"%s\"', a)
        if funcname in self.funcs:
            ret = self.funcs[funcname](self.callargs, context);
            if isinstance(ret, tuple):
                logging.debug('Call returns \"%s\"', ret[0])
                return (ret[0] + self.line, ret[1])
            else:
                logging.debug('Call returns \"%s\"', ret)
                return (ret + self.line, self.lane)
        logging.error('Function \"%s\" not found', funcname)
        return (self.line, self.lane)

class MakeData:
    def __init__(self, variables):
        self.variables = variables

def filter_empty (line):
    if len(line) == 0:
        logging.debug("Get empty ")
        return True
    elif line[0] == '#':
        logging.debug("Get comment: %s", line)
        return True
    return False

def parse_variable(line):
    varpattern = re.compile(r"\.?[\w-]*")
    varmatch = varpattern.match(line)
    if varmatch.end() > 0:
        varname = varmatch.group()
        logging.debug('Variable %s from %s', varname, line)
        return (varname, line[varmatch.end():])
    else:
        return (None,line)

def parse_func_token(line):
    buf = [ (len(line), ')' ) ]
    for c in ['$' , ',' , ')' ]:
        ipos = line.find(c)
        while c == '$' and line[ipos:ipos+2] == '$$':    # special case of '$$' should be skipped
            ipos = line.find(c, ipos+2)
        if ipos >= 0 and ipos < buf[-1][0]:
            buf.append( (ipos, c) )
    if buf[-1][0] == len(line):
        logging.error('No ending symbols for function at \"%s\"', line)
    return buf[-1]