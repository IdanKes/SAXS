import numpy
import re
from silx.gui import qt
from skimage import io
from silx.gui.plot.PlotWindow import PlotWindow
import pyFAI, fabio
import subprocess
from PIL import Image, ImageOps
import PIL
from silx.gui.plot import tools
from PyQt5 import QtWidgets
from silx.gui.widgets.BoxLayoutDockWidget import BoxLayoutDockWidget
import pandas as pd
from nexusformat.nexus import *
from PyQt5.QtWidgets import QMessageBox
from docking_bars import MyCurveLegendsWidget
from open_methods import open_directory,open_poni,open_mask,open_nxs
from plotting_methods import image_plot,curve_plot,plot_mul_curves


class MyPlotWindow(qt.QMainWindow):

    def __init__(self, parent=None):
        super(MyPlotWindow, self).__init__(parent)

        # Create a PlotWidget
        self._plot = PlotWindow(parent=self,roi=False)

        #menu bar
        menuBar = self.menuBar()
        fileMenu = qt.QMenu("&More Options", self)
        menuBar.addMenu(fileMenu)
        self.save_csv_action = qt.QAction('Save Integrated Data as CSV File...',self)
        fileMenu.addAction(self.save_csv_action)
        self.save_csv_action.triggered.connect(self.save_csv)
        self.beamcenterx=0
        self.beamcentery=0
        self.wavelength=0

        #Bottom Toolbar
        position = tools.PositionInfo(plot=self._plot,
                                      converters=[('Radius from Beam Center (px)', lambda x, y: numpy.sqrt((x-self.beamcenterx)**2 + (y-self.beamcentery)**2)),
                                                  ('Angle', lambda x, y: numpy.degrees(numpy.arctan2(y-self.beamcentery, x-self.beamcenterx))),
                                                  ('X Position (px)', lambda x,y: x),
                                                  ('Y Position (px)', lambda x, y: y)])
        #('q', lambda x, y: (4*numpy.pi*(numpy.sin(numpy.degrees(numpy.arctan2(y-self.beamcentery, x-self.beamcenterx)))))/self.wavelength)]

        toolBar1 = qt.QToolBar("xy", self)
        self.addToolBar(qt.Qt.BottomToolBarArea,toolBar1)
        progressbar=qt.QProgressBar(self,objectName="GreenProgressBar")
        progressbar.setFixedSize(312,30)
        progressbar.setTextVisible(False)
        self.progressbar=progressbar
        toolBar1.addWidget(position)
        toolBar1.addWidget(progressbar)

        #window
        self.setWindowTitle("Saxsii")
        icon=qt.QIcon('files/icon.png')
        self.setWindowIcon(icon)

        #layout
        options = qt.QWidget(self)
        layout = qt.QVBoxLayout(options)
        button = qt.QPushButton("Calibration Tool", self)
        button.clicked.connect(self.InitiateCalibration)
        layout.addWidget(button)
        button = qt.QPushButton("Load Image Folder", self)
        button.clicked.connect(self.open_directory_wrap)
        layout.addWidget(button)
        tw=qt.QTreeWidget(self)
        layout.addWidget(tw)
        self.tw=tw
        tw.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        tw.setHeaderHidden(True)
        tw.itemSelectionChanged.connect(self.ShowImage)
        tw.itemDoubleClicked.connect(self.ShowImage)
        button = qt.QPushButton("Load PONI File", self)
        button.clicked.connect(self.open_poni_wrap)
        layout.addWidget(button)
        poni_label=qt.QLabel(self)
        poni_label.setText('No PONI')
        self.poni_label=poni_label
        layout.addWidget(button)
        layout.addWidget(poni_label)
        button = qt.QPushButton("Load Mask File", self)
        button.clicked.connect(self.open_mask_wrap)
        layout.addWidget(button)
        mask_label = qt.QLabel(self)
        mask_label.setText('No Mask')
        self.mask_label = mask_label
        layout.addWidget(button)
        layout.addWidget(mask_label)

        #integration paramteres
        integparams = qt.QGroupBox('Integration Parameters')
        sublayout=qt.QFormLayout(integparams)
        bins=qt.QLineEdit('1000')
        self.bins=bins
        minradius=qt.QLineEdit('0')
        self.minradius=minradius
        maxradius = qt.QLineEdit('10')
        self.maxradius = maxradius

        sublayout.addRow('Bins:',bins)
        sublayout.addRow('Min Radius:', minradius)
        sublayout.addRow('Max Radius:', maxradius)
        layout.addWidget(integparams)

        q_combobox=qt.QComboBox()
        sublayout.addRow('Radial unit:',q_combobox)
        q_combobox.addItems(['q (nm^-1)','q (A^-1)'])
        self.q_combo=q_combobox

        buttonsWidget = qt.QWidget()
        buttonsWidgetLayout = qt.QHBoxLayout(buttonsWidget)
        buttons = ['Integrate Selected','Integrate All']
        addbuttons = [qt.QPushButton(c) for c in buttons]
        addbuttons[0].clicked.connect(self.Integrate_selected)
        addbuttons[1].clicked.connect(self.Integrate_all)
        for button in addbuttons:
            buttonsWidgetLayout.addWidget(button)
        layout.addWidget(buttonsWidget)
        layout.addStretch()

        #Integration Data dict
        self.idata={}
        self.unitdict={'q (nm^-1)':"q_nm^-1",'q (A^-1)':"q_A^-1"}
        self.nxs_file_dict = {}

        #Data Fields
        options2 = qt.QGroupBox('Calibration Data')
        #layout2 = qt.QFormLayout(options2)
        layout2=qt.QFormLayout(options2)
        self.layout2=layout2
        wavelength=qt.QLineEdit()
        distance=qt.QLineEdit()
        beamcenterx=qt.QLineEdit()
        beamcentery=qt.QLineEdit()
        layout2.addRow('Distance:', distance)
        layout2.addRow('Wavelength:', wavelength)
        layout2.addRow('Beam Center X:',beamcenterx)
        layout2.addRow('Beam Center Y:', beamcentery)
        self.wavelengthdisplay=wavelength
        self.distance=distance
        self.beamcenterxdisplay=beamcenterx
        self.beamcenterydisplay=beamcentery

        # 1D loaded Images List
        options3=qt.QWidget(self)
        layout3 =qt.QVBoxLayout(options3)
        layout3.addWidget(qt.QLabel('Integrated Images:'))
        loadedlistwidget = qt.QListWidget(self)
        layout3.addWidget(loadedlistwidget)
        self.loadedlistwidget=loadedlistwidget
        loadedlistwidget.itemSelectionChanged.connect(self.plot_mul_curves_wrap)
        loadedlistwidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        tools1d=qt.QLabel('1d Tools')
        tools1d.setStyleSheet("border: 1px solid black;")
        layout3.addWidget(tools1d)
        subtracttbut=qt.QPushButton('subtract',self)
        layout3.addWidget(subtracttbut)
        subtracttbut.clicked.connect(self.subtractcurves)

        #Loaded Directory name
        frame = qt.QLabel(self)
        frame.setText("Directory:")
        frame.setFont(qt.QFont('Segoe UI', 9))
        self.frame = frame
        self.frame.setStyleSheet("border: 0.5px solid black;")

        # Gui Geometry
        gridLayout = qt.QGridLayout()
        gridLayout.setSpacing(2)
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridLayout.addWidget(options, 1, 0)
        gridLayout.addWidget(self._plot, 1, 1,2,1)
        gridLayout.addWidget(frame, 0, 1)
        gridLayout.setRowStretch(1, 1)
        gridLayout.setColumnStretch(1, 1)
        gridLayout.addWidget(options3, 1, 2)
        gridLayout.addWidget(options2,2,2)

        centralWidget = qt.QWidget(self)
        centralWidget.setLayout(gridLayout)
        self.setCentralWidget(centralWidget)

        # legend dock
        plot = self._plot
        curveLegendsWidget = MyCurveLegendsWidget()
        curveLegendsWidget.setPlotWidget(plot)
        dock = BoxLayoutDockWidget()
        dock.setWindowTitle('Curve legends')
        dock.setWidget(curveLegendsWidget)
        plot.addDockWidget(qt.Qt.TopDockWidgetArea, dock)

    def getPlotWidget(self):
        """"Returns the PlotWidget object """""
        return self._plot

    def getIntegrationParams(self):
        bins = int(self.bins.text())
        minradius = int(self.minradius.text())
        maxradius = int(self.maxradius.text())
        poni = self.poni_file
        mask = fabio.open(self.mask_file)
        q_choice = self.q_combo.currentText()
        unit_dict = self.unitdict
        q_choice = unit_dict[q_choice]
        plot = self.getPlotWidget()
        curve_plot(self,plot)
        nxs_file_dict = self.nxs_file_dict
        datadict = self.idata
        loadedlist = self.loadedlistwidget
        return bins,minradius,maxradius,poni,mask,q_choice,nxs_file_dict,datadict,loadedlist,plot


    def showInitalImage(self):
        """inital image logo"""
        plot = self.getPlotWidget()
        plot.getDefaultColormap().setName('viridis')
        im = Image.open('files/saxsii.jpeg')
        im=im.rotate(180, PIL.Image.NEAREST, expand = 1)
        im_mirror = PIL.ImageOps.mirror(im)
        plot.addImage(im_mirror)

    def InitiateCalibration(self):
        subprocess.run(["pyFAI-calib2"])

    def full_integration(self,image,mask,poni,bins,minradius,maxradius,q_choice,datadict,nxs,nxs_file_dict):
        if not nxs:
            imagefolder=self.imagepath
            imagepath=imagefolder+'/'+image
            img = fabio.open(imagepath)
            filename = image.split('.')[0]
            img_array = img.data
        if nxs:
            imagefolder = self.imagepath
            image_name = image.split('.')[0]+'.nxs'
            image_data = nxs_file_dict[image_name][image]
            img_array=image_data
            filename=image
        ai = pyFAI.load(poni)
        res = ai.integrate1d_ng(img_array,
                                bins,
                                mask=mask,
                                unit=q_choice,
                                filename="{}/{}.dat".format(imagefolder,filename),
                                error_model='poisson',
                                radial_range=(minradius, maxradius))
        datadict[filename] = res

    def integrate(self,imagelist):
        bins, minradius, maxradius, poni, mask, q_choice, nxs_file_dict, datadict, loadedlist,plot=self.getIntegrationParams()
        tw = self.tw
        loadeditemsTextList = [str(loadedlist.item(i).text()) for i in range(loadedlist.count())]
        if len(imagelist) == 0:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please Select an Image to Integrate")
            x = msg.exec_()
        else:
            length=len(imagelist)
            i=1
            for image in imagelist:
                pvalue=int((i/length)*100)
                self.progressbar.setValue(pvalue)
                self.progressbar.setFont(qt.QFont('Segoe UI',9))
                if image not in loadeditemsTextList:
                    if (image.endswith('.tiff') or image.endswith('.tif')):
                        self.full_integration(image=image, poni=poni, mask=mask.data, bins=bins, minradius=minradius,
                                              maxradius=maxradius, q_choice=q_choice, datadict=datadict, nxs=False,
                                              nxs_file_dict=nxs_file_dict)

                        filename = image.split('.')[0]
                        res = datadict[filename]
                        plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(filename),
                                      linewidth=2)
                        loadedlist.addItem(image)
                    regexp = re.compile(r'(?:nxs - image ).*$')
                    if regexp.search(image):
                        self.full_integration(image=image, poni=poni, mask=mask.data, bins=bins, minradius=minradius,
                                              maxradius=maxradius, q_choice=q_choice, datadict=datadict, nxs=True,
                                              nxs_file_dict=nxs_file_dict)
                        res = datadict[image]
                        plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(image),
                                      linewidth=2)
                        loadedlist.addItem(image)
                    if image.endswith('.nxs'):
                        None

                else:
                    if (image.endswith('.tiff') or image.endswith('.tif')):
                        filename = image.split('.')[0]
                        res = datadict[filename]
                        plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(filename),
                                      linewidth=2)
                    regexp = re.compile(r'(?:nxs - image ).*$')
                    if regexp.search(image):
                        res = datadict[image]
                        plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(image),
                                      linewidth=2)
                i+=1
    def Integrate_selected(self):
        tw=self.tw
        imagelist=[item.text(0) for item in tw.selectedItems()]
        self.integrate((imagelist))

    def Integrate_all(self):
        def get_subtree_nodes(tree_widget_item):
            """Returns all QTreeWidgetItems in the subtree rooted at the given node."""
            nodes = []
            nodes.append(tree_widget_item)
            for i in range(tree_widget_item.childCount()):
                nodes.extend(get_subtree_nodes(tree_widget_item.child(i)))
            return nodes

        def get_all_items(tree_widget):
            """Returns all QTreeWidgetItems in the given QTreeWidget."""
            all_items = []
            for i in range(tree_widget.topLevelItemCount()):
                top_item = tree_widget.topLevelItem(i)
                all_items.extend(get_subtree_nodes(top_item))
            return all_items

        tw=self.tw
        imagelist=get_all_items(tw)
        imagelist_names=[image.text(0) for image in imagelist]
        self.integrate(imagelist_names)

    def open_directory_wrap(self):
        open_directory(self)

    def open_poni_wrap(self):
         open_poni(self)

    def open_mask_wrap(self):
        open_mask(self)

    def open_nxs_wrap(self,path):
        open_nxs(self,path)

    def ShowImage(self):
        tw=self.tw
        plot = self.getPlotWidget()
        nxs_file_dict=self.nxs_file_dict
        image_plot(plot)
        if tw.selectedItems()==[]:
            None
        else:
            filepath=self.imagepath +'/'+ str(tw.selectedItems()[0].text(0))
            if (filepath.endswith('.tiff') or filepath.endswith('.tif')):
                try:
                    image = io.imread(filepath) #convert to fabio?
                except Exception:
                    im=fabio.open(filepath)
                    image=im.data
                plot.addImage(image,resetzoom=True)
                plot.resetZoom()
            if filepath.endswith('.nxs'):
                None
            regexp=re.compile(r'(?:nxs - image ).*$')
            if regexp.search(filepath):
                filename=filepath.split('.')[0].split('/')[-1]+'.nxs'
                image_number=filepath.split('-')[-1]
                image=nxs_file_dict[filename][filename+' -'+image_number]
                plot.addImage(image, resetzoom=True)
                plot.resetZoom()


    def plot_mul_curves_wrap(self):
        plot_mul_curves(self)


    def subtractcurves(self):
        loadedlist = self.loadedlistwidget
        plot = self.getPlotWidget()
        datadict = self.idata
        curvelist = [item.text() for item in loadedlist.selectedItems()]
        curvenames=[]
        for curve in curvelist:
            if '.nxs' in curve:
                curvenames.append(curve)
            else:
                curvenames.append(curve.split('.')[0])

        if len(curvelist)==2:
            name1 = curvenames[0]
            name2=curvenames[1]
            res1 = datadict[name1]
            res2=datadict[name2]
            res3_intensity=abs(numpy.subtract(res1.intensity,res2.intensity))
            res3={'radial':res1.radial,'intensity':res3_intensity,'sigma':res1.sigma}
            name3=name1+' SUBTRACT '+name2
            datadict[name3]=res3
            loadedlist.addItem(name3)
            plot.addCurve(x=res1.radial,y=res3_intensity,legend='{}'.format(name1+' SUBTRACT '+name2),linewidth=1,color='green')
            plot.setGraphGrid(which='both')

        else:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please select only 2 curves to subtract")
            x = msg.exec_()

    def save_csv(self):
        filepath=self.imagepath
        q_choice = self.q_combo.currentText()
        loadedlist = self.loadedlistwidget
        curvelist = [item.text() for item in loadedlist.selectedItems()]
        curvenames = []
        for curve in curvelist:
            if '.nxs' in curve:
                curvenames.append(curve)
            else:
                curvenames.append(curve.split('.')[0])
        if curvelist==[]:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please Select Integrated Curve to Save")
            x = msg.exec_()
        else:
            for curve in curvenames:
                df=pd.read_csv(r'{}/{}.dat'.format(filepath,curve),header=None,sep="\s+",skiprows=23)
                df.rename(columns={0: q_choice,1:'Intesnsity',2:'Sigma_I'},inplace=True)
                df.to_csv(filepath+'/{}_csv.csv'.format(curve),index=False)



def main():
    from styling import return_style
    StyleSheet=return_style()
    global app
    app = qt.QApplication([])
    app.setStyleSheet(StyleSheet)
    window = MyPlotWindow()
    window.setAttribute(qt.Qt.WA_DeleteOnClose)
    window.showInitalImage()
    window.showMaximized()
    app.exec()

if __name__ == '__main__':
    main()