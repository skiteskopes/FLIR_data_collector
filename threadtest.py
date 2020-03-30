from tkinter import *
import time
import threading

class Threader(threading.Thread):

    def __init__(self, tbox, *args, **kwargs):

        threading.Thread.__init__(self, *args, **kwargs)
        self.tbox = tbox
        self.daemon = True # Stop threads when your program exits.
        self.start()

    def run(self):
        time.sleep(2)
        self.tbox.insert(END, "Some text1\n")

        time.sleep(2)
        self.tbox.insert(END, "Some text2\n")

        time.sleep(2)
        self.tbox.insert(END, "Some text3")


class MyClass(object):
        def __init__(self):
            self.root = Tk()

            button = Button(self.root, text="Button", command= lambda: Threader(tbox=self.tbox)).pack()

            #scrollbar and textbox
            scrollbar = Scrollbar(self.root)
            scrollbar.pack(side=RIGHT, fill=Y)
