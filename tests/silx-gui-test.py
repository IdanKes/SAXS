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
from PyQt5 import QtWidgets
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
        self.setWindowTitle("Saxii")
        icon=qt.QIcon('icon.png')
        self.setWindowIcon(icon)

        #layout
        options = qt.QWidget(self)
        layout = qt.QVBoxLayout(options)
        button = qt.QPushButton("Calibration Tool", self)
        button.clicked.connect(self.InitiateCalibration)
        layout.addWidget(button)
        button = qt.QPushButton("Load Folder", self)
        button.clicked.connect(self.open)
        layout.addWidget(button)
        listwidget=qt.QListWidget(self)
        layout.addWidget(listwidget)
        self.listwidget=listwidget
        listwidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        listwidget.itemSelectionChanged.connect(self.ShowImage)

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
        plot.setGraphGrid(which='both')

    def InitiateCalibration(self):
        subprocess.run(["pyFAI-calib2"])

    def full_integration(self,image,mask,poni,bins,minradius,maxradius,datadict):
        img = fabio.open('new images/{}'.format(image))
        ai = pyFAI.load("PYFAI FILE/waxs_test.poni")
        filename=image.split('.')[0]
        img_array = img.data
        print(bins,filename,minradius,maxradius)
        res = ai.integrate1d_ng(img_array,
                                bins,
                                mask=mask,
                                unit="q_nm^-1",
                                filename="new images/tests/{}.dat".format(filename),
                                error_model='poisson',
                                radial_range=(minradius, maxradius))
        datadict[filename] = res

    def Integrate(self):
        bins=int(self.bins.text())
        minradius=int(self.minradius.text())
        maxradius=int(self.maxradius.text())
        poni = None
        mask = fabio.open('new images/msk_waxs.msk')

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
            for item in datadict.items():
                filename = item[0]
                res = item[1]
                plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(filename),linewidth=2)


    def Integrate_all(self):
        bins = int(self.bins.text())
        minradius = int(self.minradius.text())
        maxradius = int(self.maxradius.text())
        poni = None
        mask = fabio.open('new images/msk_waxs.msk')

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

            imagelist=[str(listwidget.item(i).text()) for i in range(listwidget.count())]
            for image in imagelist:
                if image not in loadeditemsTextList:
                    loadedlist.addItem(image)
                self.full_integration(image=image,poni=poni,mask=mask.data,bins=bins,minradius=minradius,maxradius=maxradius,datadict=datadict)
            for item in datadict.items():
                name=item[0]
                res=item[1]
                plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(name), linewidth=2)

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

        if listwidget.selectedItems()==[]:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please Select an Image")
            x = msg.exec_()
        else:
            mypath = 'new images/' + str(listwidget.selectedItems()[0].text())
            plot.getDefaultColormap().setName('jet')
            cm = colors.Colormap(name='jet', normalization='log')
            plot.setDefaultColormap(cm)
            plot.setYAxisLogarithmic(False)
            plot.setKeepDataAspectRatio(True)
            plot.setGraphGrid(which=None)
            image = io.imread(mypath)
            plot.addImage(image,resetzoom=True)
            plot.resetZoom()

    def PlotMulCurves(self):
        def colorbank():
            bank=['blue','red','black','green']
            i=0
            while True:
                yield bank[i]
                i+=1
                i=i%len(bank)
        loadedlist = self.loadedlistwidget
        plot = self.getPlotWidget()
        plot.clear()
        self.curve_plot(plot)
        datadict=self.idata
        curvelist = [item.text() for item in loadedlist.selectedItems()]
        curvenames=[item.split('.')[0] for item in curvelist]
        a = colorbank()
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
            plot.addCurve(x=res1.radial,y=res3_intensity,legend='{}'.format(name1+' MINUS '+name2),linewidth=1,color='green')
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