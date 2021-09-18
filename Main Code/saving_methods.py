import pandas as pd
from silx.gui.qt import QMessageBox

def save_csv(self):
    filepath = self.imagepath
    q_choice = self.q_combo.currentText()
    loadedlist = self.loadedlistwidget
    curvelist = [item.text() for item in loadedlist.selectedItems()]
    curvenames = []
    for curve in curvelist:
        if '.nxs' in curve:
            curvenames.append(curve)
        else:
            curvenames.append(curve.split('.')[0])
    if curvelist == []:
        msg = QMessageBox()
        msg.setWindowTitle("Error")
        msg.setText("Please Select Integrated Curve to Save")
        x = msg.exec_()
    else:
        for curve in curvenames:
            df = pd.read_csv(r'{}/{}.dat'.format(filepath, curve), header=None, sep="\s+", skiprows=23)
            df.rename(columns={0: q_choice, 1: 'Intesnsity', 2: 'Sigma_I'}, inplace=True)
            df.to_csv(filepath + '/{}_csv.csv'.format(curve), index=False)