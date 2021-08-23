import numpy
from silx.gui import qt
from skimage import io

from silx.gui.plot.PlotWindow import PlotWindow
from os import listdir
from os.path import isfile, join
from silx.gui import colors
from silx.gui.plot import Plot2D,Plot1D
import pyFAI, fabio
import subprocess
from PIL import Image, ImageOps
import PIL
from silx.gui.plot import tools
from silx.gui.plot.tools.CurveLegendsWidget import CurveLegendsWidget
from PyQt5 import QtWidgets
from silx.gui.plot.tools.CurveLegendsWidget import CurveLegendsWidget
from silx.gui.widgets.BoxLayoutDockWidget import BoxLayoutDockWidget

import importlib
a=importlib.import_module('files.docklegend')
MyCurveLegendsWidget=a.MyCurveLegendsWidget


class MyPlotWindow(qt.QMainWindow):

    def __init__(self, parent=None):
        super(MyPlotWindow, self).__init__(parent)

        # Create a PlotWidget
        self._plot = PlotWindow(parent=self)

        #Bottom Toolbar
        position = tools.PositionInfo(plot=self._plot,
                                      converters=[('Radius', lambda x, y: numpy.sqrt(x * x + y * y)),
                                                  ('Angle', lambda x, y: numpy.degrees(numpy.arctan2(y, x))),
                                                  ('X Position', lambda x,y: x),
                                                  ('Y Position', lambda x,y: y)])
        toolBar = qt.QToolBar("xy", self)
        self.addToolBar(qt.Qt.BottomToolBarArea,toolBar)
        toolBar.addWidget(position)

        #window
        self.setWindowTitle("Saxii")
        icon=qt.QIcon('icon.png')
        self.setWindowIcon(icon)

        #layout
        options = qt.QWidget(self)
        layout = qt.QVBoxLayout(options)
        button = qt.QPushButton("Calibration Tool", self)
        button.clicked.connect(self.InitiateCalibration)
        layout.addWidget(button)
        # button = qt.QPushButton("Show Image", self)
        # button.clicked.connect(self.ShowImage)
        # layout.addWidget(button)
        button = qt.QPushButton("Load Folder", self)
        button.clicked.connect(self.open)
        layout.addWidget(button)
        listwidget=qt.QListWidget(self)
        layout.addWidget(listwidget)
        self.listwidget=listwidget
        listwidget.itemSelectionChanged.connect(self.ShowImage)
        integparams = qt.QGroupBox('Integration Parameters')
        sublayout=qt.QFormLayout(integparams)
        bins=qt.QLineEdit('1000')
        sublayout.addRow('Bins:',bins)
        layout.addWidget(integparams)
        button = qt.QPushButton("Integrate", self)
        button.clicked.connect(self.Integrate)
        layout.addWidget(button)

        layout.addStretch()

        #Integration Data dict
        self.idata={}

        #Data Fields
        ai = pyFAI.load("PYFAI FILE/waxs_test.poni")
        data_dict=ai.get_config()
        options2 = qt.QGroupBox('Calibration Data')
        #layout2 = qt.QFormLayout(options2)
        layout2=qt.QFormLayout(options2)
        wavelength=qt.QLineEdit()
        distance=qt.QLineEdit()
        layout2.addRow('Distance:',distance)
        distance.setText(str(data_dict['dist']))
        layout2.addRow('Wave Length:',wavelength)
        wavelength.setText(str(data_dict['wavelength']))

        # 1D loaded Images List
        options3=qt.QWidget(self)
        layout3 =qt.QVBoxLayout(options3)
        layout3.addWidget(qt.QLabel('Integrated Images:'))
        loadedlistwidget = qt.QListWidget(self)
        layout3.addWidget(loadedlistwidget)
        self.loadedlistwidget=loadedlistwidget
        loadedlistwidget.itemSelectionChanged.connect(self.PlotMulCurves)
        loadedlistwidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        tools1d=qt.QLabel('1d Tools')
        tools1d.setStyleSheet("border: 1px solid black;")
        layout3.addWidget(tools1d)

        #Loaded Directory name
        frame = qt.QLabel(self)
        frame.setText("Directory:")
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

    def showInitalImage(self):
        """inital image logo"""
        plot = self.getPlotWidget()
        plot.getDefaultColormap().setName('viridis')
        im = Image.open('saxi-omer.jpeg')
        im=im.rotate(180, PIL.Image.NEAREST, expand = 1)
        im_mirror = PIL.ImageOps.mirror(im)
        plot.addImage(im_mirror)

    def InitiateCalibration(self):
        subprocess.run(["pyFAI-calib2"])

    def Integrate(self):
        plot = self.getPlotWidget()
        listwidget = self.listwidget
        loadedlist=self.loadedlistwidget
        datadict=self.idata
        img = fabio.open('new images/{}'.format(listwidget.selectedItems()[0].text()))
        cur_item=listwidget.selectedItems()[0].text()
        itemsTextList = [str(loadedlist.item(i).text()) for i in range(loadedlist.count())]
        if cur_item not in itemsTextList:
            loadedlist.addItem(cur_item)
        ai = pyFAI.load("PYFAI FILE/waxs_test.poni")
        img_array = img.data
        mask = fabio.open('new images/msk_waxs.msk')
        filename=listwidget.selectedItems()[0].text().split('.')[0]
        res = ai.integrate1d_ng(img_array,
                                4000,
                                mask=mask.data,
                                unit="q_nm^-1",
                                filename="new images/tests/{}.dat".format(filename),
                                error_model='poisson',
                                radial_range=(0,10))
        datadict[filename]=res
        plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(filename))
        plot.setGraphYLabel('Intensity')
        plot.setGraphXLabel('Scattering vector (nm-1)')
        plot.setYAxisLogarithmic(True)
        plot.resetZoom()

    def open(self):
        listwidget=self.listwidget
        filepath = qt.QFileDialog.getExistingDirectory(None, 'Select File')
        self.frame.setText('Directory :{}'.format(filepath))
        self.frame.setStyleSheet("border: 0.5px solid black;")
        self.frame.setFont(qt.QFont('Segoe UI',9))

        try:
            onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f)) and f.endswith('.tif')]
            for file in onlyfiles:
                listwidget.addItem(str(file))
        except FileNotFoundError:
            pass

    def ShowImage(self):
        listwidget = self.listwidget
        plot = self.getPlotWidget()
        plot.clear()
        #print('new images/'+str(listwidget.selectedItems()[0].text()))
        image=io.imread('new images/'+str(listwidget.selectedItems()[0].text()))
        plot.getDefaultColormap().setName('jet')
        cm = colors.Colormap(name='jet', normalization='log')
        plot.setDefaultColormap(cm)
        plot.setYAxisLogarithmic(False)
        plot.addImage(image)
        plot.resetZoom()

    def PlotMulCurves(self):
        loadedlist = self.loadedlistwidget
        plot = self.getPlotWidget()
        datadict=self.idata
        curvelist = [item.text() for item in loadedlist.selectedItems()]
        plot.clear()
        for curve in curvelist:
            name=curve.split('.')[0]
            res=datadict[name]
            plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(name))



def main():
    global app
    app = qt.QApplication([])
    window = MyPlotWindow()
    window.setAttribute(qt.Qt.WA_DeleteOnClose)
    window.showInitalImage()
    window.showMaximized()
    app.exec()


if __name__ == '__main__':
    main()