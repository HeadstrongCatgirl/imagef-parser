from MyLittleParserUi import Ui_MainWindow
import imgfap
from functools import partial
from PyQt5.QtWidgets import QApplication
from sys import argv, exit
from asyncio import ensure_future
import threading
consumers = [
    ensure_future(imgfap.main(imgfap.client, q=imgfap.galQ)),
    ensure_future(imgfap.organizer(imgfap.client, q=imgfap.orgQ, galQ=imgfap.galQ))
]
app = QApplication(argv)
window = Ui_MainWindow()

window.pushButton.clicked.connect(
    partial(window.getInput, imgfap.galQ, imgfap.orgQ))
window.show()
# loop = threading.Thread(target=imgfap.loop.run_forever)
# loop.start()
loop0 = threading.Thread(target=exit, args=(app.exec_(), ))
loop0.start()
imgfap.loop.run_forever()
