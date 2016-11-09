#!/usr/bin/env python

from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL)

import csv
import gc
import sys
from collections import defaultdict
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sim
from operator import itemgetter
from multiprocessing import Pool, cpu_count

wsi = defaultdict(lambda: dict())
v   = DictVectorizer()
D   = []

with open('03-cw-wsi.txt') as f:
    reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
    for row in reader:
        word, sid, _, words = row

        try:
            words = {k: float(v) for record in words.split('  ') for k, v in (record.rsplit(':', 1),)}
        except ValueError:
            print('Skipping misformatted string: %s.' % words, file=sys.stderr)
            continue

        wsi[word][int(sid)] = words
        D.append(words)

X = v.fit_transform(D)

def emit(word):
    sneighbours = {}

    for sid, words in wsi[word].items():
        sense  = '%s#%d' % (word, sid)
        vector = v.transform(words)
        sneighbours[sense] = {}

        for neighbour, weight in words.items():
            neighbours   = wsi[neighbour]
            candidates   = [(nsid, sim(vector, v.transform(neighbours[nsid]))[0, 0]) for nsid in neighbours]
            nsid, cosine = max(candidates, key=itemgetter(1))
            if cosine > 0:
            # if cosine > 0 or len(candidates) == 1:
                nsense = '%s#%d' % (neighbour, nsid)
                sneighbours[sense][nsense] = weight

    return sneighbours

with Pool(cpu_count() - 1) as pool:
    for sneighbours in pool.imap_unordered(emit, wsi):
        for sense, neighbours in sneighbours.items():
            for nsense, weight in neighbours.items():
                print('%s\t%s\t%f' % (sense, nsense, weight))

# for word, senses in wsi.items():
#     for sid, words in senses.items():
#         sense  = '%s#%d' % (word, sid)
#         vector = v.transform(words)
#         sneighbours = {}

#         for neighbour, weight in words.items():
#             neighbours = wsi[neighbour]
#             items = [(nsid, sim(vector, v.transform(neighbours[nsid]))[0, 0]) for nsid in neighbours]
#             nsid, cosine = max(items, key=itemgetter(1))
#             if cosine > 0:
#                 nsense = '%s#%d' % (neighbour, nsid)
#                 sneighbours[nsense] = weight

#         for nsense, weight in sneighbours.items():
#             print('%s\t%s\t%f' % (sense, nsense, weight))
