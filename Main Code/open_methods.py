from silx.gui.qt import QFileDialog,QTreeWidgetItem,QFont
from os.path import isfile,join
from os import listdir
import pyFAI
import numpy as np
from nexusformat.nexus import nxload

def open_directory(self):
    nxs_file_dict=self.nxs_file_dict
    directory_frame = self.frame
    tw=self.tw
    tw.clear()
    filepath = QFileDialog.getExistingDirectory(None, 'Select Folder')
    directory_frame.setText('Directory :{}'.format(filepath))
    self.imagepath = filepath
    try:
        onlyfiles = [f for f in listdir(filepath) if
                     isfile(join(filepath, f)) and (f.endswith('.tif') or f.endswith('.tiff') or f.endswith('.nxs'))]
        for file in onlyfiles:
            treeitem = QTreeWidgetItem([str(file)])
            if file.endswith('.nxs'):
                try:
                    self.open_nxs_wrap(filepath + '/' + file)
                    keys = nxs_file_dict[file].keys()
                    for key in keys:
                        treeitemchild = QTreeWidgetItem([key])
                        treeitem.addChild(treeitemchild)
                except Exception:
                    continue
            tw.addTopLevelItem(treeitem)
    except FileNotFoundError:
        pass


def open_poni(self):
    try:
        filepath = QFileDialog.getOpenFileName(self,filter='*.poni')
        self.poni_file=filepath[0]
        self.poni_label.setText('loaded PONI file: /{}'.format(filepath[0].split("/")[-1]))
        self.poni_label.setFont(QFont('Segoe UI',9))
        ai = pyFAI.load(self.poni_file)
        data_dict = ai.get_config()
        detector=data_dict['detector']
        #FIXME_data_dict bug from calib2
        if detector=='Pilatus300k' or 'Pilatus6M':
            self.pixel_size=0.000172
        else:
            try:
                self.pixel_size=data_dict['detector_config']['pixel1']
            except Exception:
                None
        layout2=self.layout2
        self.distancedisplay.setText('%.2f' % data_dict['dist'])
        self.wavelengthdisplay.setText(str(data_dict['wavelength']))
        self.fit2ddata=ai.getFit2D()
        self.beamcenterxdisplay.setText('%.2f' % self.fit2ddata['centerX'])
        self.beamcenterydisplay.setText('%.2f' % self.fit2ddata['centerY'])
        self.beamcenterx=self.fit2ddata['centerX']
        self.beamcentery=self.fit2ddata['centerY']
        self.wavelength=data_dict['wavelength']
        self.distance=data_dict['dist']
    except Exception:
        None

def open_mask(self):
    try:
        filepath = QFileDialog.getOpenFileName(self,filter='*.msk')
        self.mask_file=filepath[0]
        self.mask_label.setText('loaded Mask file: /{}'.format(filepath[0].split("/")[-1]))
        self.mask_label.setFont(QFont('Segoe UI',9))
    except Exception:
        None


def open_nxs(self, path):
    def find_scan_data(tree):
        location = ''
        keys = tree.keys()
        if 'scan_data' in keys:
            return location
        for key in keys:
            location += str(tree[key])
            find_scan_data(tree[key])
        return location
    file = path.split('/')[-1]
    nxs_file_dict = self.nxs_file_dict
    nxs_file_dict[file] = {}
    nxs_file = nxload(path)
    nxs_folder = find_scan_data(nxs_file)
    images_loc = nxs_file[nxs_folder].scan_data.eiger_image
    images_data = np.array(images_loc)
    images_data1 = np.flip(images_data, 1)
    image_count = list(range(1, len(images_data1) + 1))
    zipped = zip(image_count, images_data1)
    for item in zipped:
        nxs_file_dict[file]['{} - image {}'.format(file, item[0])] = item[1]