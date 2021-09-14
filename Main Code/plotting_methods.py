from silx.gui import colors

def curve_plot(self,plot):
    plot.clear()
    q_choice = self.q_combo.currentText()
    plot.setGraphYLabel('Intensity')
    plot.setGraphXLabel('Scattering vector {}'.format(q_choice))
    plot.setYAxisLogarithmic(True)
    plot.setKeepDataAspectRatio(False)
    plot.setAxesDisplayed(True)
    # plot.setGraphGrid(which='both')


def image_plot(plot):
    plot.clear()
    plot.getDefaultColormap().setName('jet')
    cm = colors.Colormap(name='jet', normalization='log')
    plot.setDefaultColormap(cm)
    plot.setYAxisLogarithmic(False)
    plot.setKeepDataAspectRatio(True)
    plot.setGraphGrid(which=None)
    plot.setGraphYLabel('')
    plot.setGraphXLabel('')


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
    curve_plot(self,plot)
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