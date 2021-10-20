class Image:
    def __init__(self):
        self.image_name = None
        self.markers = []
        self.two_d_image=None
        self.one_d_image=None

class TwoDImage(Image):
    def __init__(self,father):
        self.image_data=None
        self.one_d = None
        self.name=father.image_name
        self.markers=father.markers

class OneDImage(Image):
    def __init__(self,father):
        self.data=None
        self.two_d_image=None
        self.name = father.image_name
        self.markers = father.markers


a=Image
a.markers=[1,2,3,4]
a.image_name='hello'
b=TwoDImage(a)
b.image_data=[1,2,3]
a.two_d_image=b
c=OneDImage(a)
a.one_d_image=c
print(a.two_d_image.name,a.one_d_image.markers,a.two_d_image.markers,b.markers)
a.markers=[1,2]
print(b.markers)