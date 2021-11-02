import subprocess
#installing packages
# package_list=['pyFAI','numpy']
# run_list=[]
# for package in package_list:
#     run_list.append('pip install {}'.format(package))
subprocess.run('pip install PyQt5')
subprocess.run('pip install pandas')
subprocess.run('pip install pyFAI')
subprocess.run('pip install numpy')
subprocess.run('pip install silx')
subprocess.run('pip install pillow==6.2.2')
subprocess.run('pip install nexusformat')
subprocess.run('pip install opencv-python')
subprocess.run('pip install fabio')
subprocess.run('pip install numpy')
subprocess.run('pip install scikit-image')
print('***********************************')
print('success!')
