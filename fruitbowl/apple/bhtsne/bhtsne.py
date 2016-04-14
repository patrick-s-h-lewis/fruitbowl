'''
.. module:: bhtsne 
   :platform: Unix, OSX
   :synopsis: perform large, efficient, tsne reductions using barnes-hut methods 

.. moduleauthor:: Patrick Lewis
'''
#Copyright (c) 2015 Patrick Lewis
#
#
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

# Copyright (c) 2013, Pontus Stenetorp <pontus stenetorp se>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from os.path import abspath, dirname, isfile, join as path_join
from shutil import rmtree
from struct import calcsize, pack, unpack
from subprocess import Popen
from sys import stderr, stdin, stdout
from tempfile import mkdtemp
from os import devnull
import numpy as np

class TmpDir:
    '''Class for temporary directory for communicating to C Program'''
    def __enter__(self):
        '''Enter the temporary directory'''
        self._tmp_dir_path = mkdtemp()
        return self._tmp_dir_path

    def __exit__(self, type, value, traceback):
        '''Leave the temporary directory'''
        rmtree(self._tmp_dir_path)


def _read_unpack(fmt, fh):
    return unpack(fmt, fh.read(calcsize(fmt)))
            
class TSNE(object):
    '''Perform TSNE reductions'''
    
    def __init__(self,n_components=2,theta=0.5,randseed=-1,perplexity=30.):
        '''build a TSNE object
        
        Kwargs:
            n_components (int): dimensions to reduce to
            theta (float): theta  parameter
            randseed (int): if -1, no randseed, if 0, randseed
            perplexity (float): perplexity parameter
        '''
        self.n_components=n_components
        self.theta=theta
        self.perplexity=perplexity
    
    def fit_transform(self,feed,randseed=-1):
        '''wrapper for bh_tsne reduction
        
        Args:
            feed (list or numpy.2darray):list of n d-dimensional numpy.arrays or d-by-n matrix
                containing the vectors to reduce.
        
        Kwargs:
            randseed (int): if -1, no random seeding, if 0, use random seeding
        
        Returns:
            fitted (numpy.2darray): n-by-dims matrix containing reduced vectors
        '''
        #ensure the input is list of lists for clean interfacing with c program
        san_feed = map(lambda x:list(x),list(feed))
        fitted=np.zeros((len(san_feed),2))
        ind=0
        #perform reduction, pack results into matrix for export
        for result in self.bh_tsne(feed, 
                              no_dims=self.n_components,
                              perplexity=self.perplexity,
                              theta=self.theta,
                              randseed=randseed,
                              verbose=0):
            fitted[ind,:]=result
            ind+=1
        return fitted
    
    def bh_tsne(self,samples, no_dims=2, perplexity=None, theta=None, randseed=-1,
            verbose=False):
        '''Perform TSNE reduction
        
        Args:
            samples (list): list of d_dimensional vectors to reduce
        
        Kwargs:
            no_dims (int): dimensions to reduce to, defaults to 2
            perplexity (float): perplexity parameter
            theta (float): theta parameter
            randseed (int): if -1, no random seeding, if 0, use random seeding (default -1)
            verbose (bool): if True, prints progress to stdout
        
        Yields:
            result (list) : reduced data points, yielded 1 by 1
        '''
        # Assume that the dimensionality of the first sample is representative for
        #   the whole batch
        sample_dim = len(samples[0])
        sample_count = len(samples)

        # bh_tsne works with fixed input and output paths, give it a temporary
        #   directory to work in so we don't clutter the filesystem
        with TmpDir() as tmp_dir_path:
            # Note: The binary format used by bh_tsne is roughly the same as for
            #   vanilla tsne
            with open(path_join(tmp_dir_path, 'data.dat'), 'wb') as data_file:
                # Write the bh_tsne header
                data_file.write(pack('iiddi', sample_count, sample_dim, theta, perplexity, no_dims))
                # Then write the data
                for sample in samples:
                    data_file.write(pack('{}d'.format(len(sample)), *sample))
                # Write random seed if specified
                if randseed != self.randseed:
                    data_file.write(pack('i', randseed))

            # Call bh_tsne and let it do its thing
            with open(devnull, 'w') as dev_null:
                BH_TSNE_BIN_PATH =  path_join(dirname(__file__), 'bh_tsne')
                bh_tsne_p = Popen((abspath(BH_TSNE_BIN_PATH), ), cwd=tmp_dir_path,
                        # bh_tsne is very noisy on stdout, tell it to use stderr
                        #   if it is to print any output
                        stdout=stderr if verbose else dev_null)
                bh_tsne_p.wait()
                assert not bh_tsne_p.returncode, ('ERROR: Call to bh_tsne exited '
                        'with a non-zero return code exit status, please ' +
                        ('enable verbose mode and ' if not verbose else '') +
                        'refer to the bh_tsne output for further details')

            # Read and pass on the results
            with open(path_join(tmp_dir_path, 'result.dat'), 'rb') as output_file:
                # The first two integers are just the number of samples and the
                #   dimensionality
                result_samples, result_dims = _read_unpack('ii', output_file)
                # Collect the results, but they may be out of order
                results = [_read_unpack('{}d'.format(result_dims), output_file)
                    for _ in xrange(result_samples)]
                # Now collect the landmark data so that we can return the data in
                #   the order it arrived
                results = [(_read_unpack('i', output_file), e) for e in results]
                # Put the results in order and yield it
                results.sort()
                for _, result in results:
                    yield result
                # The last piece of data is the cost for each sample, we ignore it
                #read_unpack('{}d'.format(sample_count), output_file)