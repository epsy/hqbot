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


import inspect
from time import time
from contextlib import contextmanager

from twisted.internet import protocol, reactor
from twisted.words.protocols import irc
from twisted.python import log

from pyhqbot import register

@contextmanager
def log_errors(logger=log.err):
    try:
        yield
    except Exception:
        logger()

class Bot(irc.IRCClient):
    lineRate = 1

    @property
    def username(self):
        return self.factory.user

    @property
    def password(self):
        return self.factory.password

    @property
    def ircchannel(self):
        return '#' + self.factory.channel

    @property
    def owner(self):
        return self.factory.channel

    @property
    def storage(self):
        return self.factory.storage

    def __init__(self, nickname):
        self.nickname = nickname
        self.ops = set()
        self.next_cronjobs = {}

    def signedOn(self):
        self.join(self.ircchannel)
        self.run_init()
        log.msg("Signed on...")

    def run_init(self):
        for init in register.inits:
            call = Call(self, init.module)
            call.init(init)

    def joined(self, channel):
        if channel != self.ircchannel:
            log.warn("Odd, I shouldn't be joining " + channel)
            return

        self.run_cronjobs()

        log.msg("Joined channel")

    def echo(self, message):
        self.say(self.ircchannel, message)

    def modeChanged(self, user, channel, set, modes, args):
        if channel != self.ircchannel:
            return # only care about changes in our channel
        for mode, arg in zip(modes, args):
            if mode == 'o':
                if set:
                    self.ops.add(arg)
                else:
                    self.ops.discard(arg)

    def userRenamed(self, old, new):
        if old in self.ops:
            self.ops.remove(old)
            self.ops.add(new)

    def userLeft(self, user, channel):
        if not channel or channel == self.ircchannel:
            nick = user.split('!')[0]
            self.ops.discard(nick)

    def userKicked(self, user, channel, operator, message):
        self.userLeft(user, channel)

    def userQuit(self, user, message):
        self.userLeft(user, '')

    def privmsg(self, user, channel, message):
        if channel != self.ircchannel:
            return

        if message.startswith('!'): #command
            self.run_command(user, message)

        #hand it to scanners
        self.run_scanners(user, message, register.scanner.MSG)

    def action(self, user, channel, message):
        if channel != self.ircchannel:
            return

        self.run_scanners(user, message, register.scanner.ACTION)

    def run_command(self, user, message):
        args = message[1:].split()
        try:
            command = args[0].lower()
        except IndexError:
            return

        if command in register.commands:
            cmdinfo = register.commands[command]
            call = Call(self, cmdinfo.module)
            call.command(cmdinfo, user, args)
        else:
            pass # no such command

    def run_scanners(self, user, message, type):
        for scanner in register.scanners:
            if type & scanner.types:
                call = Call(self, scanner.module)
                call.scan(scanner, user, message, type)

    def run_cronjobs(self):
        for job in register.cronjobs:
            time_next = self.next_cronjobs.get(job, 0)
            if time_next <= time():
                if time_next:
                    self.run_cronjob(job)
                self.next_cronjobs[job] = time() + job.interval
        next_cronjob_time = min(self.next_cronjobs.values())
        reactor.callLater(next_cronjob_time - time(), self.run_cronjobs)

    def run_cronjob(self, job):
        call = Call(self, job.module)
        call.cron(job)


class Call(object):
    def __init__(self, bot, module):
        self.bot = bot
        self.module = module
        self.storage = bot.storage.part(module)

    @property
    def nick(self):
        return self.originator.split('!', 1)[0]

    def reply(self, message):
        self.bot.echo("{0}: {1}".format(self.nick, message))

    def init(self, init):
        init.fn(self)

    def command(self, cmd, user, args):
        self.originator = user

        if not self._check_level(self.nick, cmd.lvl):
            print "{0} did not have privilege".format(user, cmd.lvl)
            return

        try:
            inspect.getcallargs(cmd.fn, self, *args)
        except TypeError:
            self.reply("Bad arguments for {0}".format(cmd.fn.func_name))
            return

        with log_errors():
            ret = cmd.fn(self, *args)

            if ret:
                self.reply(ret)

    def _check_level(self, nick, level):
        if level >= register.command.OWNER and nick != self.bot.owner:
            return False
        elif level >= register.command.OP and nick not in self.bot.ops:
            return False
        return True

    def scan(self, scanner, user, message, type):
        self.originator = user
        with log_errors():
            scanner.fn(self, message, type)

    def cron(self, job):
        with log_errors():
            job.fn(self)

class BotFactory(protocol.ClientFactory):
    protocol = Bot

    def __init__(self, channel, user, password, storage):
        self.channel = channel.lower()
        self.user = user.encode('utf-8')
        self.password = password.encode('utf-8')
        self.storage = storage

    @property
    def host(self):
        return "{0}.jtvirc.com".format(self.channel)
    port = 6667

    def buildProtocol(self, addr):
        p = self.protocol(self.user)
        p.factory = self
        return p

    def stopFactory(self):
        self.storage.save()

    def clientConnectionFailed(self, connector, reason):
        reactor.callLater(30, connector.connect)

    def clientConnectionLost(self, connector, reason):
        reactor.callLater(3, connector.connect)
