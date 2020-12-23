import logging
import re
import os
import glob
import makelib as ml

def allfuncs ():
    return { "wildcard" : wildcard,
             "firstword" : firstword,
             "lastword" : lastword,
             "dir" : mkfdir,
             "patsubst" : patsubst }

def wildcard (args, context):
    if len(args) != 1:
        logging.error('Function wildcard takes 1 argument, get %s', len(args))
        return ""
    return (' '.join(glob.glob(args[0])), ml.MakeLane(context))

def firstword (args, context):
    if len(args) != 1:
        logging.error('Function lastword takes 1 argument, get %s', len(args))
        return ""
    return re.split(r'\s',args[0].strip())[0]

def lastword (args, context):
    if len(args) != 1:
        logging.error('Function lastword takes 1 argument, get %s', len(args))
        return ""
    return re.split(r'\s',args[0].strip())[-1]

def mkfdir(args, context):
    if len(args) != 1:
        logging.error('Function dir takes 1 argument, get %s', len(args))
        return ""
    path = os.path.dirname(args[0])
    if(path == ''):
        path = '.'
    return path + "/"

def patsubst(args, context):
    if len(args) != 3:
        logging.error('Function patsubst takes 3 argument, get %s', len(args))
        return ""
    words = re.split(r'\s',args[2].strip())
    ipatpos = args[0].find('%')
    if ipatpos < 0:
        parser = lambda x: patsimple(x, args[0], args[1])
    else:
        ireplpos = args[1].find('%')
        if ireplpos < 0:
            parser = lambda x: patmatcher(x, args[0][:ipatpos], args[0][ipatpos+1:], args[1], False, '')
        else:
            parser = lambda x: patmatcher(x, args[0][:ipatpos], args[0][ipatpos+1:], args[1][:ireplpos], True, args[1][ireplpos+1:])
    return " ".join(map (parser, words) )

def patsimple(word, pattern, repl):
    if word == pattern:
        return repl
    else:
        return word

def patmatcher(word, prefix, suffix, replprefix, replmatch, replsuffix):
    if not (word.startswith(prefix) and word.endswith(suffix) ):
        return word
    if len(word) < (len(prefix)+len(suffix)):
        return word
    if replmatch:
        if suffix == "":
            return replprefix + word[len(prefix):] + replsuffix
        else:
            return replprefix + word[len(prefix):-len(suffix)] + replsuffix
    else:
        return replprefix + replsuffix
