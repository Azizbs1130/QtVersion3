
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class  MplWidget (QWidget):
    
    def  __init__ ( self, parent  =  None ):

        QWidget.__init__ (self, parent)

        self.canvas = FigureCanvas (Figure ())
        
        vertical_layout  =  QVBoxLayout () 
        vertical_layout.addWidget (self.canvas )
        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)
        vertical_layout.addWidget(self.toolbar)




        self.setLayout (vertical_layout )