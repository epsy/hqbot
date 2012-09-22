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


import cPickle as pickle

class Storage(object):
    def __init__(self, file):
        self.file = file
        self.obj = {}

    def load(self):
        try:
            self.obj = pickle.load(open(self.file, 'rb'))
        except IOError:
            pass

    def save(self):
        pickle.dump(self.obj, open(self.file, 'wb'))

    def part(self, name):
        if name not in self.obj:
            self.obj[name] = {}
        return StoragePart(name, self, self.obj[name])

    def join(self, part, write=True):
        as_dict = dict(part)
        pickle.dumps(as_dict) # before merging, check if the part
                              # can be pickled, let it raise otherwise
        self.obj[part.name] = as_dict
        if write:
            self.save()


class StoragePart(dict):
    def __init__(self, name, parent, val):
        self.name = name
        self._parent = parent
        super(StoragePart, self).__init__(val)

    def save(self, write=True):
        self._parent.join(self, write)
