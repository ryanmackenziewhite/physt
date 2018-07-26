"""Input and output for histograms.
"""
import json

from . import __version__
from .histogram_base import HistogramBase
from .util import find_subclass
from .histogram_pb2 import Summary

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

def load_message(path=None):
    summary = Summary()
    with open(path, "rb") as f:
        summary.ParseFromString(f.read())
    return summary    

def save_message(histograms, path=None, **kwargs):
    '''
    Creates a Summary protobuf
    Takes list of histograms
    Create a collection of histograms serialized to a single protobuf
    Enforce histogram name is defined (required)
    '''
    summary = Summary()
    for h in histograms:
        proto = summary.histograms[h.name]      
        proto.CopyFrom(h.to_protobuf())
    
    #print(summary)
    if(path):
        with open(path,"wb") as f:
            f.write(summary.SerializeToString())
    return summary        


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
