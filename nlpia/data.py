import os
import shutil
import requests
from .constants import logging

from pugnlp.futil import path_status
import pandas as pd

np = pd.np
logger = logging.getLogger(__name__)


USER_HOME = os.path.expanduser("~")
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
DATA_URL = 'http://totalgood.org/static/data'
W2V_FILE = 'GoogleNews-vectors-negative300.bin.gz'
W2V_URL = 'https://www.dropbox.com/s/4bcegydk3pn9067/GoogleNews-vectors-negative300.bin.gz?dl=0'
W2V_PATH = os.path.join(DATA_PATH, W2V_FILE)

with open(os.path.join(DATA_PATH, 'kite.txt')) as f:
    kite_text = f.read()

with open(os.path.join(DATA_PATH, 'kite_history.txt')) as f:
    kite_history = f.read()

harry_docs = ["The faster Harry got to the store, the faster and faster Harry would get home."]
harry_docs += ["Harry is hairy and faster than Jill."]
harry_docs += ["Jill is not as hairy as Harry."]


def no_tqdm(it, total=1):
    return it


def download(names=None, verbose=True):
    names = [names] if isinstance(names, (str, bytes, basestring)) else names
    names = names or ['w2v']
    file_paths = {}
    for name in names:
        name = name.lower().strip()
        if name in ('w2v', 'word2vec'):
            file_paths['w2v'] = download_file(W2V_URL, 'GoogleNews-vectors-negative300.bin.gz', size=1647046227,
                                              verbose=verbose)
    return file_paths


def download_file(url, local_file_path=None, size=None, chunk_size=1024, verbose=True):
    """Uses stream=True and a reasonable chunk size to be able to download large (GB) files over https"""
    local_file_path = os.path.join(DATA_PATH, url.split('/')[-1]) if local_file_path is None else local_file_path
    if not (local_file_path.startswith(DATA_PATH) or local_file_path[0] in ('/', '~')):
        local_file_path = os.path.join(DATA_PATH, local_file_path)
    # if verbose:
    #     tqdm_prog = tqdm
    #     print('requesting URL: {}'.format(W2V_URL))
    # else:
    #     tqdm_prog = no_tqdm
    stat = path_status(local_file_path)
    if stat['type'] == 'file' and stat['size'] == size:  # TODO: check md5
        return local_file_path

    r = requests.get(url, stream=True)
    size = r.headers.get('Content-Length', None) if size is None else size
    print(r.headers.keys())
    print('size: {}'.format(size))

    with open(local_file_path, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
        # for chunk in tqdm_prog(r.iter_content(chunk_size=chunk_size)):
        #     if chunk:  # filter out keep-alive chunks
        #         f.write(chunk)
    return local_file_path


def read_csv(*args, **kwargs):
    """Like pandas.read_csv, only little smarter (checks first column to see if it should be the data frame index)"""
    index_names = ('Unnamed: 0',)
    kwargs.update({'low_memory': False})
    df = pd.read_csv(*args, **kwargs)
    if df.columns[0] in index_names or (df[df.columns[0]] == df.index).all():
        df = df.set_index(df.columns[0], drop=True)
    elif (df[df.columns[0]] == np.arange(len(df))).all():
        df = df.set_index(df.columns[0], drop=False)
    elif (df.index == np.arange(len(df))).all() and str(df[df.columns[0]].dtype).startswith('int') and df[df.columns[0]].count() == len(df):
        df = df.set_index(df.columns[0], drop=False)
    return df


def multifile_dataframe(paths=['urbanslang{}of4.csv'.format(i) for i in range(1, 5)], header=0, index_col=None):
    """Like pandas.read_csv, but loads and concatenates (df.append(df)s) DataFrames together"""
    df = pd.DataFrame()
    for p in paths:
        df = df.append(read_csv(p, header=header, index_col=index_col), ignore_index=True if not index_col else False)
    if index_col and df.index.name == index_col:
        del df[index_col]
    return df