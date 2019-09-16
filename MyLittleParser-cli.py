import imgfap
import asyncio
import sys
from functools import partial


def got_stdin_data(galQ, orgQ):
    inp = sys.stdin.readline()
    if ('/gallery' in inp) or ('pictures' in inp):
        asyncio.async(galQ.put([inp, '']))
    elif '/organizer' in inp or inp.endswith('galleries?folderid=-1'):
        asyncio.async(orgQ.put([inp, '']))
    # asyncio.async(q.put())



consumers = [
    asyncio.ensure_future(imgfap.main(imgfap.client, q=imgfap.galQ)),
    asyncio.ensure_future(imgfap.organizer(imgfap.client, q=imgfap.orgQ, galQ=imgfap.galQ))
]
imgfap.loop.add_reader(sys.stdin, got_stdin_data, imgfap.galQ, imgfap.orgQ)
imgfap.loop.run_forever()
