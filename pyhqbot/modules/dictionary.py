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
from time import time

from pyhqbot.register import init, command, scanner

@init
def create_storage(call):
    if not call.storage:
        call.storage.update({
            'words': {},
            })
        call.storage.save()

@command(lvl=command.OP)
def define(call, cmd, name, *definition):
    call.storage['words'][name.lower()] = ' '.join(definition)
    call.reply("Defined \"{0}\".".format(name))

@command(lvl=command.OP)
def undefine(call, cmd, name):
    try:
        del call.storage['words'][name.lower()]
    except KeyError:
        call.reply("\"{0}\" was not defined.".format(name))
    else:
        call.reply("Undefined \"{0}\".".format(name))

@command(lvl=command.OP)
def terms(call, cmd):
    if call.storage['words']:
        return ', '.join(call.storage['words'])
    else:
        return "No terms defined."

@command(lvl=command.OP)
def term(call, cmd, name):
    return call.storage['words'].get(
        name, "Sorry, \"{0}\" is not defined.".format(name))

@command(lvl=command.OP)
def tell(call, cmd, victim, term):
    try:
        definition = call.storage['words'][term.lower()]
    except KeyError:
        return "Sorry, \"{0}\" is not defined.".format(term)
    else:
        call.bot.echo("{0}: {1}".format(victim, definition))

word_re = re.compile(r'^(?P<excl>!)?(?P<word>\w+)(?(excl)|\?)$')

@scanner(types=scanner.MSG)
def wordsnooper(call, line, type):
    match = word_re.match(line)
    if match:
        word = match.group('word').lower()
        try:
            definition = call.storage['words'][word]
        except KeyError:
            return
        if call.nick in call.bot.ops or check_rate(call.storage, word):
            call.reply(definition)

MIN_ELAPSE_REPEAT = 60
def check_rate(storage, word):
    return False # remove if not only operators can use this
    ts = time()
    if ts < MIN_ELAPSE_REPEAT + storage['last'].get(word, 0):
        return False
    else:
        storage['last'][word] = ts
        return True
