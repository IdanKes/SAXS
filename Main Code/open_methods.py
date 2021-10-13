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
    try:
        if self.imagepath !=filepath:
            self.min_radius_display.setText('Minimum')
            self.max_radius_display.setText('Maximum')
            self.min_radius = 0
            self.max_radius = 0
    except Exception:
        None
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
        print('/'.join(filepath[0].split('/')[:-1]))
        print(self.frame.text().split('Directory :')[-1])
        self.poni_file=filepath[0]
        self.poni_label.setText('loaded PONI file: /{}'.format(filepath[0].split("/")[-1]))
        self.poni_label.setFont(QFont('Segoe UI',9))
        ai = pyFAI.load(self.poni_file)
        self.ai=ai
        data_dict = ai.get_config()
        detector=data_dict['detector']
        #FIXME_data_dict bug from calib2 - maybe from datadict?
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
        if self.beamcenterx ==0 or '/'.join(filepath[0].split('/')[:-1])!=self.frame.text().split('Directory :')[-1]:
            self.beamcenterx=self.fit2ddata['centerX']
            self.beamcentery=self.fit2ddata['centerY']
            self.beamcenterxdisplay.setText('%.2f' % self.fit2ddata['centerX'])
            self.beamcenterydisplay.setText('%.2f' % self.fit2ddata['centerY'])
        else:
            ai.setFit2D(self.fit2ddata['directDist'],self.beamcenterx,self.beamcentery,self.fit2ddata['tilt'],self.fit2ddata['tiltPlanRotation'],self.fit2ddata['pixelX'],self.fit2ddata['pixelY'])
        self.wavelength=data_dict['wavelength']
        self.distance=data_dict['dist']
        self.set_min_button.setEnabled(True)
        self.set_max_button.setEnabled(True)
        self.setqminAction.setEnabled(True)
        self.setqmaxAction.setEnabled(True)
        self.set_max_button.setToolTip('')
        self.set_min_button.setToolTip('')
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