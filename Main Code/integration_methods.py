import numpy
import re
import fabio
import pyFAI
from silx.gui.qt import QMessageBox, QFont
from utils import dotdict



def full_integration(self, image, mask, poni, bins, minradius, maxradius, q_choice, datadict, nxs, nxs_file_dict):
    if not nxs:
        imagefolder = self.imagepath
        imagepath = imagefolder + '/' + image
        img = fabio.open(imagepath)
        filename = image.split('.')[0]
        img_array = img.data
    if nxs:
        imagefolder = self.imagepath
        image_name = image.split('.')[0] + '.nxs'
        image_data = nxs_file_dict[image_name][image]
        img_array = image_data
        filename = image
    ai = pyFAI.load(poni)

    #FIX-ME angstrem bug
    if q_choice=="q_A^-1":
        res = ai.integrate1d_ng(img_array,
                                bins,
                                mask=mask,
                                unit="q_nm^-1",
                                filename="{}/{}.dat".format(imagefolder, filename),
                                error_model='poisson',
                                radial_range=(minradius, maxradius))

        new_radial=numpy.true_divide(res.radial, 10)
        new_res={'radial':new_radial,'intensity':res.intensity,'sigma':res.sigma}
        new_res=dotdict(new_res)
        datadict[filename] = new_res

    else:
        res = ai.integrate1d_ng(img_array,
                                bins,
                                mask=mask,
                                unit=q_choice,
                                filename="{}/{}.dat".format(imagefolder, filename),
                                error_model='poisson',
                                radial_range=(minradius, maxradius))
        datadict[filename] = res


def send_to_integration(self, imagelist):
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
            self.progressbar.setFont(QFont('Segoe UI',9))
            if image not in loadeditemsTextList:
                if (image.endswith('.tiff') or image.endswith('.tif')):
                    full_integration(self,image=image, poni=poni, mask=mask.data, bins=bins, minradius=minradius,
                                          maxradius=maxradius, q_choice=q_choice, datadict=datadict, nxs=False,
                                          nxs_file_dict=nxs_file_dict)

                    filename = image.split('.')[0]
                    res = datadict[filename]
                    plot.addCurve(x=res.radial, y=res.intensity, yerror=res.sigma, legend='{}'.format(filename),
                                  linewidth=2)
                    loadedlist.addItem(image)
                regexp = re.compile(r'(?:nxs - image ).*$')
                if regexp.search(image):
                    full_integration(self,image=image, poni=poni, mask=mask.data, bins=bins, minradius=minradius,
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