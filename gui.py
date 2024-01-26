from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
import traceback, sys , os
from mplwidget import MplWidget
from PyQt5 import uic
import serial
import serial.tools.list_ports
import time, datetime
import numpy as np
import mplcursors
import logging
from logging.handlers import TimedRotatingFileHandler
import matplotlib.pyplot as plt



class WorkerSignals(QObject):

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker2Signals(QObject):

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.kwargs["progress_callback"] = self.signals.progress

    def run(self):

        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class Worker2(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker2, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.kwargs["progress_callback"] = self.signals.progress

    def run(self):

        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class MatplotlibWidget(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        loadUi("Qt3.ui" , self)

        self.setWindowTitle("SeeedStudio Real Time Plot")

        self.index = self.BRbox.findText("115200")
        self.BRbox.setCurrentIndex(self.index)

        self.AddSerPorts()

        self.Connectbtn.setCheckable(True)
        self.Connectbtn.clicked[bool].connect(self.press)
        self.Exitbtn.clicked.connect(self.closeEvent)
        
        self.arr1motion = np.array([])
        self.arr2heart = np.array([])
        self.arr3breath = np.array([])
        self.arr4distance = np.array([])
        self.array_i = np.array([])
        self.i = 0
        self.curr_sec = 0
        self.prev_sec = 0
        self.result = ""

        self.motionvalue = "0"
        self.breathvalue = "0"
        self.heartvalue = "0"
        self.distancevalue = "0"


        self.motionplot = 0.0
        self.breathplot = 0.0
        self.heartplot = 0.0
        self.distanceplot = 0.0
        self.LoggingEnabled = 0

        self.Heartbeat_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.Heartbeat_label.setStyleSheet(
            'border: 5px solid black;background-color: rgb(85, 255, 255);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#0000ff;')
        
        ######################################################################
        self.Breathrate_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.Breathrate_label.setStyleSheet(
            'border: 5px solid black;background-color: rgb(85, 255, 255);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#aa0000;')
        ######################################################################
        # TOP RIGHT LABEL
        self.Motionvalue_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.Motionvalue_label.setStyleSheet(
            'border: 5px solid black;background-color: rgb(85, 255, 255);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#005500;')

        ######################################################################
        # 2nd TOP LEFT LABEL
        self.distance_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.distance_label.setStyleSheet(
            'border: 5px solid black;background-color: rgb(85, 255, 255);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#FFA500;')
        
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())


        ########################### Logging ##########################
        self.formatter = logging.Formatter("%(asctime)s, %(message)s", datefmt="%d-%b-%y,%H:%M:%S")
        
        self.handler = TimedRotatingFileHandler("log/Plot1.txt", when="M",interval=1, encoding="utf8")
        self.handler.suffix = "_%#d-%#m-%Y,%H-%M-%S"+".txt"
        self.handler.setFormatter(self.formatter)

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

        self.plotfilebtn.clicked.connect(self.PlotLogFile)
        self.checkBoxlog.setChecked(False)
        self.checkBoxlog.toggled.connect(lambda: self.checkBox(self.checkBoxlog))
        self.openfilebtn.clicked.connect(self._open_file_dialog)


        self.default_path = os.path.dirname(os.path.abspath(__file__))
        self.default_path = self.default_path + "C:/Users/azizb/OneDrive/Bureau/FZI/Heartbeat&Breathing Radar/Qt/QtVersion3/log"

    def _open_file_dialog(self):
        self.default_path = str(QFileDialog.getExistingDirectory())
        self.lineEdit.setText(self.default_path)

    def checkBox(self, chkbox):
        if chkbox.isChecked() == True:
            self.LoggingEnabled = 1 

        else:
            self.LoggingEnabled = 0
            self.time_label.setText("")
            print(chkbox.text() + " is not anymore selected")

    def PlotLogFile(self):
        self.logger.handlers.clear()
        self.LoggingEnabled = 0

        try:
            time_list=[]
            Time = []
            Data = []
            heartarray = []
            breatharray = []
            motionarray = []
            distancearray = []
            Dummytime = []
            CSVData = []
            i = 0

            with open(self.default_path + "/Plot1.txt" , "r") as f:
                for line in f.readlines():
                    i = i+1
                    time_list.append(line.split()[0])
                    Data.append(line.split()[2])
                    Dummytime.append(i)
                    CSVData.append(Data[0].split(","))

                for i in range(len(Data)):
                    test = Data[i].split(",")
                    heartarray.append(int(test[0]))
                    breatharray.append(int(test[1]))
                    motionarray.append(int(test[2]))
                    distancearray.append(int(test[3]))
                    Time_int = (time_list[i].split(","))
                    Time.append(Time_int[1])

            f.close()

            heartarrayNP = np.array((heartarray))
            breatharrayNP = np.array((breatharray))
            motionarrayNP = np.array((motionarray))
            distancearrayNP = np.array((distancearray))
            DummytimeNP_Array = np.array(Time)

            plt.ylim(0,300)
            plt.grid()
            plt.xticks(rotation=90, ha="right")
            plt.tight_layout()
            plt.tick_params(axis="x", which="major", labelsize=8)

            plt.plot(DummytimeNP_Array, heartarrayNP, label="HeartRate", marker="o", linestyle="-")
            plt.plot(DummytimeNP_Array, breatharrayNP, label="BreathRate", marker="+", linestyle="-")
            plt.plot(DummytimeNP_Array, motionarrayNP, label="MotionRate", marker=".", linestyle="-")
            plt.plot(DummytimeNP_Array, distancearrayNP, label="Distance", marker="x", linestyle="-")

            plt.legend(loc="upper left")
            plt.title("Real Time Plot", fontweight = "bold")
            plt.xlabel("Time")
            plt.ylabel("Values")
            plt.show()

            Time = []
            Data = []
            heartarray = []
            breatharray = []
            motionarray = []
            distancearray = []
            Dummytime = []
            CSVData = []
            heartarrayNP = np.array([])
            breatharrayNP = np.array([])
            motionarrayNP = np.array([])
            distancearrayNP = np.array([])

        except:
            print("file not found")

        


    def AddSerPorts(self):
        self.Ports = serial.tools.list_ports.comports()
        
        for x in range(len(self.Ports)):
            self.Port = self.Ports[x]
            print(self.Port)
            self.Portstr = str(self.Port)
            self.PortName = self.Portstr.split(" ")
            self.portnameA = self.PortName[0]
            self.Portsbox.addItems([self.portnameA])

    def closeEvent(self, event):

        reply = QMessageBox.question(
            self, "Message", 
            "Are you sure you want to quit? Any unsaved work will be lost.",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel)
        
        if reply == QMessageBox.Yes:
            sys.exit()
        else:
            pass

        

    #Problem when closing the App from the X Button, if you click Cancel the App crashes
    def keyPressEvent(self, event):
        """Close application from escape key.

        results in QMessageBox dialog from closeEvent, good but how/why?
        """
        if event.key() == Qt.Key_Escape:
            sys.exit()


    def press(self):
        if self.Connectbtn.isChecked():
            self.chosenport = self.Portsbox.currentText()
            self.chosenBR = self.BRbox.currentText()
            self.Connectbtn.setText("Connected")
            print("Connected to " + str(self.chosenport))

            worker = Worker(self.execute_this_fn)
            worker.signals.result.connect(self.print_output)
            worker.signals.finished.connect(self.thread_complete)

            self.threadpool.start(worker)

            worker2 = Worker(self.execute_this_fn2)  # Any other args, kwargs are passed to the run function
            worker2.signals.result.connect(self.print_output2)
            worker2.signals.finished.connect(self.thread_complete2)
            # worker.signals.progress.connect(self.progress_fn)

            # Execute
            self.threadpool.start(worker2)
        
        else:
            self.Connectbtn.setText("DISCONNECTED")
            print("DISCONNECTED from " + str(self.chosenport))
            self.logger.handlers.clear()
            self.LoggingEnabled = 0
            self.chosenport = 0

    def execute_this_fn(self, progress_callback):

        try:
            self.ser = serial.Serial(self.chosenport, self.chosenBR, timeout=0.1)
            time.sleep(0.25)

            print("I have opened "  +str(self.chosenport) + ", with Baud Rate "+str(self.chosenBR))
            print("Thread1 started")

            while (self.chosenport != 0):

                self.now = datetime.datetime.now()
                firstLine = self.ser.readline().decode("utf-8").rstrip()
                if "feature" in firstLine:
                    motionvaluestr = firstLine.split(" ")[9]
                    self.motionvalue = int(motionvaluestr)

                if "heart" in firstLine:
                    heartvaluestr = firstLine.split(' ')[8]
                    self.heartvalue = int(heartvaluestr)

                if "breath" in firstLine:
                    breathvaluestr = firstLine.split(' ')[8]
                    self.breathvalue = int(breathvaluestr)

                if "distance" in firstLine:
                    distancevaluestr = firstLine.split(" ")[11]
                    self.distancevalue = int(distancevaluestr)

                if "Radar detects that the current user is out of monitoring range." in firstLine:
                    self.OutofBounds_label.setStyleSheet(
            'border: 5px solid black;background-color: rgb(255,0,0);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#000000;')
                    self.OutofBounds_label.setText("YES")

                if "stationary" in firstLine:
                    self.Motiontext_label.setStyleSheet(
            'border: 5px solid black;background-color: rgb(0,255,0);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#000000;')
                    self.Motiontext_label.setText("Stationary")

                if "somebody in motion" in firstLine:
                    self.Motiontext_label.setStyleSheet(
            'border: 5px solid black;background-color: rgb(255,0,0);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#000000;')
                    self.Motiontext_label.setText("In Motion!!")

                if self.LoggingEnabled == 1 :
                    x = datetime.datetime.now()
                    print(x.second)
                    self.curr_sec = x.second

                    if self.curr_sec != self.prev_sec:
                        self.time_label.setText(
                            str(x.time().hour) + ":" + str(x.time().minute) + ":" + str(x.time().second))
                        
                        self.logger.info( str(self.heartvalue) +"," + str(self.breathvalue) + "," + str(self.motionvalue) + "," + str(self.distancevalue))
                    self.prev_sec = self.curr_sec

                self.update_labels()
            print("Port Closed")
            self.ser.close()
        
        except Exception as e:
            print("Port closed")
            self.ser.close()
            self.MplWidget.canvas.axes.clear()
            self.MplWidget.canvas.draw()
            print("Exception has occured")
            print(e)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setInformativeText(str(e))
            msg.setText("Please Select a Serial Port!")
            msg.setWindowTitle("Error")
            msg.exec()

    def execute_this_fn2(self, progress_callback):
        try:
            self.arr1motion = []
            self.arr2heart = []
            self.arr3breath = []
            self.arr4distance = []
            self.array_i = []
            self.MplWidget.canvas.axes.clear()
            self.MplWidget.canvas.draw()


            while(self.chosenport != 0):
                self.update_graph()

        except Exception as e:
            self.MplWidget.canvas.axes.clear()
            self.MplWidget.canvas.draw()
            print("Exception has occured")
            print(e)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setInformativeText(str(e))
            msg.exec()

    
    def update_graph(self):

        self.motionplot = int(self.motionvalue)
        self.arr1motion = np.append(self.arr1motion, self.motionplot)

        self.heartplot = int(self.heartvalue)
        self.arr2heart = np.append(self.arr2heart, self.heartplot)

        self.breathplot = int(self.breathvalue)
        self.arr3breath = np.append(self.arr3breath, self.breathplot)

        self.distanceplot = int(self.distancevalue)
        self.arr4distance = np.append(self.arr4distance, self.distanceplot)

        self.array_i = np.append(self.array_i, self.i)
        self.i = self.i + 1

        if self.i == 50:
            """self.arr1motion[0:50] = self.arr1motion[1:51]
            self.arr1motion[50] = int(self.motionvalue)

            self.arr2heart[0:50] = self.arr2heart[1:51]
            self.arr2heart[50] = int(self.heartvalue)

            self.arr3breath[0:50] = self.arr3breath[1:51]
            self.arr3breath[50] = int(self.breathvalue)

            self.arr4distance[0:50] = self.arr4distance[1:51]
            self.arr4distance[50] = int(self.distancevalue)"""
            self.i = 0
            self.array_i = []
            self.arr1motion = []
            self.arr2heart = []
            self.arr3breath = []
            self.arr4distance = []

        self.MplWidget.canvas.axes.clear()

        self.MplWidget.canvas.axes.plot(self.array_i, self.arr1motion, marker="*", linestyle= "-", color="#005500")
        self.MplWidget.canvas.axes.plot(self.array_i, self.arr2heart, marker=".", linestyle= "-", color= "#0000ff")
        self.MplWidget.canvas.axes.plot(self.array_i, self.arr3breath, marker="o", linestyle= "-", color= "#aa0000")
        self.MplWidget.canvas.axes.plot(self.array_i, self.arr4distance, marker="x", linestyle= "-", color= "#FFA500")

        self.MplWidget.canvas.axes.set_ylim(0,300)
        self.MplWidget.canvas.axes.set_xlim(0,50)
        self.MplWidget.canvas.axes.set_ylabel("Values")
        self.MplWidget.canvas.axes.legend(("Motionvalue", "Heartrate", "BreathRate" , "Distance"), loc= "upper right")
        self.MplWidget.canvas.axes.set_title("Real Time Plot")
        self.MplWidget.canvas.axes.grid(True, lw=".2", ls="--", c=".1")

        mplcursors.cursor(hover=True) 


        self.MplWidget.canvas.draw()
        
        
    def PlotLogFile(self):
        print("test")


    def print_output(self, s):
        print(s)

    def thread_complete(self):
        print("THREAD COMPLETE 1")
        

    def print_output2(self, s):
        print(s)

    def thread_complete2(self):
        print("THREAD2 COMPLETE!")

    def update_labels(self):

        self.Heartbeat_label.setText("{:.2f} ".format(float(self.heartvalue)))
        self.Breathrate_label.setText("{:.2f}".format(float(self.breathvalue)))
        self.Motionvalue_label.setText("{:.2f}".format(float(self.motionvalue)))
        self.distance_label.setText("{:.2f}".format(float(self.distancevalue)))

    




            



app = QApplication([])
app.setStyle("Fusion")
window = MatplotlibWidget()
window.show()
sys.exit(app.exec_())
