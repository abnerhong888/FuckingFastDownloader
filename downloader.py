import argparse
import yaml
import threading
import time
import sys
import os
from tqdm import tqdm
from pySmartDL import SmartDL

job_limits = 0
interrupt = False
lock = threading.Lock()

class Config:
    dest_dir=""
    download_concurrent_limit=3
    download_threads=4
    download_speed_limit=0

def size_to_bytes(size_str):
    for i in range(len(size_str) - 1, -1, -1):
        if size_str[i].isalpha():
            continue
        else:
            break
    i += 1
    number = size_str[:i]
    unit = size_str[i:]
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    if(unit in units):
        return int(float(number) * (1024 ** units.index(unit)))
    return int(size_str)

def read_config_yaml(file_path):
    data = read_yaml(file_path)
    if(data.get('config') == None):
        raise ValueError('config not found')
        
    data = data['config']

    if(data.get('destination') == None):
        raise ValueError('destination not found')

    config = Config()
    config.dest_dir = data.get('destination', '')
    config.download_concurrent_limit = data.get('download_concurrent_limit', 3)
    config.download_threads = data.get('download_threads', 4)
    value = data.get('download_speed_limit', 0)
    if isinstance(value, str):
        config.download_speed_limit = size_to_bytes(value)
    else:
        config.download_speed_limit = value
    return config
    
def argparses():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", type=str, default=None, help="links.yaml file path")
    parser.add_argument("-c", "--cfg", type=str, default=None, help="config.yaml file path")
    args = parser.parse_args()
    return args
    
def worker(pbar, info, config):
    global job_limits
    global interrupt

    name = info['name']
    url = info['url']

    with lock:
        job_limits += 1

    dest_path = config.dest_dir + '/' + name
    dl_threads = config.download_threads
    dl_threads = dl_threads if dl_threads <= threading.active_count() else threading.active_count()
    dl_speed_limit = config.download_speed_limit

    obj = SmartDL(url, threads=dl_threads, progress_bar=False, dest=dest_path)
    obj.limit_speed(dl_speed_limit if dl_speed_limit != 0 else -1)

    obj.start(blocking=False)

    while not obj.isFinished():
        if(interrupt):
            obj.stop()
            break

        pbar.update(int(obj.get_progress()*100 - pbar.n))
        pbar.set_postfix(speed=obj.get_speed(human=True), 
                        #  eta=obj.get_eta(human=True),
                         dl=obj.get_dl_size(human=True))
        time.sleep(0.2) 

    pbar.close()

    with lock:
        job_limits -= 1
def read_yaml(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"YAML file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            return data if data is not None else {}
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")

def read_linker_yaml(file_path):
    data = read_yaml(file_path)
    return data['data']

def create_folder_by_name(config, file_name):
    file_name = file_name.split('.')[0]
    path = config.dest_dir + '/' + file_name
    if not os.path.exists(path):
        os.makedirs(path)

    config.dest_dir = path
    return config

def main():
    global job_limits
    global interrupt

    args = argparses()
    if(args.link == None):
        raise ValueError('link not found')
    if(args.cfg == None):
        raise ValueError('cfg not found')

    threads = []

    try:
        queue = read_linker_yaml(args.link)
        config = read_config_yaml(args.cfg)
        config = create_folder_by_name(config, queue[0]['name'])

        dl_limit = config.download_concurrent_limit

        cnt = 0
        while len(queue):
            if(job_limits < dl_limit):
                info = queue.pop(0)
                name = info['name']
                
                pbar = tqdm(total=100, desc=name, position=cnt % dl_limit, bar_format='{l_bar}{bar}|{postfix}')
                t = threading.Thread(target=worker, args=(pbar, info, config))
                t.start()
                threads.append(t)
                
                cnt += 1
            
        for t in threads:
            t.join()

    except KeyboardInterrupt: 
        interrupt = True

        for t in threads:
            t.join()

        sys.exit(0) # Exit cleanly with a status code of 0

if __name__ == "__main__":
    main()