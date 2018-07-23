#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 Ryan Mackenzie White <ryan.white4@canada.ca>
#
# Distributed under terms of the  license.

"""

"""
import sys
import os
import pytest
import numpy as np

sys.path = [os.path.join(os.path.dirname(__file__), "..")] + sys.path
import physt
from physt import bin_utils, io
from physt.histogram1d import Histogram1D
from physt.pfile import Pfile 

class TestFile(object):
    
    def test_to_dict(self):
        from physt.examples import normal_h1
        h = normal_h1()
        a_file = Pfile('test')
        a_file.book(h.name,h)
        a_file.display_from_json()
    

    def test_json_write_2d(self):
        from physt import h2
        values = np.random.rand(500, 2)
        h = h2(values[:,0], values[:,1], 3)
        print(h.to_json())
        #assert False

    def test_simple(self):
        h = physt.h2(None, None, "integer", adaptive=True)
        h << (0, 1)
        json = h.to_json()
        read = io.parse_json(json)
        assert h == read

    def test_file(self):
        from physt.examples import normal_h1
        h = normal_h1()
        a_file = Pfile('test')
        a_file.book(h.name,h)
        print(a_file.keys)
    
    def test_json_write_string(self):
        from physt.examples import normal_h1
        h = normal_h1()
        a_file = Pfile('junk')
        a_file.book(h.name,h)
        print(a_file.save_to_json())
    
    def test_json_read_string(self):
        from physt.examples import normal_h1
        h = normal_h1()
        a_file = Pfile('junk')
        a_file.book(h.name,h)
        a_file.save_to_json()
        b_file = Pfile()
        b_file.parse_from_json('junk.json')
        b_file.display_from_json()
    
    def test_merge(self):
        from physt.examples import normal_h1
        h = normal_h1()
        a_file = Pfile('junk')
        a_file.book(h.name,h)
        a_file.save_to_json()
        b_file = Pfile()
        b_file.parse_from_json('junk.json')
        b_file.display_from_json()

        files = ['junk.json','junk.json']

        c_file = io.merge('junk', files)
        c_file.display_from_json()
        

if __name__ == "__main__":
    pytest.main(__file__)
