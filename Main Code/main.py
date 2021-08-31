import numpy
from silx.gui import qt
from skimage import io
from silx.gui.plot.PlotWindow import PlotWindow
from os import listdir,path
from os.path import isfile, join
from silx.gui import colors
import pyFAI, fabio
import subprocess
from PIL import Image, ImageOps
import PIL
from silx.gui.plot import tools
from PyQt5 import QtWidgets, QtCore
from silx.gui.widgets.BoxLayoutDockWidget import BoxLayoutDockWidget
from PyQt5.QtWidgets import QMessageBox
import importlib
a=importlib.import_module('files.docklegend')
MyCurveLegendsWidget=a.MyCurveLegendsWidget


class MyPlotWindow(qt.QMainWindow):

    def __init__(self, parent=None):
        super(MyPlotWindow, self).__init__(parent)

        # Create a PlotWidget
        self._plot = PlotWindow(parent=self)
        a=qt.QSize(10,10)

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
        self.setWindowTitle("Saxsii")
        icon=qt.QIcon('icon.png')
        self.setWindowIcon(icon)

        #layout
        options = qt.QWidget(self)
        layout = qt.QVBoxLayout(options)
        button = qt.QPushButton("Calibration Tool", self)
        button.clicked.connect(self.InitiateCalibration)
        layout.addWidget(button)
        button = qt.QPushButton("Load Image Folder", self)
        button.clicked.connect(self.open)
        layout.addWidget(button)
        listwidget=qt.QListWidget(self)
        layout.addWidget(listwidget)
        self.listwidget=listwidget
        listwidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        listwidget.itemSelectionChanged.connect(self.ShowImage)
        button = qt.QPushButton("Load PONI File", self)
        button.clicked.connect(self.open_poni)
        layout.addWidget(button)
        poni_label=qt.QLabel(self)
        poni_label.setText('No PONI')
        self.poni_label=poni_label
        layout.addWidget(button)
        layout.addWidget(poni_label)
        button = qt.QPushButton("Load Mask File", self)
        button.clicked.connect(self.open_mask)
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
        self.q_choice=q_combobox.currentText()

        buttonsWidget = qt.QWidget()
        buttonsWidgetLayout = qt.QHBoxLayout(buttonsWidget)
        buttons = ['Integrate Selected','Integrate All']
        addbuttons = [qt.QPushButton(c) for c in buttons]
        addbuttons[0].clicked.connect(self.Integrate)
        addbuttons[1].clicked.connect(self.Integrate_all)
        for button in addbuttons:
            buttonsWidgetLayout.addWidget(button)
        layout.addWidget(buttonsWidget)

        layout.addStretch()

        #Integration Data dict
        self.idata={}

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
        self.wavelength=wavelength
        self.distance=distance
        self.beamcenterx=beamcenterx
        self.beamcentery=beamcentery

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
        subtracttbut=qt.QPushButton('subtract',self)
        layout3.addWidget(subtracttbut)
        subtracttbut.clicked.connect(self.subtractcurves)

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

    def curve_plot(self,plot):
        plot.clear()
        plot.setGraphYLabel('Intensity')
        plot.setGraphXLabel('Scattering vector (nm^-1)')
        plot.setYAxisLogarithmic(True)
        plot.setKeepDataAspectRatio(False)
        plot.setAxesDisplayed(True)
        #plot.setGraphGrid(which='both')

    def InitiateCalibration(self):
        subprocess.run(["pyFAI-calib2"])

    def full_integration(self,image,mask,poni,bins,minradius,maxradius,datadict):
        imagefolder=self.imagepath
        imagepath=imagefolder+'/'+image
        img = fabio.open(imagepath)
        ai = pyFAI.load(poni)
        filename=image.split('.')[0]
        img_array = img.data
        res = ai.integrate1d_ng(img_array,
                                bins,
                                mask=mask,
                                unit="q_A^-1",
                                filename="{}/{}.dat".format(imagefolder,filename),
                                error_model='poisson',
                                radial_range=(minradius, maxradius))
        datadict[filename] = res

    def Integrate(self):
        bins=int(self.bins.text())
        minradius=int(self.minradius.text())
        maxradius=int(self.maxradius.text())
        poni = self.poni_file
        mask = fabio.open(self.mask_file)

        plot = self.getPlotWidget()
        self.curve_plot(plot)

        listwidget = self.listwidget
        datadict=self.idata
        imagelist = [item.text() for item in listwidget.selectedItems()]
        loadedlist = self.loadedlistwidget
        loadeditemsTextList = [str(loadedlist.item(i).text()) for i in range(loadedlist.count())]
        if len(imagelist)==0:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please Select an Image to Integrate")
            x = msg.exec_()
        else:
            for image in imagelist:
                if image not in loadeditemsTextList:
                    loadedlist.addItem(image)

                self.full_integration(image=image, poni=poni, mask=mask.data, bins=bins, minradius=minradius,
                                      maxradius=maxradius, datadict=datadict)
            for image in imagelist:
                filename = image.split('.')[0]
                res = datadict[filename]
                plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(filename),linewidth=2)



    def Integrate_all(self):
        bins = int(self.bins.text())
        minradius = int(self.minradius.text())
        maxradius = int(self.maxradius.text())
        poni = self.poni_file
        mask = fabio.open(self.mask_file)

        datadict = self.idata
        listwidget = self.listwidget
        loadedlist = self.loadedlistwidget
        loadeditemsTextList = [str(loadedlist.item(i).text()) for i in range(loadedlist.count())]

        if listwidget.count()==0:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("No Images to Integrate")
            x = msg.exec_()
        else:
            plot = self.getPlotWidget()
            self.curve_plot(plot)
            a = self.colorbank()

            imagelist=[str(listwidget.item(i).text()) for i in range(listwidget.count())]
            for image in imagelist:
                if image not in loadeditemsTextList:
                    loadedlist.addItem(image)
                self.full_integration(image=image,poni=poni,mask=mask.data,bins=bins,minradius=minradius,maxradius=maxradius,datadict=datadict)
            for item in datadict.items():
                name=item[0]
                res=item[1]
                plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(name), linewidth=2,color=next(a))

    def open(self):
        listwidget=self.listwidget
        filepath = qt.QFileDialog.getExistingDirectory(None, 'Select File')
        self.frame.setText('Directory :{}'.format(filepath))
        self.frame.setStyleSheet("border: 0.5px solid black;")
        self.frame.setFont(qt.QFont('Segoe UI',9))
        self.imagepath=filepath

        try:
            onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f)) and f.endswith('.tif')]
            for file in onlyfiles:
                listwidget.addItem(str(file))
        except FileNotFoundError:
            pass

    def open_poni(self):
        filepath = qt.QFileDialog.getOpenFileName(self,filter='*.poni')
        self.poni_file=filepath[0]
        self.poni_label.setText('loaded PONI file: /{}'.format(filepath[0].split("/")[-1]))
        #self.frame.setStyleSheet("border: 0.5px solid black;")
        self.poni_label.setFont(qt.QFont('Segoe UI',9))
        ai = pyFAI.load(self.poni_file)
        data_dict = ai.get_config()
        layout2=self.layout2
        self.distance.setText(str(data_dict['dist']))
        self.wavelength.setText(str(data_dict['wavelength']))
        self.fit2ddata=ai.getFit2D()
        self.beamcenterx.setText(str(self.fit2ddata['centerX']))
        self.beamcentery.setText(str(self.fit2ddata['centerY']))

    def open_mask(self):
        filepath = qt.QFileDialog.getOpenFileName(self,filter='*.msk')
        self.mask_file=filepath[0]
        self.mask_label.setText('loaded Mask file: /{}'.format(filepath[0].split("/")[-1]))
        #self.frame.setStyleSheet("border: 0.5px solid black;")
        self.mask_label.setFont(qt.QFont('Segoe UI',9))

    def ShowImage(self):
        listwidget = self.listwidget
        plot = self.getPlotWidget()
        plot.clear()

        if listwidget.selectedItems()==[]:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please Select an Image")
            x = msg.exec_()
        else:
            mypath = self.imagepath +'/'+ str(listwidget.selectedItems()[0].text())
            print(mypath)
            plot.getDefaultColormap().setName('jet')
            cm = colors.Colormap(name='jet', normalization='log')
            plot.setDefaultColormap(cm)
            plot.setYAxisLogarithmic(False)
            plot.setKeepDataAspectRatio(True)
            plot.setGraphGrid(which=None)
            image = io.imread(mypath)
            plot.addImage(image,resetzoom=True)
            plot.resetZoom()

    def colorbank(self):
        bank = ['blue', 'red', 'black', 'green']
        i = 0
        while True:
            yield bank[i]
            i += 1
            i = i % len(bank)

    def PlotMulCurves(self):
        loadedlist = self.loadedlistwidget
        plot = self.getPlotWidget()
        plot.clear()
        self.curve_plot(plot)
        datadict=self.idata
        curvelist = [item.text() for item in loadedlist.selectedItems()]
        curvenames=[item.split('.')[0] for item in curvelist]
        a = self.colorbank()
        for curve in curvenames:
            name=curve
            res=datadict[name]
            color=next(a)
            plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(name),color=color,linewidth=2)

    def subtractcurves(self):
        loadedlist = self.loadedlistwidget
        plot = self.getPlotWidget()
        datadict = self.idata
        curvelist = [item.text() for item in loadedlist.selectedItems()]
        curvenames = [item.split('.')[0] for item in curvelist]
        if len(curvelist)==2:
            name1 = curvenames[0]
            name2=curvenames[1]
            res1 = datadict[name1]
            res2=datadict[name2]
            res3_intensity=abs(numpy.subtract(res1.intensity,res2.intensity))
            plot.addCurve(x=res1.radial,y=res3_intensity,legend='{}'.format(name1+' SUBTRACT '+name2),linewidth=1,color='green')
            plot.setGraphGrid(which='both')

        else:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please select only 2 curves to subtract")
            x = msg.exec_()

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