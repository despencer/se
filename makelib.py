import logging

def parse(filename):
    parser = MakeParser()
    parser.parsefile(filename)

class MakeParser:

    def __init__(self):
        logging.info('-'*80)
        logging.info('Makefile parsing started')
        self.tokens = [ ("-include", lambda s, x: s.parse_include(x, True)),
                        ("include", lambda s, x: s.parse_include(x, False)) ]

    def parsefile(self, filename):
        logging.info('Parsing %s', filename)
        with open(filename) as f:
            lines = f.readlines()
        concat = ''
        for l in lines:
            if l[-1] == '\n':
                l = l[:-1]
            if filter_empty (l):
                continue
            if l[-1] == '\\':
                concat = concat + l[:-1]
                continue
            self.parse_line (concat + l)
            concat = ''
        if len(concat) > 0:
            parse_line (self, concat)

    def parse_line (self, line):
        if self.parse_tokens(line):
            pass
        elif self.parse_setting_or_target (line):
            pass
        else:
            logging.error("Can't select: %s", line)

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

    def parse_target (self, line):
        logging.debug('Processing target %s', line)

    def parse_include (self, line, silent):
        logging.debug('Processing (silent=%s) Dinclude %s', silent, line)

def filter_empty (line):
    if len(line) == 0:
        logging.debug("Get empty ")
        return True
    elif line[0] == '#':
        logging.debug("Get comment: %s", line)
        return True
    return False

