import subprocess as sp
from multiprocessing import Pool
import random


# number below should the N in this query:
# item_lst = list(coll.find({ "$or": [{ "reviews" : {"$exists" :0}}, {"reviews": {"$size":0}}]}).sort('_id'))
# print len(item_lst)

N = 24
chunks = 6				# number of parallel scripts running
delta = N / chunks
start_end_pairs = [(i * delta, (i+1) * delta) for i in xrange(chunks)][::-1]

def run_task(args):
    start, end = args
    sp.call('python27 get_info.py %s %s &' % (start, end), shell=True)


if __name__ == '__main__':
    pool = Pool(3)		# number of processor cores used
    pool.map(run_task, start_end_pairs)
    
