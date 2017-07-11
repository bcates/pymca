# /*#########################################################################
# Copyright (C) 2004-2014 V.A. Sole, European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""
Plugin to load positioner info from a CSV or HDF5 file.
"""
__authors__ = ["P. Knobel"]
__license__ = "MIT"

import csv
from io import open

from PyMca5 import StackPluginBase
from PyMca5.PyMcaGui.io.hdf5.HDF5Widget import getGroupDialog
from PyMca5.PyMcaGui.io import PyMcaFileDialogs

try:
    import h5py
except ImportError:
    h5py = None

DEBUG = 0

# TODO (handle .txt extension, and single scan .spec format)


class LoadPositionersStackPlugin(StackPluginBase.StackPluginBase):
    def __init__(self, stackWindow):
        StackPluginBase.DEBUG = DEBUG
        StackPluginBase.StackPluginBase.__init__(self, stackWindow)
        self.methodDict = {'Load positioners': [self._loadFromFile,
                                                "Load positioners from file"]}
        self.__methodKeys = ['Load positioners']
        # self.widget = None

    # def stackClosed(self):
    #     if self.widget is not None:
    #         self.widget.close()

    #Methods implemented by the plugin
    def getMethods(self):
        return self.__methodKeys

    def getMethodToolTip(self, name):
        return self.methodDict[name][1]

    def getMethodPixmap(self, name):
        return self.methodDict[name][2]

    def applyMethod(self, name):
        return self.methodDict[name][0]()

    def _loadFromFile(self):
        stack = self.getStackDataObject()
        if stack is None:
            return
        mcaIndex = stack.info.get('McaIndex')
        if not (mcaIndex in [0, -1, 2]):
            raise IndexError("1D index must be 0, 2, or -1")
        filefilter = ['HDF5 Files (*.h5 *.nxs *.hdf *.hdf5)', 'CSV (*.csv)']
        if h5py is None:
            filefilter = filefilter[1:]
        filename, ffilter = PyMcaFileDialogs.\
                    getFileList(parent=None,
                        filetypelist=filefilter,
                        message='Load',
                        mode='OPEN',
                        single=True,
                        getfilter=True,
                        currentfilter=filefilter[0])
        if len(filename):
            if DEBUG:
                print("file name = %s file filter = %s" % (filename, ffilter))
        else:
            if DEBUG:
                print("nothing selected")
            return
        filename = filename[0]

        positioners = {}
        if ffilter.startswith('HDF5'):
            h5Group = getGroupDialog(filename)
            if h5Group is None:
                return
            positioners = {}
            for dsname in h5Group:
                # links and subgroups just ignored for the time being
                if not isinstance(h5Group[dsname], h5py.Dataset):
                    continue
                positioners[dsname] = h5Group[dsname][()]
        else:
            with open(filename, "rb") as csvfile:
                has_header = csv.Sniffer().has_header(csvfile.read(1024))
                if not has_header:
                    raise IOError(
                        "The CSV file does not appear to define motor names in header line")
                csvfile.seek(0)
                dialect = csv.Sniffer().sniff(csvfile.read(1024),
                                              delimiters="\t;:|, ")
                # (setting reasonable possible delimiters prevents corner cases in which
                # a number is detected to be the delimiter)
                csvfile.seek(0)
                csvreader = csv.reader(csvfile, dialect)
                motor_names = next(csvreader)
                for row in csvreader:
                    for i, value in enumerate(row):
                        positioners[motor_names[i]] = float(value)

        self._stackWindow.setPositioners(positioners)


MENU_TEXT = "Load positioners from file"


def getStackPluginInstance(stackWindow, **kw):
    ob = LoadPositionersStackPlugin(stackWindow)
    return ob
