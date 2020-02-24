
'''
-------------------------------------------------------
FLIR Systems - Windows Data_Curation_Tool ver 1.1.0
-------------------------------------------------------
by: Bill Zhang
- Tkinter application for opening and cropping the RGB counterparts of FLIR
  IR camera images to better match the resolution and frame of reference.
- Internal AGC functionality is translated from Andres Prieto-Moreno's
  BosonUSB.cpp
- https://github.com/FLIR/BosonUSB/blob/master/BosonUSB.cpp
- 8-21-2019: Functionality with keypress
- 8-30-19: Integration of side_by_side.py along with frame_cropper tool
- 8-30-19: Integration of Delete button in side_by_side with makedirs
- 8-31-19: Integration of keypress for side_by_side tool
- 8-31-19: Integration of Error Message system for user friendliness
- 9-4-19: Integration of Pair Count and filename label for image_viewer_function
- 12-21-19 Converted Everything to OOB Format and all Windows are Now Centered
'''
from tkinter import *
import cv2
import numpy as np
import imghdr
import os
import PIL.Image, PIL.ImageTk
import numpy as np
from tkinter import filedialog
import math
import gc
from tkinter import messagebox
import tifffile as tiff
global counter
global number_label
import tifffile
global label1
import shutil
class FLIR_DATA_COLLECTOR(Frame):
    def __init__(self,master):
        self.master = master
        master.title("FLIR_DATA_COLLECTOR")
        master.iconbitmap('flam.ico')
        master.geometry("350x200")
        self.BOX_DOWNLOAD_label = Label(master,text="Pull Data From Conservator Tool:").place(x=15,y=50)
        self.side_by_side_label = Label(master,text="Open RGB and IR Tool:").place(x=15,y=100)
        self.menu_label = Label(master,text="Data_Curation_Tool version 1.1.0 by Bill Zhang").place(x=15,y=10)
        self.BOX_DOWNLOAD_button = Button(master, text = "Start", command =
        self.box_download_function, bg = 'navy blue', fg = 'white').place(x=250,y=50)
        self.image_viewer_button = Button(master, text = "Start", command =
        self.image_viewer_function, bg = 'navy blue', fg = 'white').place(x=250,y=100)
        self.frame_cropper_button = Button(master, text = "Start", command =
        self.frame_cropper_function, bg = 'navy blue', fg = 'white').place(x=250,y=150)
        self.frame_cropper_label = Label(master,text="Frame Cropper Tool:").place(x=15,y=150)
    def box_download_function(self):
        root.withdraw()
        window = Tk()
        frame_cropper = BOX_DOWNLOAD(window)
        window.mainloop()
    def image_viewer_function(self):
        root.withdraw()
        window1 = Tk()
        w = 850 # width for the Tk root
        h = 175 # height for the Tk root
        ws = window1.winfo_screenwidth() # width of the screen
        hs = window1.winfo_screenheight() # height of the screen
        xx = (ws/2) - (w/2)
        yy = (hs/2) - (h/2)
        window1.geometry('%dx%d+%d+%d' % (w, h,xx,yy))
        image_viewer = IMAGE_VIEWER(window1)
        window1.mainloop()
    def frame_cropper_function(self):
        root.withdraw()
        window = Tk()
        frame_cropper = FRAME_CROPPER(window)
        window.mainloop()
class FRAME_CROPPER(Frame):
    def __init__(self,master):
        master.iconbitmap('flam.ico')
        master.title("FLIR FRAME CROPPER")
class IMAGE_VIEWER(Frame):
    def __init__(self,master):
        master.iconbitmap('flam.ico')
        master.title("FLIR IMAGE VIEWER")
        master.geometry("850x175")
        self.button = Button(master, text = "Start", bg = 'navy blue', fg = 'white',
        command = self.open_images).grid(row = 7, column = 1)
        master.resizable(width=False, height=False)
        self.radioselection = IntVar()
        self.R4 = Radiobutton(master, text="Dual PRO 13mm 640, 32 deg HFOV", variable=self.radioselection, value=1, command=self.thirteen)
        self.R4.grid(row=4,column=1 )
        self.R5 = Radiobutton(master, text="Dual PRO 19mm 640, 32 deg HFOV", variable=self.radioselection, value=2, command=self.nineteen)
        self.R5.grid(row=5,column=1 )
        self.R6 = Radiobutton(master, text="Dual PRO 25mm 640, 32 deg HFOV", variable=self.radioselection, value=3, command=self.twentyfive)
        self.R6.grid(row=6,column=1 )
        self.R4.select()
        self.R4.invoke()
        self.radiolabel = Label(master,text="Select camera model here:").grid(row=4,column=0)
        self.instructions = Label(master,text="Select Directory for Data containting RGB and IR images:").grid(row=0,column=1)
        self.RGB = Label(master,text="Directory").grid(row = 2, column = 0)
        self.rgbbutton = Button(master, text = "Select", command =
        self.select_rgb, bg = 'navy', fg = 'white').grid(row =2, column =1)
        self.label1 = Label(master, text = 'Please Select Directory',fg='black')
        self.label1.grid(row=2, column=2)
        self.filename1 = "NULL"
    def thirteen(self):
        self.scale_percent = 88
    def nineteen(self):
        self.scale_percent = 200
    def twentyfive(self):
        self.scale_percent = 225
    def open_images(self):
        if self.filename1 == "NULL":
            self.label1.config(text = 'No Directory Selected',fg='red')
        else:
            gc.disable()
            window2 = Toplevel()
            open_images = OPEN_IMAGES(window2,self.scale_percent,self.filename1,self.label1)
    def select_rgb(self):
        self.filename1 = filedialog.askdirectory()
        self.label1.config(text = self.filename1,fg='green')
class OPEN_IMAGES(Frame):
    def __init__(self,master,scale_percent,filename1,label1):
        self.master = master
        master.bind("<Right>",self.next_key)
        master.bind("<Left>",self.back_key)
        self.counter = 0
        self.scale_percent = scale_percent
        self.filename1 = filename1
        master.title("FLIR Image Viewer")
        master.iconbitmap('flam.ico')
        self.counter_list = []
        gc.disable()
        self.tiff_files = list()
        self.jpg_files = list()
        self.new_rgb = list()
        self.new_ir = list()
        for ir_filename in os.listdir(self.filename1):
            if ir_filename.endswith('.TIFF'):
                self.tiff_files.append(ir_filename)
        for rgb_filename in os.listdir(self.filename1):
            if rgb_filename.endswith('JPG'):
                self.jpg_files.append(rgb_filename)
        for file in self.tiff_files:
            ir_name = re.split('_|\\.',file)
            ir_name_clone = ir_name[:]
            for i in ir_name_clone:
                if not i.isnumeric():
                    ir_name.remove(i)
            for files in self.jpg_files:
                rgb_name = re.split('_|\\.',files)
                rgb_name_clone = rgb_name[:]
                for ii in rgb_name_clone:
                    if not ii.isnumeric():
                        rgb_name.remove(ii)
                if ir_name == rgb_name:
                    self.new_rgb.append(files)
                    self.new_ir.append(file)
        self.pair_amount = len(self.new_rgb)
        if self.pair_amount ==0:
            master.destroy()
            label1.config(text ="ERROR: Selected directory does not have valid images", fg= "red")
        else:
            self.grabrgb = filename1 + str('/')+str(self.new_rgb[0])
            self.grabir = filename1 + str('/')+str(self.new_ir[0])
            print(self.grabrgb)
            self.rgb_img1 = cv2.cvtColor(cv2.imread(self.grabrgb), cv2.COLOR_BGR2RGB)
            self.rgb_scale_percent = 15
            self.rgb_width = int(self.rgb_img1.shape[1] * self.rgb_scale_percent / 100)
            self.rgb_height = int(self.rgb_img1.shape[0] * self.rgb_scale_percent / 100)
            self.dim1 = (self.rgb_width, self.rgb_height)
            self.rgb_img = cv2.resize(self.rgb_img1, self.dim1, interpolation = cv2.INTER_AREA)
            #IR remask
            self.ir_img = np.zeros((512, 640), dtype = "uint8")
            self.array=tiff.imread(self.grabir)
            self.max = np.amax(self.array)
            self.min = np.amin(self.array)
            for a in range (0,512):
                for b in range (0,640):
                    self.ir_img[a][b] = ( ( 255 * ( self.array[a][b] - self.min) ) ) // (self.max-self.min)
            self.ir_resized_width = int(self.ir_img.shape[1] * self.scale_percent // 100)
            self.ir_resized_height = int(self.ir_img.shape[0] * self.scale_percent // 100)
            self.dim = (self.ir_resized_width, self.ir_resized_height)
            self.ir_img1 = cv2.resize(self.ir_img, self.dim, interpolation =cv2.INTER_AREA)
            self.height, self.width, self.nochannels = self.rgb_img.shape
            self.height1, self.width1, = self.ir_img1.shape
            self.newheight = self.height + 150
            self.newwidth = self.width +563
            self.ws = master.winfo_screenwidth() # width of the screen
            self.hs = master.winfo_screenheight() # height of the screen
            self.xx = (self.ws/2) - (self.newwidth/2)
            self.yy = (self.hs/2) - (self.newheight/2)
            master.geometry('%dx%d+%d+%d' % (self.newwidth, self.newheight,self.xx,self.yy))
            master.resizable(width=False, height=False)
            self.canvas1 = Canvas(master, width = self.width, height = self.height, bg='navy blue')
            self.canvas1.pack(expand = YES, fill=BOTH)
            self.rgblabel1 = Label(self.canvas1, text = '{0}'.format(self.new_rgb[0]), bg = 'navy', fg = 'white')
            self.rgblabel1.place(x=self.width//2-80, y=self.height + 40)
            self.irlabel1 =  Label(self.canvas1, text = '{0}'.format(self.new_ir[0]), bg = 'navy', fg = 'white')
            self.irlabel1.place(x=self.width+563//2-50, y=self.height + 40)
            self.number_label = Label(self.canvas1, text = '0{0} of {1}'.format(self.counter+1, self.pair_amount), bg = 'navy', fg = 'white')
            self.number_label.place(x=self.width-21, y=self.height + 40)
            self.next_button = Button(self.canvas1, text = "Next", command = self.Next, bg ='navy', fg='white').place(x=0,y=0)
            self.back_button = Button(self.canvas1, text="Back", command = self.Back, bg= 'navy', fg='white')
            self.back_button.place(x=35,y=0)
            self.delete_button = Button(self.canvas1, text="Delete", command = self.Delete, bg= 'navy', fg='white')
            self.delete_button.place(x=70,y=0)
            self.help_button = Button(self.canvas1, text="Help", command = self.Help, bg= 'navy', fg='white')
            self.help_button.place(x=112,y=0)
            self.entry_box = Entry(self.canvas1)
            self.entry_box.place(x=self.width+5, y=self.height + 80)
            self.entry_label = Label(self.canvas1, text="Jump to Image:", fg = 'white', bg= 'navy')
            self.entry_label.place(x=self.width-85, y=self.height + 80)
            self.entry_button = Button(self.canvas1, text="Jump", command = self.Jump, bg= 'white', fg='navy')
            self.entry_button.place(x=self.width+48, y=self.height + 110)
            self.rgbimage = PIL.Image.fromarray(self.rgb_img)
            self.photo = PIL.ImageTk.PhotoImage(self.rgbimage)
            self.canvas1_w = self.width/2
            self.canvas1_h = self.height/2 + 25
            self.canvas2_w =  self.width1/2
            self.canvas2_h = self.height1/2 +25
            self.irimage = PIL.Image.fromarray(self.ir_img1)
            self.photo1 = PIL.ImageTk.PhotoImage(self.irimage)
            self.canvas2 = self.canvas1.create_image(self.canvas2_w + self.width,self.canvas2_h,image=self.photo1)
            self.canvas1.create_image(self.canvas1_w, self.canvas1_h ,image=self.photo)
            self.error_label = Label(self.canvas1, text ="Dummmy Label", fg = 'red', bg ='white')
            """
            self.enter_class = Entry(self.canvas1)
            self.enter_class.place()
            self.enter_class_label = Label(self.canvas1, text = "Enter COCO Class Here")
            self.coco_class_list = ["person, "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck, "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "tennis racket", "bottle", "wine glass", "cup", "fork","knife","spoon", "bowl", "apple","banana", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed","dining table", "toilet", "tv", "laptop","mouse","remote","keyboard","cell phone","microwave","oven","toaster","sink","refrigerator","book","clock","vase","scissors","teddy bear","hair drier","toothbrush"]
            creating tag buttons
            """
    def Next(self):
        self.counter += 1
        while self.counter in self.counter_list:
            self.counter += 1
        if self.counter > (self.pair_amount-1):
            self.counter = (0)
        self.Change()
    def Back(self):
        self.counter -= 1
        while self.counter in self.counter_list:
            self.counter = self.counter-1
        if self.counter < 0:
            self.counter = 0
        self.Change()
    def Jump(self):
        self.value = self.entry_box.get()
        self.value = int(self.value)
        if self.value < 1 or self.value > self.pair_amount:
            self.error_label.config(text="ERROR: value is out of bounds")
            self.error_label.place(x=self.width+ 150, y=self.height + 80)
        if self.pair_amount >= self.value >= 1:
            self.reference_value = self.value-1
            if self.reference_value in self.counter_list:
                self.error_label.config(text="ERROR: value for images has been deleted")
                self.error_label.place(x=self.width+ 150, y=self.height + 80)
            else:
                self.error_label.config(text ="SATISFIED: Jumped to Images", fg = 'green', bg = 'white')
                self.error_label.place(x=self.width+ 150, y=self.height + 80)
                self.counter = self.reference_value
                self.Change()
    def Delete(self):
        self.counter_list.append(self.counter)
        os.chdir(self.filename1)
        self.directory = os.getcwd()
        self.trash = self.directory + r'\Trash'
        try:
            os.makedirs(self.trash)
        except FileExistsError:
            print ('Error: Creating directory. ' +  self.trash)
        shutil.move(self.grabrgb,self.trash)
        shutil.move(self.grabir,self.trash)
        self.counter += 1
        if self.counter > (self.pair_amount-1):
            self.counter = 0
        while self.counter in self.counter_list:
            self.counter += 1
        self.Change()
    def Help(self):
        print('hi')
    def Change(self):
        self.grabrgb = self.filename1 + str('/')+str(self.new_rgb[self.counter])
        self.grabir = self.filename1 + str('/')+str(self.new_ir[self.counter])
        self.rgb_img1 = cv2.cvtColor(cv2.imread(self.grabrgb), cv2.COLOR_BGR2RGB)
        self.rgb_img = cv2.resize(self.rgb_img1, self.dim1, interpolation = cv2.INTER_AREA)
        self.array=tiff.imread(self.grabir)
        self.max = np.amax(self.array)
        self.min = np.amin(self.array)
        for a in range (0,512):
            for b in range (0,640):
                    self.ir_img[a][b] = ( ( 255 * ( self.array[a][b] - self.min) ) ) // (self.max-self.min)
        self.ir_img1 = cv2.resize(self.ir_img, self.dim, interpolation =cv2.INTER_AREA)
        self.rgbimage = PIL.Image.fromarray(self.rgb_img)
        self.photo = PIL.ImageTk.PhotoImage(self.rgbimage)
        self.canvas1.create_image(self.canvas1_w, self.canvas1_h ,image=self.photo)
        self.irimage = PIL.Image.fromarray(self.ir_img1)
        self.photo1 = PIL.ImageTk.PhotoImage(self.irimage)
        self.canvas2 = self.canvas1.create_image(self.canvas2_w + self.width,self.canvas2_h,image=self.photo1)
        self.rgblabel1.config(text = '{0}'.format(self.new_rgb[self.counter]) )
        self.irlabel1.config(text = '{0}'.format(self.new_ir[self.counter]))
        if (self.counter+1) >= 10:
            self.number_label.config(text = '{0} of {1}'.format(self.counter+1, self.pair_amount))
        if (self.counter+1) < 10:
            self.number_label.config(text = '0{0} of {1}'.format(self.counter+1, self.pair_amount))
    def next_key(self,event):
        self.Next()
    def back_key(self,event):
        self.Back()
class BOX_DOWNLOAD(Frame):
    def __init__(self,master):
        self.master = master
        master.title("FLIR BOX DOWNLOAD")
if __name__ == '__main__':
        root = Tk()
        my_gui = FLIR_DATA_COLLECTOR(root)
        w = 350 # width for the Tk root
        h = 200 # height for the Tk root
        ws = root.winfo_screenwidth() # width of the screen
        hs = root.winfo_screenheight() # height of the screen
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        # set the dimensions of the screen
        # and where it is placed
        root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        root.mainloop()
