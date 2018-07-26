import sys
import os
import pytest
import numpy as np

sys.path = [os.path.join(os.path.dirname(__file__), "..")] + sys.path
import physt
from physt import bin_utils, io
from physt.histogram1d import Histogram1D
from physt import histogram1d_pb2

class TestIO(object):
    def test_json_write_string(self):
        bins = [1.2, 1.4, 1.5, 1.7, 1.8 ]
        values = [4, 0, 3, 7.2]
        example = Histogram1D(bins, values, overflow=1, underflow=2)
        output = io.save_json(example)
        #print(output)
        #assert False

    def test_json_write_2d(self):
        from physt import h2
        values = np.random.rand(500, 2)
        h = h2(values[:,0], values[:,1], 3)
        #print(h.to_json())
        #assert False

    def test_io_equality_on_examples(self):
        pass
        #from physt.examples import munros
        # for example in ALL_EXAMPLES:
        #h = munros()
        #json = h.to_json()
        #read = io.parse_json(json)
        #assert h == read

    def test_simple(self):
        h = physt.h2(None, None, "integer", adaptive=True)
        h << (0, 1)
        json = h.to_json()
        read = io.parse_json(json)
        assert h == read

    def test_protobuf(self):
        '''
        Create the protocol buffer
        Does it match the json object?
        '''
        print('PROTOBUF')
        bins = [1.2, 1.4, 1.5, 1.7, 1.8]
        values = [4, 0, 3, 7.2]
        example = Histogram1D(bins, values, overflow=1, underflow=2)
        output = io.save_json(example)
        
        h_dict = example.to_dict()
        summary = histogram1d_pb2.Summary()
        proto_hist = summary.histograms1d.add()
        proto_hist.histogram_type = type(example).__name__

        proto_hist.binnings.adaptive = example.binning.is_adaptive() 
        proto_hist.binnings.binning_type = type(example.binning).__name__
        proto_hist.dtype = str(np.dtype(example.dtype))
        
        meta = example.meta_data
        proto_hist.meta.axis_names.extend(example.axis_names)

        
        for bins in example.binning.bins.tolist():
            limits = proto_hist.binnings.bins.add()
            limits.limits.extend(bins)
        proto_hist.frequencies.extend(h_dict['frequencies'])
        proto_hist.errors2.extend(h_dict['errors2'])

        print(output)
        print(proto_hist)

if __name__ == "__main__":
    pytest.main(__file__)
