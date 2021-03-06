from silx.gui import colors
from silx.gui.qt import QMessageBox
import numpy as np
import cv2
import numpy

def curve_plot_settings(self, plot):
    plot.clear()
    q_choice = self.q_combo.currentText()
    plot.setGraphYLabel('Intensity')
    plot.setGraphXLabel('Scattering vector {}'.format(q_choice))
    plot.setYAxisLogarithmic(True)
    plot.setKeepDataAspectRatio(False)
    plot.setAxesDisplayed(True)
    # plot.setGraphGrid(which='both')
    self.toolbar1.setVisible(False)
    self.toolbar2.setVisible(True)


def image_plot_settings(self,plot):
    plot.getDefaultColormap().setName('jet')
    cm = colors.Colormap(name='jet', normalization='log')
    plot.setDefaultColormap(cm)
    plot.setYAxisLogarithmic(False)
    plot.setKeepDataAspectRatio(True)
    plot.setGraphGrid(which=None)
    plot.setGraphYLabel('')
    plot.setGraphXLabel('')
    self.toolbar1.setVisible(True)
    self.toolbar2.setVisible(False)


def plot_restricted_radius_image(self, plot, image,new_image):
    plot.clear()
    if new_image:
        plot.addImage(image, resetzoom=True)
        self.displayed_image_range=plot.getDataRange()
        self.max_radius=numpy.sqrt((self.displayed_image_range[0][1]-self.beamcenterx)**2+(self.displayed_image_range[1][1]-self.beamcentery)**2)
    else:
        centerx=int(self.beamcenterx)
        centery=int(self.beamcentery)
        cv2.circle(image,(centerx,centery),int(self.min_radius),(255, 255, 255),3)
        cv2.circle(image, (centerx, centery), int(self.max_radius), (255, 255,255), 3)
        cv2.drawMarker(image, (centerx, centery), color=(255, 255, 255), markerSize=25, thickness=2)
        plot.addImage(image,resetzoom=True)
        #image_plot_settings(self,plot)
        self.displayed_image_range = plot.getDataRange()

def plot_center_beam_image(self, plot, image):
    plot.clear()
    centerx = int(self.beamcenterx)
    centery = int(self.beamcentery)
    self.beamcenterxdisplay.setText('%.2f' % centerx)
    self.beamcenterydisplay.setText('%.2f' % centery)
    cv2.drawMarker(image, (centerx, centery),color=(255,255,255),markerSize = 25,thickness=2)
    cv2.circle(image, (centerx, centery), int(self.min_radius), (255, 255, 255), 3)
    cv2.circle(image, (centerx, centery), int(self.max_radius), (255, 255, 255), 3)
    plot.addImage(image, resetzoom=True)
    #image_plot_settings(self,plot)
    self.set_min_button.setEnabled(True)
    self.set_max_button.setEnabled(True)
    self.setqminAction.setEnabled(True)
    self.setqmaxAction.setEnabled(True)
    self.set_max_button.setToolTip('You can also right click the plot!')
    self.set_min_button.setToolTip('You can also right click the plot!')
#
def colorbank():
    bank = ['blue', 'red', 'black', 'green']
    i = 0
    while True:
        yield bank[i]
        i += 1
        i = i % len(bank)

def plot_mul_curves(self):
    loadedlist = self.loadedlistwidget
    plot = self.getPlotWidget()
    plot.clear()
    curve_plot_settings(self, plot)
    datadict=self.idata
    curvelist = [item.text() for item in loadedlist.selectedItems()]
    a = colorbank()
    for curve in curvelist:
        color = next(a)
        if 'SUBTRACT' in curve:
            res = datadict[curve]
            plot.addCurve(x=res['radial'], y=res['intensity'], yerror=res['sigma'], legend='{}'.format(curve),color=color, linewidth=2)
        elif 'nxs' in curve:
            res = datadict[curve]
            plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(curve), color=color,
                           linewidth=2)
        else:
            name=curve.split('.')[0]
            res=datadict[name]
            plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(name),color=color,linewidth=2)

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
        res3_intensity=abs(np.subtract(res1.intensity,res2.intensity))
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