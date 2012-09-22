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


from clize import clize

@clize
def launch(
        channel,
        credentials="./credentials.json",
        persistence="./persistence.pickle",
        *modules):
    """Starts a TwitchTV irc moderator bot in channel

    channel: the channel to join

    credentials: where to look for a ["login", "password"] file

    persistence: where to keep persistent data

    modules: hooks to load"""
    import sys
    from twisted.python import log
    log.startLogging(sys.stdout)
    from twisted.internet import reactor
    from pyhqbot.irc import BotFactory
    from pyhqbot.loader import load
    for module in modules:
        try:
            load(module)
        except ImportError as e:
            print "Error loading \"{0}\": {1}".format(module, e)
        except Exception as e:
            import sys
            sys.excepthook(*sys.exc_info())
            print "Error in module \"{0}\"".format(module)
        else:
            continue
        return
    user, password = get_credentials(credentials)
    storage = get_storage(persistence)
    factory = BotFactory(channel, user, password, storage)
    reactor.connectTCP(factory.host, factory.port, factory)
    reactor.run()

def get_credentials(file):
    from json import load
    return load(open(file))

def get_storage(file):
    from pyhqbot.storage import Storage
    st = Storage(file)
    st.load()
    return st
