# hqbot - a bot for moderating twitchtv chats
# Copyright (C) 2012  Yann Kaiser
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import re
from collections import namedtuple
from inspect import stack

Initializer = namedtuple('Initializer', ('fn', 'module'))
inits = []
def init(fn):
    inits.append(Initializer(fn, _get_module_name()))
    return fn

Command = namedtuple('Command', ('fn', 'module', 'lvl'))
commands = {}
def command(fn=None, lvl=0):
    def apply(fn):
        commands[fn.func_name] = Command(fn, _get_module_name(), lvl)
        return fn
    if fn:
        return apply(fn)
    else:
        return apply
command.OP = 1
command.OWNER = 2

Scanner = namedtuple('Scanner', ('fn', 'module', 'types'))
scanners = []
def scanner(fn=None, types=3):
    def apply(fn):
        scanners.append(Scanner(fn, _get_module_name(), types))
        return fn
    if fn:
        return apply(fn)
    else:
        return apply
scanner.MSG = 1
scanner.ACTION = 2
scanner.CHAT = scanner.MSG | scanner.ACTION

Cron = namedtuple('Cron', ('fn', 'module', 'interval'))
cronjobs = []
def cron(fn=None, interval=60*60):
    def apply(fn):
        cronjobs.append(Cron(fn, _get_module_name(), interval))
        return fn
    if fn:
        return apply(fn)
    else:
        return apply

_module_name = re.compile(r'^pyhqbot\.modules\.(?P<name>[^.]+)(?:\.(?P<submodule>.*))?$')
def _get_module_name():
    for item in stack():
        try:
            module = item[0].f_locals['__name__']
        except KeyError:
            pass
        else:
            m = _module_name.match(module)
            if m:
                return m.group('name')

def dump():
    print inits, commands, scanners, cronjobs
