import sys
import os
import pytest
import numpy as np

sys.path = [os.path.join(os.path.dirname(__file__), "..")] + sys.path
import physt
from physt import bin_utils, io
from physt.histogram1d import Histogram1D
from physt import histogram_pb2


from physt.util import find_subclass
from physt.histogram_base import HistogramBase

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
        #print('PROTOBUF')
        bins = [1.2, 1.4, 1.5, 1.7, 1.8]
        values = [4, 0, 3, 7.2]
        example = Histogram1D(bins, values, overflow=1, underflow=2,name="key")
        #example.name = 'key'
        output = io.save_json(example)
        
        h_dict = example.to_dict()
         
        summary = histogram_pb2.Summary()
        proto_hist = summary.histograms[example.name]      
        proto_hist.CopyFrom(example.to_protobuf())
        
        io.save_message([example])

        histogram_type = proto_hist.histogram_type
        # TODO: Check version
        klass = find_subclass(HistogramBase, histogram_type)
        tested = klass.from_message(proto_hist)
        print(example)
        #tested.name='key'
        print(tested)
        #assert example == tested

    def test_io_protobuf(self):
        print('PROTOBUF')
        bins = [1.2, 1.4, 1.5, 1.7, 1.8]
        values = [4, 0, 3, 7.2]
        example = Histogram1D(bins, values, overflow=1, underflow=2,name='key')
        example.name = 'key'
        summary = histogram_pb2.Summary()
        proto_hist = summary.histograms[example.name]      
        proto_hist.CopyFrom(example.to_protobuf())
        io.save_message([example],'test_proto.data')
        load = io.load_message('test_proto.data')

        histos = {}
        for key in load.histograms:
            histogram_type = load.histograms[key].histogram_type
            klass = find_subclass(HistogramBase, histogram_type)
            histos[key] = klass.from_message(load.histograms[key])





if __name__ == "__main__":
    pytest.main(__file__)
