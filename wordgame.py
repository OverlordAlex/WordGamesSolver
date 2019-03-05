from collections import defaultdict, Counter
from copy import copy, deepcopy
from random import randint

import sys


class Node:
    # TODO: remove char - its encoded in the dict
    char = ''
    prev, nxt = None, None

    def __init__(self, prev_node, char):
        self.char = char
        self.prev = prev_node
        self.nxt = {}

        if prev_node:
            prev_node.nxt[char] = self

    def __str__(self):
        return "(" + str(self.prev.char) + ")" + str(self.char) + ": " + str(self.nxt)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.char)
    #def __eq__(self, other):
    #    return self.char == other.char

class Dictionary:
    def add_word(self, word):
        self.add_part(self.trie, None, word, 0)

    def add_part(self, struct, prev, word, depth):
        if not word:
            # we are at the end of the word
            Node(prev, 0)
            return
        char = word[0]
        if char not in struct:
            struct[char] = Node(prev, char)
            try:
                self.metastruct[depth].append(struct[char])
            except:
                print depth
                #exit()
                return
            #self.metastruct[depth].add(struct[char])
        node = struct[char]
        #self.metastruct[depth].add(node)
        self.add_part(node.nxt, node, word[1:], depth + 1)

    def get_words(self, node, length):
        if not length:
            if 0 in node.nxt:
                return [node.char]
            return [0]
        words = []
        for char in node.nxt.keys():
            if not char:
                continue
            possible = self.get_words(node.nxt[char], length - 1)
            for sub in possible:
                if sub:
                    words.append(node.char + sub)
        return words

    def is_word(self, word):
        node = self.trie
        while word:
            char = word[0]
            word = word[1:]
            if not char in node:
                return False
            node = node[char].nxt
        return 0 in node

    def get_prefix(self, node):
        s = ""
        while node.prev:
            node = node.prev
            s = node.char + s
        return s

    def get_words_matching(self, pairs, length):
        def _match(word, pairs):
            for char,pos in pairs:
                if not char == word[pos]:
                    return False
            return True

        # use the last pair of char+pos 
        pairs = sorted(pairs, reverse=True, key=lambda pair: pair[1])
        char, pos = pairs[0]
        words = self.get_words_where(char, pos, length)

        words = filter(lambda item: _match(item, pairs[1:]), words)

        return words

    def get_words_where(self, char, pos, length):
        #pos -= 1 # humans are 1-index
        suff = []
        intersections = self.metastruct[pos]
        for node in intersections:
            if node.char == char:
                suffixes = self.get_words(node, length-pos-1)
                for s in suffixes:
                    if s:
                        pref = self.get_prefix(node)
                        suff.append(pref + s)
        return suff

    def word_possible(self, word, pairs):
        pass

    def load_words(self, dictionaryFile):
        with open(dictionaryFile, 'r') as fh:
            for word in fh:
                word = word.strip().lower()
                if len(word) < 3 or len(word) > 5:
                    continue
                self.add_word(word)

    def __init__(self, dFile = None):
        # TODO: changed this to set and tanked performance - build afterwards?
        #self.metastruct = [set(), set(), set(), set(), set()]
        #self.metastruct = [[], [], [], [], []]
        self.metastruct = [ [] for i in range(100)]
        #self.metastruct = [set() for i in range(6)]
        self.trie = {}
        if dFile:
            self.load_words(dFile)


class WordRow:
    row = -1
    col_offset = -1
    length = 0
    val = 0

    def __init__(self, row, col_offset, length, val):
        self.row = row
        self.col_offset = col_offset
        self.length = length
        self.val = val

    def __cmp__(self, other):
        return cmp(self.val, other.val)

    def __repr__(self):
        return "ROW: " + str(self.row) + ", " + str(self.col_offset) + " (" + str(self.length) + ") = " + str(self.val)

class WordCol:
    col = -1
    row_offset = -1
    length = 0
    val = 0

    def __init__(self, col, row_offset, length, val):
        self.col = col
        self.row_offset = row_offset
        self.length = length
        self.val = val

    def __cmp__(self, other):
        return cmp(self.val, other.val)

    def __repr__(self):
        return "COL: " + str(self.col) + ", " + str(self.row_offset) + " (" + str(self.length) + ") = " + str(self.val)

class Game:
    dd = None
    grid, metagrid = None, None

    def __init__(self, dictionary):
        self.dd = dictionary

    def check_word(self, word, characters, wild_consts = 0, wild_vowels = 0, wild_any = 0):
        ''' given a list of characters check if they can make the word '''
        possible = False
        vowels = 'aeiou'

        chars = Counter(characters)
        word = Counter(word)
        remaining = word-chars
        extra = chars-word

        chars.subtract(word)
        possible = all(val >= 0 for val in chars.values())
        if not possible:
            # have to use wildcards
            for char, count in remaining.items():
                while count > 0:
                    if char in vowels:
                        if wild_vowels > 0:
                            wild_vowels -= 1
                        else:
                            wild_any -= 1
                    else:
                        if wild_consts > 0:
                            wild_consts -= 1
                        else:
                            wild_any -= 1
                    count -= 1
            possible = wild_any >= 0

        return possible, ''.join(char*val for char,val in extra.items()), wild_consts, wild_vowels, wild_any


    def show_grid(self, grid):
        print '\n'.join([''.join([char if char else ' ' for char in row]) for row in grid])
        print "="*25

    def build_grid(self):
        grid = [['' for i in range(5)] for i in range(5)]
        grid[0][0] = '*'
        grid[0][1] = '*'
        grid[1][0] = '*'
        grid[4][3] = '*'
        grid[4][4] = '*'
        self.grid = grid

        rows = [WordRow(0, 2, 3, 1), WordRow(1, 1, 4, 2), WordRow(2, 0, 5, 3), WordRow(3, 0, 5, 3), WordRow(4, 0, 3, 1)]
        cols = [WordCol(0, 2, 3, 1), WordCol(1, 1, 4, 2), WordCol(2, 0, 5, 3), WordCol(3, 0, 4, 2), WordCol(4, 0, 4, 2)]
        self.metagrid = (sorted(rows, reverse=True), sorted(cols, reverse=True))

    def evaluate(self, grid, final=False):
        rowTotal, colTotal = 0, 0

        for row in self.metagrid[0]:
            word = ""
            for i in range(row.length):
                word += grid[row.row][row.col_offset + i]
            if len(word) == row.length and self.dd.is_word(word):
                rowTotal += row.val

        for col in self.metagrid[1]:
            word = ""
            for i in range(col.length):
                word += grid[col.row_offset + i][col.col]
            if len(word) == col.length and self.dd.is_word(word):
                colTotal += col.val

        if final:
            print rowTotal, colTotal
        return rowTotal * colTotal

    VOWELS = "aeiou"
    CONSTS = "qwrtypsdfghjklzxcvbnm"
    ALL = VOWELS + CONSTS

    def setRow(self, grid, metaRow, word):
        if len(word) > metaRow.length:
            raise "u wot m8"
        for i in range(len(word)):
            grid[metaRow.row][metaRow.col_offset + i] = word[i]

    def setCol(self, grid, metaCol, word):
        if len(word) > metaCol.length:
            raise "u wot m8"
        for i in range(len(word)):
            grid[metaCol.row_offset + i][metaCol.col] = word[i]

    def _solve(self, grid, old_meta, chars, wilds):
        # given a grid, and a list of metaobjs not yet considered, a string of characteters and a tuple of (wild vowel, wild consts, wilds) return a maximum scoring grid
        ngrid = deepcopy(grid)
        meta = deepcopy(old_meta) #??
        possible = chars + wilds[0]*self.CONSTS + wilds[1]*self.VOWELS + wilds[2]*self.ALL

        #print 1, ' '*(10-len(meta)), len(meta), len(old_meta), chars, wilds
        bestscore = -1
        bestgrid = None

        if (not chars) or (not meta):
            return self.evaluate(grid), grid

        #print ' '*(10-len(meta)), len(meta), meta 
        while meta:
            nxt = meta.pop(0)

            pairs = []
            if isinstance(nxt, WordRow):
                for i in range(nxt.length):
                    if ngrid[nxt.row][nxt.col_offset + i]:
                        pairs.append((ngrid[nxt.row][nxt.col_offset], i))
            else:
                for i in range(nxt.length):
                    if ngrid[nxt.row_offset + i][nxt.col]:
                        pairs.append((ngrid[nxt.row_offset + i][nxt.col], i))

            words = []
            if pairs:
                pchars = ''.join(chx for chx,_ in pairs)
                words = self.dd.get_words_matching(pairs, nxt.length)
                words = filter(lambda item: self.check_word(item, chars + pchars, *wilds)[0], words)
            else:
                for char in set(possible):
                    words += self.dd.get_words_where(char, 0, nxt.length)
                words = filter(lambda item: self.check_word(item, chars, *wilds)[0], words)
            # TODO - custom filter that saves check_word 
            # TODO - filter should not throw away words that can be made with the pairs
            if not words:
                # there are no possible words, keep searching the smaller ones?
                score, filledgrid = self._solve(ngrid, meta, chars, wilds)
                if score > bestscore:
                    bestscore = score
                    bestgrid = filledgrid
                if bestscore == 100:
                    return bestscore, bestgrid
                continue
                #return self._solve(ngrid, meta, chars, wilds)
                #return self.evaluate(ngrid), ngrid

            for word in words:
                #print "REE", word
                #print ' '*(10-len(meta)), len(meta), len(old_meta), word, chars
                nngrid = deepcopy(grid)
                if isinstance(nxt, WordRow):
                    self.setRow(nngrid, nxt, word)
                else:
                    self.setCol(nngrid, nxt, word)
                _, nchars, wildc, wildv, wilda = self.check_word(word, chars, *wilds)
                #print "REE", word, nchars
                #TODO consistent wildcard vowel/const order
                score, filledgrid = self._solve(nngrid, meta, nchars, (wildc, wildv, wilda))
                if score > bestscore:
                    bestscore = score
                    bestgrid = filledgrid
                if bestscore == 100:
                    return bestscore, bestgrid

        return bestscore, bestgrid

    def solve(self, grid, characters, wild_consts = 0, wild_vowels = 0, wild_any = 0):
        score, bestgrid = self._solve(grid, sorted(self.metagrid[0] + self.metagrid[1], reverse=True), characters, (wild_consts, wild_vowels, wild_any))

        self.show_grid(bestgrid)
        self.evaluate(bestgrid, True)
        print score

        return bestgrid


if __name__ == "__main__":
    dd = Dictionary()
    dd.load_words(sys.argv[1])

#>> dd = wordgame.Dictionary('/usr/share/dict/words')
# from pympler.asizeof import asizeof
# total_time = timeit('import wordgame; wordgame.Dictionary("/usr/share/dict/words")', number=1)

