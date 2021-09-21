import numpy
import re
from silx.gui import qt
from skimage import io
from silx.gui.plot.PlotWindow import PlotWindow
import fabio
import subprocess
from PIL import Image
from silx.gui.plot import tools
from PyQt5 import QtWidgets
from silx.gui.widgets.BoxLayoutDockWidget import BoxLayoutDockWidget
from docking_bars import MyCurveLegendsWidget
from open_methods import open_directory,open_poni,open_mask,open_nxs
from plotting_methods import image_plot,curve_plot,plot_mul_curves,subtractcurves
from saving_methods import save_csv
from integration_methods import full_integration,send_to_integration
import pyFAI.units as unit


class MyPlotWindow(qt.QMainWindow):
    """configuring GUI Parameteres and functionalities"""
    def __init__(self, parent=None):
        super(MyPlotWindow, self).__init__(parent)

        # Creating a PlotWidget
        self._plot = PlotWindow(parent=self,roi=False,print_=False,control=True)

        #menu bar
        menuBar = self.menuBar()
        fileMenu = qt.QMenu("&More Options", self)
        menuBar.addMenu(fileMenu)
        self.save_csv_action = qt.QAction('Save Integrated Data as CSV File...',self)
        fileMenu.addAction(self.save_csv_action)
        self.save_csv_action.triggered.connect(self.save_csv_wrap)
        self.beamcenterx=0
        self.beamcentery=0
        self.wavelength=0

        #add functionalities to toolbar
        plot_tool_bar=self.getPlotWidget().toolBar()
        toolButton = qt.QToolButton(self)
        toolButton.setCheckable(True)
        plot_tool_bar.addWidget(toolButton)

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
        progressbar.setFixedSize(290,30)
        progressbar.setTextVisible(False)
        self.progressbar=progressbar
        toolBar1.addWidget(position)
        toolBar1.addWidget(progressbar)

        #window parameters
        self.setWindowTitle("Saxsii")
        icon=qt.QIcon('files/icon.png')
        self.setWindowIcon(icon)

        #layout coniguration
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

        #Integration Data dicts
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

        # Integrated Images List
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
        subtracttbut.clicked.connect(self.subtract_curves_wrap)

        #Loaded Directory name
        frame = qt.QLabel(self)
        frame.setText("Directory:")
        frame.setFont(qt.QFont('Segoe UI', 9))
        self.frame = frame
        self.frame.setStyleSheet("border: 0.5px solid black;")

        # Gui Geometry Settings
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

        #legend dock
        plot = self._plot
        curveLegendsWidget = MyCurveLegendsWidget()
        curveLegendsWidget.setPlotWidget(plot)
        dock = BoxLayoutDockWidget()
        dock.setWindowTitle('Curve legends')
        dock.setWidget(curveLegendsWidget)
        plot.addDockWidget(qt.Qt.TopDockWidgetArea, dock)

    def getPlotWidget(self):
        return self._plot

    def getIntegrationParams(self):
        bins = int(self.bins.text())
        minradius = float(self.minradius.text())
        maxradius = float(self.maxradius.text())
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
        im=numpy.flip(im,0)
        plot.addImage(im)

    def InitiateCalibration(self):
        subprocess.run(["pyFAI-calib2"])

    def Integrate_selected(self):
        tw=self.tw
        imagelist=[item.text(0) for item in tw.selectedItems()]
        send_to_integration(self,imagelist)

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
        send_to_integration(self,imagelist_names)

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

    def subtract_curves_wrap(self):
        subtractcurves(self)

    def save_csv_wrap(self):
        save_csv(self)

def main():
    from styling import return_style
    StyleSheet=return_style()
    global app
    app = qt.QApplication([])
    app.setStyleSheet(StyleSheet)
    app.setStyle('Fusion')
    window = MyPlotWindow()
    window.setAttribute(qt.Qt.WA_DeleteOnClose)
    window.showInitalImage()
    window.showMaximized()
    app.exec()

if __name__ == '__main__':
    main()