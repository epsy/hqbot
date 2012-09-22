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
import string
from operator import itemgetter

from twisted.python import log

from pyhqbot.register import init, command, scanner, cron

@init
def create_storage(call):
    call.storage.update({
            'last': {},
            'scores': {},
            'permits': {},
            'last_msgs': {},
            'last_times': {},
            'reason_last_shown': {},
        })
    call.storage.save()

MIN_ADD_PUNISH = 6
@scanner(types=scanner.CHAT)
def spam_watch(call, line, type):
    if call.nick in call.bot.ops:
        return

    if time() < call.storage['permits'].get(call.nick, 0):
        return

    score, per_type = calculate_score(call, line)
    add_score(call, call.nick, score)
    if score >= MIN_ADD_PUNISH:
        punish(call, call.nick, per_type)

MAX_SCORE_ONCE = 25
def calculate_score(call, message):
    total_score = 0
    per_type = {}

    for score_type, compute in score_calculators.items():
        score = compute(call, message)
        if score:
            total_score += score
            per_type[score_type] = score

    return min(MAX_SCORE_ONCE, total_score), per_type

SCORE_LINK = 25
link_re = re.compile(r'\.[^ ]+/')
def link_score(call, message):
    if link_re.search(message):
        return SCORE_LINK
    return 0

SCORE_CAPITALS = .6
SCORE_CAPITALS_MIN = 5
def caps_score(call, message):
    cap_count = 0
    for char in message:
        if char != char.lower():
            cap_count += 1
    if cap_count >= SCORE_CAPITALS_MIN:
        return cap_count * SCORE_CAPITALS
    return 0

SCORE_FREQ = 5
SCORE_FREQ_MIN = 0.5
def freq_score(call, message):
    if call.nick not in call.storage['last_times']:
        times = []
    else:
        times = call.storage['last_times'][call.nick]

    times = times[-2:] + [time()]
    call.storage['last_times'][call.nick] = times

    if len(times) == 3:
        freq = 2 / (times[-1] - times[0])
        if freq > SCORE_FREQ_MIN:
            return freq * SCORE_FREQ

    return 0

keep = string.ascii_lowercase
def dumbify(text):
    return ''.join(c for c in text.lower() if c in keep)

SCORE_REPEAT = 4
SCORE_REPEAT_LENGTH_BONUS = 0.2
SCORE_REPEAT_SAME= 7
def repeat_score(call, message):
    if call.nick not in call.storage['last_msgs']:
        msgs = []
    else:
        msgs = call.storage['last_msgs'][call.nick]

    search = dumbify(message)

    if len(search) < 3:
        return 0

    msgs = msgs[-4:]
    call.storage['last_msgs'][call.nick] = msgs + [search]

    same_found = 0
    found = 0
    lengths = [len(search)]

    for msg in msgs:
        if msg == search:
            same_found += 1
            lengths.append(len(msg))
        elif len(msg) > 5 and msg in search or len(search) > 5 and search in msg:
            found += 1
            lengths.append(len(msg))

    if found or same_found:
        return (
            found * SCORE_REPEAT
            + same_found * SCORE_REPEAT_SAME
            + min(lengths) * SCORE_REPEAT_LENGTH_BONUS
            )
    return 0


score_calculators = {
    'link': link_score,
    'caps': caps_score,
    'freq': freq_score,
    #'repeat': repeat_score,
}

def add_score(call, name, add):
    if add <= 0:
        return

    score = decay_score(call, name)
    call.storage['scores'][name] = score + add
    call.storage['last'][name] = time()
    log.msg("Added {0} to {1}'s spam score. It is now {2}".format(
        score, name, call.storage['scores'][name]))
    call.storage.save(False)

SCORE_TIME_STAY = 10 * 60
SCORE_DECAY = 1.0 / 60
def decay_score(call, name):
    score = call.storage['scores'].get(name, 0)

    if not score:
        return 0

    last = call.storage['last'].get(name, 0)
    decay_time = time() - last - SCORE_TIME_STAY

    if decay_time <= 0:
        return score

    log.msg('Decayed {0}\'s score from {1} by {2}'.format(
            name, score, decay_time * SCORE_DECAY
        ))
    return max(0, score - decay_time * SCORE_DECAY)

SCORE_TO = 10
SCORE_TO_LENGTH = 6
SCORE_BAN = 40
def punish(call, name, per_type):
    score = call.storage['scores'].get(name, 0)

    if not score:
        return

    if score >= SCORE_BAN:
        call.bot.echo('/ban {0}'.format(name))
        log.msg('Banned {0}, score {1}'.format(name, score))
    elif score >= SCORE_TO:
        length = score * SCORE_TO_LENGTH
        call.bot.echo('/timeout {0} {1}'.format(name, length))
        log.msg('Timed out {0} for {1} seconds, score {2}'.format(
            name, length, score))

    show_reason(call, name, per_type)

reason_messages = {
    'link': 'Please do not post links.',
    'caps': 'Please do not talk in capital letters.',
    'freq': 'Please do not spam.',
    'repeat': 'Please do not repeat yourself.',
}
REASON_INTERVAL = 20

def show_reason(call, name, per_type):
    reason, score = max(per_type.items(), key=itemgetter(1))

    if call.storage['reason_last_shown'].get(reason, 0) + REASON_INTERVAL < time():
        call.storage['reason_last_shown'][reason] = time()
        call.bot.echo(reason_messages[reason])

TIME_PERMIT = 60
@command(lvl=command.OP)
def permit(call, cmd, name):
    forget(call, name)
    call.storage['permits'][name] = time() + TIME_PERMIT
    call.storage.save(write=False)
    return "{0} is now permitted to post anything for {1} seconds.".format(
        name, TIME_PERMIT)

FORGET_AFTER = 60*60*24
@cron
def cleanup(call):
    storage = call.storage
    to_remove = []

    for nick, time_ in call.storage['last_times'].items():
        if time_ + FORGET_AFTER < time():
            to_remove.append(nick)

    for nick in to_remove:
        forget(call, nick)

    storage.save()

def forget(call, nick):
    storage = call.storage
    for dict in 'last', 'scores', 'permits', 'last_msgs', 'last_times':
        try:
            del storage[dict][nick]
        except KeyError:
            pass
