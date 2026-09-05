import logging
import random
import re
from collections import namedtuple

# Fix Python2/Python3 incompatibility
try: input = raw_input
except NameError: pass

log = logging.getLogger(__name__)

class Key:
    def __init__(self, word, weight, decomps):
        self.word = word
        self.weight = weight
        self.decomps = decomps


class Decomp:
    def __init__(self, parts, save, reasmbs):
        self.parts = parts
        self.save = save
        self.reasmbs = reasmbs
        self.next_reasmb_index = 0

class SorensEliza:
    def __init__(self):
        self.initials = []
        self.initial_sorens = []
        self.initial_reeds = []
        self.initial_lukes = []
        self.initial_arrans = []
        self.initial_aneirins = []
        self.initial_davids = []
        self.initial_elios = []
        self.initial_lukass = []

        self.finals = []
        self.quits = []
        self.pres = {}
        self.posts = {}
        self.synons = {}
        self.keys = {}
        self.memory = []

    def initial(self):
        return random.choice(self.initials)

    def initial_soren(self):
        return random.choice(self.initial_sorens)

    def initial_reed(self):
        return random.choice(self.initial_reeds)

    def initial_luke(self):
        return random.choice(self.initial_lukes)

    def initial_lukas(self):
        return random.choice(self.initial_lukass)

    def initial_david(self):
        return random.choice(self.initial_davids)

    def initial_arran(self):
        return random.choice(self.initial_arrans)

    def initial_aneirin(self):
        return random.choice(self.initial_aneirins)

    def initial_elio(self):
        return random.choice(self.initial_elios)

    def final(self):
        return random.choice(self.finals)

    def load(self, path):
        with open(path) as file:
            for line in file:
                if not line.strip():
                    continue
                tag, content = [part.strip() for part in line.split(':')]
                #debug file content
                #print(tag, content)
                if tag == 'initial':
                    self.initials.append(content)
                if tag == 'initial_soren':
                    self.initial_sorens.append(content)
                if tag == 'initial_reed':
                    self.initial_reeds.append(content)
                if tag == 'initial_luke':
                    self.initial_lukes.append(content)
                if tag == 'initial_lukas':
                    self.initial_lukass.append(content)
                if tag == 'initial_arran':
                    self.initial_arrans.append(content)
                if tag == 'initial_aneirin':
                    self.initial_aneirins.append(content)
                if tag == 'initial_david':
                    self.initial_davids.append(content)
                if tag == 'initial_elio':
                    self.initial_elios.append(content)
                elif tag == 'final':
                    self.finals.append(content)
                elif tag == 'quit':
                    self.quits.append(content)
                elif tag == 'pre':
                    parts = content.split(' ')
                    self.pres[parts[0]] = parts[1:]
                elif tag == 'post':
                    parts = content.split(' ')
                    self.posts[parts[0]] = parts[1:]
                elif tag == 'synon':
                    parts = content.split(' ')
                    self.synons[parts[0]] = parts
                elif tag == 'key':
                    parts = content.split(' ')
                    word = parts[0]
                    weight = int(parts[1]) if len(parts) > 1 else 1
                    key = Key(word, weight, [])
                    self.keys[word] = key
                elif tag == 'decomp':
                    parts = content.split(' ')
                    save = False
                    if parts[0] == '$':
                        save = True
                        parts = parts[1:]
                    decomp = Decomp(parts, save, [])
                    key.decomps.append(decomp)
                elif tag == 'reasmb':
                    parts = content.split(' ')
                    decomp.reasmbs.append(parts)

    def respond(self, text):
        if text.lower() in self.quits:
            return None
        text = re.sub(r'\s*\.+\s*', ' . ', text)
        text = re.sub(r'\s*,+\s*', ' , ', text)
        text = re.sub(r'\s*;+\s*', ' ; ', text)
        #print('DEBUG After removing punctuation: ', text)
        words = [w for w in text.split(' ') if w]
        #print('Input: ', words)

        words = self._sub(words, self.pres)
        log.debug('After pre-substitution: %s', words)

        keys = [self.keys[w.lower()] for w in words if w.lower() in self.keys]
        keys = sorted(keys, key=lambda k: -k.weight)
        log.debug('Sorted keys: %s', [(k.word, k.weight) for k in keys])

        output = None

        for key in keys:
            output = self._match_key(words, key)
            if output:
                log.debug('Output from key: %s', output)
                break
        if not output:
            if self.memory:
                index = random.randrange(len(self.memory))
                output = self.memory.pop(index)
                log.debug('Output from memory: %s', output)
            else:
                output = self._next_reasmb(self.keys['xnone'].decomps[0])
                log.debug('Output from xnone: %s', output)

        return " ".join(output)

    def _match_decomp_r(self, parts, words, results):
        if not parts and not words:
            return True
        if not parts or (not words and parts != ['*']):
            return False
        if parts[0] == '*':
            for index in range(len(words), -1, -1):
                results.append(words[:index])
                if self._match_decomp_r(parts[1:], words[index:], results):
                    return True
                results.pop()
            return False
        elif parts[0].startswith('@'):
            root = parts[0][1:]
            if not root in self.synons:
                raise ValueError("Unknown synonym root {}".format(root))
            if not words[0].lower() in self.synons[root]:
                return False
            results.append([words[0]])
            return self._match_decomp_r(parts[1:], words[1:], results)
        elif parts[0].lower() != words[0].lower():
            return False
        else:
            return self._match_decomp_r(parts[1:], words[1:], results)

    def _match_decomp(self, parts, words):
        results = []
        if self._match_decomp_r(parts, words, results):
            return results
        return None

    def _next_reasmb(self, decomp):
        index = decomp.next_reasmb_index
        result = decomp.reasmbs[index % len(decomp.reasmbs)]
        decomp.next_reasmb_index = index + 1
        return result

    def _reassemble(self, reasmb, results):
        output = []
        for reword in reasmb:
            if not reword:
                continue
            if reword[0] == '(' and reword[-1] == ')':
                index = int(reword[1:-1])
                if index < 1 or index > len(results):
                    raise ValueError("Invalid result index {}".format(index))
                insert = results[index - 1]
                for punct in [',', '.', ';']:
                    if punct in insert:
                        insert = insert[:insert.index(punct)]
                output.extend(insert)
            else:
                output.append(reword)
        return output

    def _sub(self, words, sub):
        output = []
        for word in words:
            word_lower = word.lower()
            if word_lower in sub:
                output.extend(sub[word_lower])
            else:
                output.append(word)
        return output

    def _match_key(self, words, key):
        for decomp in key.decomps:
            results = self._match_decomp(decomp.parts, words)
            if results is None:
                log.debug('Decomp did not match: %s', decomp.parts)
                continue
            log.debug('Decomp matched: %s', decomp.parts)
            log.debug('Decomp results: %s', results)
            results = [self._sub(words, self.posts) for words in results]
            log.debug('Decomp results after posts: %s', results)
            reasmb = self._next_reasmb(decomp)
            log.debug('Using reassembly: %s', reasmb)
            if reasmb[0] == 'goto':
                goto_key = reasmb[1]
                if not goto_key in self.keys:
                    raise ValueError("Invalid goto key {}".format(goto_key))
                log.debug('Goto key: %s', goto_key)
                return self._match_key(words, self.keys[goto_key])
            output = self._reassemble(reasmb, results)
            if decomp.save:
                self.memory.append(output)
                log.debug('Saved to memory: %s', output)
                continue
            return output
        return None

    def welcome(self, name):
        if name.lower() == 'soren':
            greeting = self.initial_soren()
        elif name.lower() == 'antony':
            greeting = self.initial_soren()
        elif name.lower() == 'elio':
            greeting = self.initial_elio()
        elif name.lower() == 'reed':
            greeting = self.initial_reed()
        elif name.lower() == 'luke':
            greeting = self.initial_luke()
        elif name.lower() == 'lukas':
            greeting = self.initial_lukas()
        elif name.lower() == 'david':
            greeting =  self.initial_david()
        elif name.lower() == 'arran':
            greeting =  self.initial_arran()
        elif name.lower() == 'aneirin':
            greeting =  self.initial_aneirin()
        else:
            greeting = self.initial()

        result = f"Hi, {name} {greeting}."
        return(result)

    def run(self):
        name = input('can you tell me your name? > ').strip()
        print(welcome(name))

        while True:
            sent = input('> ')

            output = self.respond(sent)
            if output is None:
                break

            print(output)

        print(self.final(), " ", name)

def main():
    seliza = SorensEliza()
    seliza.load('doctor_soren.txt')
    seliza.run()

if __name__ == '__main__':
#    logging.basicConfig()
    main()