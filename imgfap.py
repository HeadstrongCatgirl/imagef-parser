import re
from os import mkdir
from os.path import isdir, exists, basename
import urllib.parse as urlparse
import asyncio
import aiohttp
import async_timeout
from PIL import Image

loop = asyncio.get_event_loop()
client = aiohttp.ClientSession(loop=loop)
galQ = asyncio.Queue()  # queue for galleries
orgQ = asyncio.Queue()  # queue for folders
async def download_coroutine(session, url, filename):
    with async_timeout.timeout(10):
        async with session.get(url) as response:
            with open(filename, 'wb') as f_handle:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    f_handle.write(chunk)
            return await response.release()

def checkJpg(path):
    try:
        im=Image.open(path)
        im.thumbnail([128,128])
    except:
        return False
    return True

async def organizer(session, q=None, galQ=None):
    print("Launched organizer")
    while True:
        path, dr = await q.get()
        print('org: ' + path)
        async with session.get(path) as page:
            pcontent = await page.text()
            if not dr:
                if path.endswith('galleries?folderid=-1'):
                    dr = 'user-' + path.split('/')[-2]
                else:
                    dr = urlparse.unquote('-'.join(path.split('/')[-2:][::-1]))
                    if "?" in dr:
                        dr=dr.replace(dr[dr.index("?"):dr.index('-')], '')
                dr=dr.replace("/", '-')+'/'
            if not isdir(dr):
                print('Saving to \"'+str(dr)+'"(org)')
                mkdir(dr)
            gals = set(re.findall('href="/gallery/(.+?)"', str(pcontent)))
            if any(gals):
                for i in gals:
                    i='http://www.imagefap.com/gallery/'+i.replace('amp;', '')
                    await galQ.put([i, dr])
                if 'page=' in path:
                    await q.put([re.sub(r'page=[0-9]*', 'page='+str(int(re.findall(r'page=[0-9]*', path)[0].split('=')[1])+1), path), dr])
                elif '?' in path:
                    await q.put([path+"&page=1", dr])
                else:
                    await q.put([path+"?page=1", dr])
            else:
                continue

async def main(session, verbose=False, q=None):
    print("Launched main")
    while True:
        path, directory = await q.get()
        print('main: '+path)
        if not path.startswith('http://'):
            path = 'http://'+path
        if not path.endswith('&view=2'):
            if '?' in path:
                path += '&view=2'
            else:
                path += '?view=2'
        async with session.get(path) as page:
            pcontent = await page.text()
            res = re.findall('href="/photo/(.+?)"', str(pcontent))
            saveDir = directory + urlparse.unquote(re.search("""<title>Porn pics of (.+?) \(Page [0-9]+\)</title>""", str(pcontent)).group(1).replace('/',''))+'-'+re.findall('([0-9]{4,10})',path)[0]
            if verbose:
                print("Saving to \"" + saveDir + '"(main)')
            if not isdir(saveDir):
                mkdir(saveDir)
            if any(res):
                for i in res:
                    i = 'http://www.imagefap.com/photo/' + i.replace('amp;', '')
                    async with session.get(i) as photoPage:
                        img = re.findall('''src="http://x.imagefapusercontent.com/u/(.+?)"''', str(await photoPage.text()))
                        img = 'http://x.imagefapusercontent.com/u/' + img[0].replace('amp;', '')
                        if not exists(saveDir + '/'+img[img.rfind('/')+1:]):
                            for i in range(5):
                                try:
                                    #urlretrieve(img, saveDir+'/'+img[img.rfind('/')+1:])
                                    await download_coroutine(session, img, saveDir+'/'+img[img.rfind('/')+1:])
                                    if checkJpg(saveDir+'/'+img[img.rfind('/')+1:]):
                                        break
                                except Exception as e:
                                    print('Error:' + str(e))
                                    pass
                    #progress+=1
                    #bar.update(progress)
                if verbose:
                    print('Downloaded '+ str(len(res))+' files.')
                if 'page=' in path:
                    q.put([re.sub(r'page=[0-9]*', 'page=' + str(int(re.findall(r'page=[0-9]*', path)[0].split('=')[1]) + 1), path), directory])
                elif '?' in path:
                    q.put(path+"&page=1")
                else:
                    q.put(path+"?page=1")
