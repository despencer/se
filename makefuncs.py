import logging

def allfuncs ():
    return { "wildcard" : wildcard }

def wildcard (args):
    if len(args) != 1:
        logging.error('Function wildcard takes 1 argument, get %s', len(args))
        return ""
    return "#files"
