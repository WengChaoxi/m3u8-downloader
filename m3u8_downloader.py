#!/usr/bin/env python
try:
    import requests, re, os, threading, time, gc, traceback
except ImportError:
    import sys
    sys.exit('import error!')

cookies = ''
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie':cookies
}

def parse_m3u8(url, save_path)->list:
    '''
    parse m3u8 file
    '''
    print('parse m3u8 file...', end='')
    s_url = url.split('/')
    uri = s_url[0]+'//'+s_url[2]
    filename = s_url[-1]
    path = os.path.join(save_path, filename)
    data = b'\n'
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except IOError:
        r = requests.get(url, headers=headers)
        data = r.content
        with open(path, 'wb') as f:
            f.write(data)
    u_str = data.decode('utf8')
    urls = []
    for u in u_str.split('\n'):
        if '.key' in u:
            urls.append(uri+re.search(r'"(.+)"', u).group(1))
        if '.ts' in u:
            urls.append(uri+u)
            
    print('success')
    return urls
    
def ts_downloader(urls, save_path):
    '''
    download *.ts file
    '''
    # chunk_size = 1024
    while len(urls)>0:
        url = urls.pop(0)
        filename = url.split('/')[-1]
        file_path = os.path.join(save_path, filename)
        if os.path.exists(file_path):
            continue

        try:
            requests.packages.urllib3.disable_warnings()
            r = requests.get(url, verify=False) #, stream=True)
            with open(file_path, 'wb') as f:
                #for chunk in r.iter_content(chunk_size):
                #    f.write(chunk)
                f.write(r.content)
            del r
            gc.collect()
            print('download %s...success'%(file_path))
        except:
            pass
        finally:
            if not os.path.exists(file_path):
                urls.append(url)
            
            # time.sleep(0.02)
                
def m3u8_to_mp4(m3u8_path, mp4_path):
    # fix index.m3u8
    with open(m3u8_path, 'r', encoding='utf8') as f:
        temp = f.read()
        r = ''
        for str in temp.split('\n'):
            if '.ts' in str:
                r = str.split('/')[-1]
                r = str.replace(r, '')
                break
        temp = temp.replace(r, m3u8_path.replace('index.m3u8', ''))
    with open(m3u8_path, 'w', encoding='utf8') as f:
        f.write(temp)
    
    # ffmpeg -allowed_extensions ALL -i index.m3u8 -c copy out.mp4
    # os.popen(), os.system()
    cmd = 'bin/ffmpeg.exe -allowed_extensions ALL -i %s -c copy %s'%(m3u8_path, mp4_path)
    r = os.popen(cmd)
    print(r.read())
    
def m3u8_downloader(url, save_path, thread_count):
    urls = parse_m3u8(url, save_path)
    url_count = len(urls)
    
    # share the urls to threads
    part = url_count//thread_count
    for i in range(thread_count):
        p_urls = []
        index = part*i
        if(i==thread_count-1):
            p_urls = urls[index:url_count]
        else:
            p_urls = urls[index:index+part]
        t = threading.Thread(target=ts_downloader, kwargs={'urls':p_urls, 'save_path':save_path})
        t.setDaemon(True)
        t.start()
    
    # wait for threads finish
    main_thread = threading.current_thread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()
        
if __name__ == "__main__":
    try:     
        m3u8_url = 'https://domain.com/index.m3u8'
        save_path = 'D:/path/to/file/'
        
        thread_count = 100 # 下载线程
        m3u8_downloader(m3u8_url, save_path, thread_count)
        # 自行下载ffmpeg.exe放于bin目录下，用于转换
        # m3u8_to_mp4(save_path+'/index.m3u8', 'data/out.mp4')
    except KeyboardInterrupt:
        sys.exit('user abort')
    finally:
        print('by wcx')