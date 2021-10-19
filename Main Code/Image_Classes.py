class TwoDImage:
    def __init__(self):
        self.image_name=None
        self.image_data=None
        self.markers=[]
        self.was_processed=False
        self.one_d = None

class OneDImage:
    def __init__(self):
        self.name=None
        self.data=None
        self.markers=[]
        self.two_d_image=None
