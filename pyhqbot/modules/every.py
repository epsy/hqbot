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


from pyhqbot.register import init, command, cron

@init
def create_storage(call):
    call.storage.update({'message': ''})
    call.storage.save()

@command(lvl=command.OP)
def repeat(call, cmd, *message):
    if message:
        if message == ('--',):
            call.storage['message'] = ''
            call.reply('Cleared repeat message.')
        else:
            call.storage['message'] = ' '.join(message)
            call.reply('Changed repeat message.')
        call.storage.save()
    else:
        return (
            "Current message is \"{0}\". Clear it with !repeat --"
            .format(call.storage['message'])
            )

@cron(interval=10*60)
def show_message(call):
    if call.storage['message']:
        call.bot.echo(call.storage['message'])
