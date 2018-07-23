"""Input and output for histograms.
"""
import json


from . import __version__
from .histogram_base import HistogramBase
from .util import find_subclass
from .pfile import Pfile


        
def save_json(histogram, path=None, **kwargs):
    """Save histogram to JSON format.

    Parameters
    ----------
    histogram : HistogramBase
        Any histogram
    path : str
        If set, also writes to the path.

    Returns
    -------
    json : str
        The JSON representation of the histogram
    """
    # TODO: Implement multiple histograms in one file?
    data = histogram.to_dict()
    data["physt_version"] = __version__
    data["physt_compatible"] = "0.3.20"

    text = json.dumps(data, **kwargs)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return text


def load_json(path=None):
    """Load histogram from a JSON file.

    Parameters
    ----------
    path : str
        Path to the histogram file.

    Returns
    -------
    hist : HistogramBase
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
        return parse_json(text)


def parse_json(text):
    """Create histogram from a JSON string.

    Parameters
    ----------
    text : str
        UTF-8 encoded JSON
    """
    data = json.loads(text, encoding="utf-8")
    histogram_type = data["histogram_type"]
    # TODO: Check version
    klass = find_subclass(HistogramBase, histogram_type)
    return klass.from_dict(data)


def merge(fname, files=[]):
    '''
    merge two or more files
    adding equivalent keys

    pass a globbing pattern
    merge all hist files in directory?
    '''
    print(fname)
    merge_name = fname + '_merge'
    print(merge_name)
    print(files)
    merge_file = Pfile(merge_name)
    merge_file.parse_from_json(files.pop())
    while(len(files)>0):
        tmp_file = Pfile()
        tmp_file.parse_from_json(files.pop())
        for key in merge_file.keys:
            merge_file._histograms[key] += tmp_file._histograms[key]
    
    return merge_file









