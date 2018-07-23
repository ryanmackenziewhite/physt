#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 Ryan Mackenzie White <ryan.white4@canada.ca>
#
# Distributed under terms of the  license.

"""
Collections of histograms in a file object

"""
import json
from collections import OrderedDict

from . import __version__
from .histogram_base import HistogramBase
from .util import find_subclass


class FileBase(object):
    '''
    Base File class to hold collections of histograms

    Requirements
    ------------
    Dictionary of {key:histogram}
    for key in file:
        key == histogram[key].name 
    
    Merge histograms from multiple files
    internal __add__ method implemented
    for file in files:
        for key in keys:
            h_0 = file.get(h_0)
            next...
        next..
        for key in keys:
            for hist in hists[key]:
                h_0.frequencies += hist.frequencies
                h_0.errors2 + hist.errors2

    Book a histogram
    Pass parameters for physt histogram for booking
    file.book(key, binning, freq=None, errors2=None, **kwargs)

    Fill a histogram
    file.fill(key,array)

    Get a histogram
    a_hist = file.get(key)

    Plot a histogram

    Write a file
    histogram_dicts = histogram[key].to_dict()
    OrderedDict = file[key]
    to_dict()
    to_json()
    '''

    def __init__(self, fname=None):
        '''
        Initialize

        Dictionary of keys to histograms
        at write convert to OrderDict
        and json
        '''
        self.name = fname
        self._meta = {}
        self._meta['name'] = self.name
        self._meta["physt_version"] = __version__
        self._meta["physt_compatible"] = "0.3.20"
        self._meta["keys"] = []
        
        self._histograms = {}
        pass
    
    @property 
    def meta_data(self):
        '''
        Dictionary of meta data 
        Keys
        Physt version info
        Filename
        Timestamp
        Pachyderm PPS and PFS meta_data
            Pileline name
            Input repo
            Output repo
        
        returns
        -------
        dict
        '''
        return self._meta
    
    @property 
    def keys(self):
        return self._histograms.keys
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, fname=None):
        '''
        if pps:
            filename = pps.pipeline.physt
        else:
            filename = fname
        '''    
        self._name = fname

    def get(self, key):
        return self._histograms[key]

    def book(self, key, histogram):
        '''
        pass physt arguments or make explicit?
        h = Histograms1D(...)
        phystfile.book(h.name,histogram)
        self._histograms[key] = histogram
        
        Override in algo 
        '''
        pass

    def fill(self, key, values, weights=None):
        '''
        if values is array_like:
            self.fill_hist(key,values,weights=None)
        if value is dict_like
            get_file(key)
            for a_key in a_dict:
                if a_key in self._histograms.keys:
                    self._histograms[key].fill_n(values[value])
        else 
            self.fill_hist(key,value,weight)
        '''
        pass

    def fill_all(self, a_dict):
        '''
        dictionary of arrays
        '''
        pass

    def fill_hist(self, key, value, weight):
        self.histograms[key].fill(value, weight)
    
    def fill_n(self, key, values, weights):
        '''
        pass arrays 
        '''
        pass

    def _to_dict(self):
        '''
        Convert histogram dict to OrderedDict
        Convert each histogram to OrderedDict
        '''
        result = OrderedDict()
        for idx, key in enumerate(self._histograms.keys):
            if self._histograms[key] is None:
                print('Error, cannot retrieve histograms')
            else:
                result[key] = self.histograms[key].to_dict()
        return result        

    def close(self):

        afile = self._to_dict()
        afile.save_to_json()
        pass 
