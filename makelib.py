import logging
import re

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
                    ('::=', self.parse_simple_expansion)  ]:
            if line.startswith(st[0]):
                return (st[1], line[len(st[0]):])
        return (None, line)

    def parse_default_setting(self, varname, value):
        logging.debug('Default %s to %s', varname, value)
        if varname not in self.allvars:
            var = self.get_variable(varname)
            parambranch = MakeLaneBranch (self.lane, self.context[-1], "{0:s} is defined as a parameter".format(varname))
            paramvalue = ("parameter", parambranch)
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
        self.expand_variable_overwrite(var, value)
        self.recursions.discard(var)

    def get_variable(self, varname):
        if varname not in self.allvars:
            var = MakeVariable(varname)
            self.allvars[varname] = var
            return var
        else:
            return self.allvars[varname]

    def expand_variable_overwrite(self, var, value):
        expansion = self.expand_value(value)
        var.values.clear()
        if len(expansion) == 0:
            var.values.append( (value, self.lane) )
        else:
            var.values.extend(expansion)

    def expand_variable_keep(self, var):
        values = list(var.values)
        var.values.clear()
        for (value , lane) in values:
            expansion = self.expand_value(value)
            if len(expansion) == 0:
                var.values.append( (value, lane) )
            else:
                for (expvalue, explane) in expansion:
                    var.values.append( (expvalue, MakeLaneJoin(lane, explane, self.context[-1]) ) )

    # if no expansion returns []
    def expand_value(self, value):
        logging.debug('Expanding value \"%s\"', value)
        i = value.find('$(')
        if i < 0 :
            return []
        pre = value[:i]
        (varname, value) = parse_variable(value[i+2:])
        if len(value) == 0:
            logging.error('Unexpected value end at %s', self.context[-1].istr )
        elif value[0] == ' ':
            return []
        elif value[0] == ')':
            if varname in self.allvars:
                return list( map( lambda x: (pre + x[0] + value[1:] , x[1]) , self.allvars[varname].values ) )
            else:
                return [ ( pre + value[1:] , self.lane ) ]
        else:
            logging.error('Unexpected symbol \"%s\" at %s, value=\"%s\"', value[0], self.context[-1].istr, value )
        return []

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
    varpattern = re.compile(r"\.?\w*")
    varmatch = varpattern.match(line)
    if varmatch.end() > 0:
        varname = varmatch.group()
        logging.debug('Variable %s from %s', varname, line)
        return (varname, line[varmatch.end():])
    else:
        return (None,line)

