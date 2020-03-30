
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
import os
from PIL import Image
from PIL import ImageTk
import numpy as np
from tkinter import filedialog
import math
import gc
from tkinter import messagebox
import tifffile as tiff
import shutil
import piexif
import subprocess
import enum
import logging
import re
import json
import time
import queue
import threading
from collections import OrderedDict
from collections import OrderedDict
from graphqlclient import GraphQLClient
from graphql_operations import try_graphql_query
from conservator_operations import ConservatorOperations
global label1
global counter
global number_label
def log(message, thread_message_queue):
    if thread_message_queue is None:
        print(message, end='', flush=True)
    else:
        thread_message_queue.put({'log': message})
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
        def destroyer():
            master.quit()
            master.destroy()
            sys.exit()
        master.protocol("WM_DELETE_WINDOW",destroyer)
    def box_download_function(self):
        root.withdraw()
        window = Toplevel()
        w = 850 # width for the Tk root
        h = 175 # height for the Tk root
        ws = window.winfo_screenwidth() # width of the screen
        hs = window.winfo_screenheight() # height of the screen
        xx = (ws/2) - (w/2)
        yy = (hs/2) - (h/2)
        window.geometry('%dx%d+%d+%d' % (w, h,xx,yy))
        frame_cropper = BOX_DOWNLOAD(window)
        window.mainloop()
    def image_viewer_function(self):
        root.withdraw()
        window1 = Toplevel()
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
        window = Toplevel()
        frame_cropper = FRAME_CROPPER(window)
        window.mainloop()
class FRAME_CROPPER(Frame):
    def __init__(self,master):
        #master.iconbitmap('flam.ico')
        master.title("FLIR FRAME CROPPER")
class IMAGE_VIEWER(Frame):
    def __init__(self,master):
        master.iconbitmap('flam.ico')
        master.title("FLIR IMAGE VIEWER")
        master.geometry("850x175")
        master.iconbitmap("flam.ico")
        self.button = Button(master, text = "View Images in Directory", bg = 'navy blue', fg = 'white',
        command = self.open_images).grid(row = 9, column = 1)
        self.upload_button =  Button(master, text = "Upload Images in Directory", bg = 'navy blue', fg = 'white',
        command = self.upload_images).grid(row = 9, column = 2)
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
        def destroyer():
            master.quit()
            master.destroy()
            sys.exit()
        master.protocol("WM_DELETE_WINDOW",destroyer)
    def thirteen(self):
        global scale_percent
        scale_percent = 88
    def nineteen(self):
        global scale_percent
        scale_percent = 200
    def twentyfive(self):
        global scale_percent
        scale_percent= 225
    def open_images(self):
        if self.filename1 == "NULL":
            self.label1.config(text = 'No Directory Selected',fg='red')
        else:
            gc.disable()
            window2 = Toplevel()
            open_images = OPEN_IMAGES(window2,scale_percent,self.filename1,self.label1)
    def upload_images(self):
        if self.filename1 == "NULL":
            self.label1.config(text = 'No Directory Selected',fg='red')
        else:
            gc.disable()
            window2 = Toplevel()
            open_images = UPLOAD_IMAGES(window2,self.filename1,self.label1)
    def select_rgb(self):
        self.filename1 = filedialog.askdirectory()
        self.label1.config(text = self.filename1,fg='green')
class UPLOAD_IMAGES(Frame):
        def __init__(self,master,filename1,label1):
            self.filename1 = filename1
            self.master = master
            master.title("CONSERVATOR UPLOAD")
            master.iconbitmap('flam.ico')
            self.ws = master.winfo_screenwidth() # width of the screen
            self.hs = master.winfo_screenheight() # height of the screen
            self.wid = (self.ws/2) - (850/2)
            self.hei = (self.hs/2) - (350/2)
            master.geometry('%dx%d+%d+%d' % (850, 350,self.wid,self.hei))
            self.frame2 = Frame(master)
            self.frame2.grid(column=1,row=1,ipadx = 185)
            self.frame2['borderwidth'] = 2
            self.frame2['relief'] = 'sunken'
            self.label = Label(self.frame2, text = 'Project Name: ',fg='black')
            self.label.pack(side=LEFT)
            self.entry_box1 = Entry(self.frame2)
            self.entry_box1.pack(side=LEFT)
            self.recvar = IntVar()
            self.exvar = IntVar()
            self.checkbutton = Checkbutton(self.frame2, text = "Keep File Structure",variable = self.recvar, onvalue=1,offvalue=0,command = self.recursive_check)
            self.checkbutton.pack(side=LEFT)
            self.checkbutton2 = Checkbutton(self.frame2, text = "Skip Existing Files",variable = self.exvar, onvalue=1,offvalue=0,command = self.exist_check)
            self.checkbutton2.pack(side=LEFT)
            self.scrollbar = Scrollbar(master)
            self.scrollbar.grid(row=2, column=2, sticky=(N,S,E))
            self.log_window = Text(master, state='disabled', width=100, height=18,yscrollcommand=self.scrollbar.set)
            self.log_window.grid(row=2,column=1)
            self.scrollbar.config(command=self.log_window.yview)
            self.upbutton = Button(master, text = "Upload", bg = 'navy blue', fg = 'white',
            command = self.upload_button_press).grid(row=3,column=1)
            self.rec = ""
            self.ex = ""
            def destroyer():
                master.quit()
                master.destroy()
            master.protocol("WM_DELETE_WINDOW",destroyer)
        def upload_button_press(self):
            project_name = self.entry_box1.get()
            ARG_DICT = dict()
            #self.update("UPLOADING DIRECTORY ")
            if self.rec == "":
                #self.update("NOT KEEPING FILE STRUCTURE...")
                ARG_DICT['recursive'] = False
            else:
                #self.update("KEEPING FILE STRUCTURE...")
                ARG_DICT['recursive'] = True
            if self.ex == "":
                #self.update("NOT SKIPPING FILES ...")
                ARG_DICT['resume'] = False
            else:
                #self.update("SKIPPING FILES ALREADY IN CONSERVATOR...")
                ARG_DICT['resume'] = True
            CLIENT = GraphQLClient('https://www.flirconservator.com/graphql')
            #client.inject_token('Bearer <API_KEY_HERE>')
            CLIENT.inject_token('uuCsYJK7UwFTo8_CPc97VQ')
            self.thread_message_queue = queue.Queue(0)
            logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
            LOGGER = logging.getLogger("conservator_upload")
            LOGGER.setLevel(logging.INFO)
            UPLOADER = ConservatorUploader(CLIENT, project_name,self.filename1,LOGGER,self.thread_message_queue, **ARG_DICT)
            self.upload_thread = threading.Thread(target=UPLOADER.upload)
            self.upload_thread.start()
            self.master.after(100, self.monitor_message_queue)
        def recursive_check(self):
            if self.recvar.get() ==1:
                self.rec = "--recursive"
            else:
                self.rec = ""
        def exist_check(self):
            if self.exvar.get() ==1:
                self.ex= "--resume"
            else:
                self.ex = ""
        def update(self,string):
            self.log_window['state']='normal'
            self.log_window.insert(END,string+'\n')
            self.log_window['state'] = 'disabled'
            self.log_window.see('end')
        def monitor_message_queue(self):
            while not self.thread_message_queue.empty():
                try:
                    queue_dict = self.thread_message_queue.get(block=False)
                    if 'log' in queue_dict.keys():
                        self.update(queue_dict['log'])
                except queue.Empty:
                    break
            self.master.after(100, self.monitor_message_queue)
VIDEO_EXTENSION_RE_LIST = (re.compile(".zip$", flags=re.I), re.compile(".mp4$", flags=re.I),
                           re.compile(".avi$", flags=re.I))


class ConservatorUploader(ConservatorOperations):
    def get_collection_id(self, project_name, parent_id=None):
        # projects are toplevel collections
        var_data = {"parentid": parent_id}
        res = try_graphql_query(self.client, """
        query allCollections($parentid: ID) {
          collections(parentId: $parentid) {
            name
            id
            parentId
          }
        }
        """, json.dumps(var_data), self.logger)
        proj_id = None
        for project_info in res['data']['collections']:
            if project_info['name'] == project_name:
                proj_id = project_info['id']
                break
        return proj_id

    def get_image_info(self, image_id):
        """
        Retrieve information about a known image ID.
        """
        var_data = {"imageid": image_id}
        res = try_graphql_query(self.client, """
          query getImageInfo($imageid: String!) {
            image(id: $imageid) {
              id
              filename
              createdAt
              state
            }
          }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        im_info = {}
        if "image" in res['data']:
            im_info = res['data']['image']
        return im_info

    def image_exists_in_folder(self, collection_id, filename):
        """
        Return information about the first image found in a collection with the
        supplied file name.
        """
        var_data = {"collectionid": collection_id, "filename": filename}
        res = try_graphql_query(self.client, """
        query imageExistsInCollection($collectionid: ID!, $filename: String!) {
          images(collectionId: $collectionid, searchText: $filename) {
            id
            filename
            createdAt
            state
          }
        }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        image_info = None
        if "images" in res['data']:
            for im_info in res['data']['images']:
                if im_info['filename'] == filename:
                    image_info = im_info
                    break
        return image_info

    def get_video_info(self, video_id):
        """
        Retrieve information about a known video ID.
        """
        var_data = {"videoid": video_id}
        res = try_graphql_query(self.client, """
          query getVideoInfo($videoid: String!) {
            video(id: $videoid) {
              id
              filename
              createdAt
              state
            }
          }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        vid_info = {}
        if "video" in res['data']:
            vid_info = res['data']['video']
        return vid_info

    def video_exists_in_folder(self, collection_id, filename):
        """
        Return information about the first video found in a collection with the
        supplied file name.
        """
        var_data = {"collectionid": collection_id, "filename": filename}
        res = try_graphql_query(self.client, """
        query videoExistsInCollection($collectionid: ID!, $filename: String!) {
          videos(collectionId: $collectionid, searchText: $filename) {
            id
            filename
            createdAt
            state
          }
        }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        vid_info = None
        if "videos" in res['data']:
            for a_vid_info in res['data']['videos']:
                if a_vid_info['filename'] == filename:
                    vid_info = a_vid_info
                    break
        return vid_info

    def create_new_collection(self, collection_name, parent_id):
        """
        Create a child collection in Conservator with the given parent_id.
        """
        collection_id = None
        collection_info = {"name": collection_name, "parentId": parent_id}
        var_data = {"collectioninfo": collection_info}
        res_str = client.execute("""
        mutation createChildCollection($collectioninfo: CreateCollectionInput!) {
          createCollection(input: $collectioninfo) {
            id
          }
        }
        """, json.dumps(var_data))
        if "createCollection" in res['data']:
            collection_id = res['data']['createCollection']['id']
        # print(json.dumps(res, indent=4))
        return collection_id

    def remove_video(self, video_id):
        """
        Remove an existing video from conservator.
        """
        var_data = {"videoid": video_id}
        res = try_graphql_query(self.client, """
          mutation removeBrokenVideo($videoid: String!) {
            removeVideo(id: $videoid)
          }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        remove_ok = False
        if "removeVideo" in res['data']:
            remove_ok = res['data']['removeVideo']
        return remove_ok

    def create_new_video(self, collection_id, filename):
        """
        Create a new video in Conservator as part of the given collection_id.
        """
        new_file_info = None
        var_data = {"collectionid": collection_id, "filename": filename}
        res = try_graphql_query(self.client, """
        mutation createVideoInCollection($filename: String!, $collectionid: ID!) {
          createVideo(filename: $filename, collectionId: $collectionid) {
            id
            filename
            createdAt
            state
          }
        }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        if "createVideo" in res['data']:
            new_file_info = res['data']['createVideo']
        return new_file_info

    def generate_signed_upload_url(self, video_id):
        """
        Retrieve an upload URL for a newly-created video.
        """
        var_data = {"videoid": video_id, "contenttype": ""}
        res = try_graphql_query(self.client, """
        mutation generateSignedVideoUploadUrl($videoid: String!, $contenttype: String!) {
          generateSignedVideoUploadUrl(videoId: $videoid, contentType: $contenttype) {
            signedUrl
          }
        }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        url = ""
        data = {}
        if res['data'] is not None and "generateSignedVideoUploadUrl" in res['data']:
            # This can fail if a URL was already requested before but no file
            # was uploaded to it.
            full_url = res['data']['generateSignedVideoUploadUrl']['signedUrl']
            url, data_str = full_url.split('?')
            data_fields = data_str.split('&')
            data = OrderedDict([dat.split('=') for dat in data_fields])
        return url, data, full_url

    def log(self, message):
            log(message, self.thread_message_queue)

    def process_video(self, video_id):
        """
        Process an uploaded video.
        """
        var_data = {"videoid": video_id, "shouldnotify": False}
        res = try_graphql_query(self.client, """
        mutation processAutoUploadedVideo($videoid: String!, $shouldnotify: Boolean) {
          processVideo(id: $videoid, shouldNotify: $shouldnotify) {
            id
          }
        }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        vidid = None
        if "data" in res and res['data'] and "processVideo" in res['data']:
            vidid = res['data']['processVideo']['id']
        return vidid

    def __init__(self, client, project_name, local_folder, logger, thread_message_queue, **kwargs):
        self.client = client
        self.thread_message_queue = thread_message_queue
        self.project_name = project_name
        self.local_folder = local_folder
        self.collection_id = None
        if logger is None:
            self.logger = logging.getLogger("ConservatorUploader")
        else:
            self.logger = logger
        self.recursive = False
        self.dry_run = False
        self.resume = False
        if "recursive" in kwargs:
            self.recursive = kwargs['recursive']
        if "dry_run" in kwargs:
            self.dry_run = kwargs['dry_run']
        if "resume" in kwargs:
            self.dry_run = kwargs['resume']
        self.uploads_in_progress = []
        self.bad_count = 0
        self.skip_count = 0

    def upload_file(self, dir_entry, collection_id):
        """
        Upload a file from a given directory entry into an existing
        collection_id.
        """
        self.logger.info("Uploading '%s' to collection id '%s'",
                         dir_entry.path, collection_id)
        self.log("INFO:Uploading "+dir_entry.path+' to collection id '+collection_id)
        # Check whether the file already exists, and if so, get its current
        # state.
        file_type = "image"
        for ext_re in VIDEO_EXTENSION_RE_LIST:
            minfo = ext_re.search(dir_entry.name)
            if minfo:
                file_type = "video"
                break
        if file_type == "video":
            file_info = self.video_exists_in_folder(collection_id, dir_entry.name)
        else:
            file_info = self.image_exists_in_folder(collection_id, dir_entry.name)
        file_state = None
        if file_info:
            file_state = file_info['state']
        if file_state is not None and file_state == "uploading":
            # The video upload was not completed, and needs to be replaced.
            self.logger.warning("Removing imcomplete upload for file '%s'", dir_entry.path)
            self.log("WARNING:Removing imcomplete upload for file "+dir_entry.path)
            remove_ok = self.remove_video(file_info['id'])
            if not remove_ok:
                self.logger.warning("Unable to remove incomplete video '%s'",
                                    file_info['filename'])
                self.log("WARNING:Unable to remove incomplete video "+file_info['filename'])

                return
            file_state = None
        if file_state is None:
            # Create the video on Conservator.
            file_info = self.create_new_video(collection_id, dir_entry.name)
            if file_info is not None:
                file_state = file_info['state']
            else:
                raise RuntimeError("Failed to create video '{}' in collection '{}'!".format(
                    dir_entry.name, collection_id))
        elif file_state in ("failed", "retrying"):
            # If "failed" or "retrying", give up.
            self.logger.warning("Skipping video '%s' in state '%s",
                             dir_entry.path, file_state)
            self.log("WARNING:Skipping video "+dir_entry.path+" in state "+file_state)
            self.bad_count += 1
            return
        elif file_state == "completed":
            # Video already uploaded.
            self.logger.warning("Skipping already-uploaded file '%s'", dir_entry.path)
            self.log("WARNING:Skipping already-uploaded file "+dir_entry.path)
            self.skip_count += 1
            return

        if file_state == "uploading":
            # Video was created and needs to be uploaded.
            # Request a signed upload URL from conservator.
            url = ""
            # params = {}
            url, _, full_url = self.generate_signed_upload_url(file_info['id'])
            if not url:
                self.logger.warning("Failed to request signed video upload URL for '%s'",
                                    dir_entry.name)
                self.log("WARNING:Failed to request signed video upload URL for "+dir_entry.name)
                remove_ok = self.remove_video(file_info['id'])
                if remove_ok is False:
                    self.logger.warning("Failed to remove not-yet-uploaded file '%s'!",
                                     dir_entry.name)
                    self.log("WARNING:Failed to remove not-yet-uploaded file "+dir_entry.name+"!")
                return
            # NOTE: Can't use requests to upload large files, see
            #       'https://gitlab.com/gitlab-com/support-forum/issues/4723'
            # Using curl in a subprocess, instead.
            curl_status = subprocess.run(["curl", "--upload-file", dir_entry.path,
                                          full_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          universal_newlines=True)
            if curl_status.returncode != 0:
                self.logger.warning("%s returned non-zero exit code (%d): %s", curl_status.args,
                                 curl_status.returncode, curl_status.stderr)
                self.log("WARNING:"+curl_status.args+" returned non-zero exit code ("+curl_status.returncode+"):"+curl_status.stderr)
                return
            else:
                # Check the output for server-side errors.
                if "<ERROR>" in curl_status.stdout:
                    self.logger.warning("Server reported upload error: %s", curl_status.stdout)
                    self.log("WARNING:Server reported upload error:"+curl_status.stdout)
                    return
                else:
                    self.logger.debug("Server reply to file upload: %s", curl_status.stdout)
                    self.log("DEBUG:Server reply to file upload:"+curl_status.stdout)

        # Process the video and update video status.
        self.process_video(file_info['id'])
        # Update video state.
        file_info = self.get_video_info(file_info['id'])
        if not file_info:
            file_info = self.get_image_info(file_info['id'])
        file_state = file_info['state']
        if file_state == "processing":
            self.logger.debug("Currently processing file: %s", file_info['filename'])
            self.log("DEBUG:Currently processing file:"+file_info['filename'])
        else:
            self.logger.debug("Video '%s' state: %s", file_info['filename'], file_state)
            self.log("DEBUG:Video "+file_info['filename']+" state:"+file_state)
        self.uploads_in_progress.append({"filename": dir_entry.path,
                                         "id": file_info['id'],
                                         "type": file_type,
                                         "start_time": time.time()})

    def upload_files_in_folder(self, local_dir, collection_id):
        """
        Upload files inside a local directory into an existing collection_id.

        May operate recursively.
        """
        subdir_list = []
        self.logger.info("Uploading files in '%s' to collection id '%s'",
                         local_dir, collection_id)
        self.log("INFO:Uploading files in "+local_dir+" to collection id "+collection_id)
        for folder_item in os.scandir(local_dir):
            if folder_item.is_dir() and self.recursive:
                # Upload all files in this folder first.  Record subfolders to
                #  descend into afterward.
                if os.listdir(folder_item.path):
                    # Only add subdirectories that contain files.
                    subdir_list.append(folder_item)
            elif folder_item.is_file():
                # Note: passing the object returned by scandir().
                self.upload_file(folder_item, collection_id)
        # Now handle recursion into subfolders.
        if self.recursive:
            for a_subdir_entry in subdir_list:
                # Create the child collection if necessary.
                child_collection_id = self.get_collection_id(
                    a_subdir_entry.name, collection_id)
                if not child_collection_id:
                    # Create a new collection, if no child collection was found
                    # with the given name.
                    child_collection_id = self.create_new_collection(
                        a_subdir_entry.name, collection_id)
                self.upload_files_in_folder(a_subdir_entry.path, child_collection_id)

    def check_for_processing_complete(self, max_timeout=60):
        self.logger.info("Checking upload processing status..")
        self.log("INFO:Checking upload processing status..")
        empty_list = True
        for idx, a_file_info in enumerate(self.uploads_in_progress):
            if "status" in a_file_info:
                continue
            empty_list = False
            start_time = a_file_info['start_time']
            file_info = self.get_video_info(a_file_info['id'])
            if not file_info:
                file_info = self.get_image_info(a_file_info['id'])
            file_state = file_info['state']
            if file_state == "processing":
                now = time.time()
                if now - start_time > max_timeout:
                    self.uploads_in_progress[idx]['status'] = "timed out"
            elif file_state == "completed":
                self.uploads_in_progress[idx]['status'] = "complete"
            else:
                # Something went wrong.
                self.uploads_in_progress[idx]['status'] = "failed"
        return empty_list

    def upload(self):
        """
        Upload all files in local_folder into the project.
        """
        self.collection_id = self.get_collection_id(self.project_name)
        if self.collection_id is None:
            raise RuntimeError("No project named '{}' found in conservator".format(project_name))
        self.upload_files_in_folder(self.local_folder, self.collection_id)
        # Wait for completion status for all videos.
        self.log("Waiting for processing to complete for all files..")
        done = False
        while done is False:
            done = self.check_for_processing_complete()
            if done is False:
                time.sleep(1)
        # Report status.
        done_count = 0
        timeout_count = 0
        bad_count = 0
        for a_vid_info in self.uploads_in_progress:
            if a_vid_info['status'] == "complete":
                done_count += 1
            elif a_vid_info['status'] == "timed out":
                timeout_count += 1
            elif a_vid_info['status'] == "failed":
                bad_count += 1
        print("Finished uploading files from {}.".format(self.local_folder), flush=True)
        self.log("Finished uploading files from {}.".format(self.local_folder))
        print("\tSuccessfully uploaded: {}".format(done_count), flush=True)
        self.log("\tSuccessfully uploaded: {}".format(done_count))
        print("\tTimed out:             {}".format(timeout_count), flush=True)
        self.log("\tTimed out:             {}".format(timeout_count))
        print("\tFailed:                {}".format(bad_count + self.bad_count), flush=True)
        self.log("\tFailed:                {}".format(bad_count + self.bad_count))
        print("\tDuplicates skipped:    {}".format(self.skip_count))
        self.log("\tDuplicates skipped:    {}".format(self.skip_count))

class OPEN_IMAGES(Frame):
    def __init__(self,master,scale_percent,filename1,label1):
        self.master = master
        master.bind("<Right>",self.next_key)
        master.bind("<Left>",self.back_key)
        master.bind("<Up>",self.up_key)
        master.bind("<Down>",self.down_key)
        self.counter = 0
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
            self.rgb_img1 = cv2.cvtColor(cv2.imread(self.grabrgb), cv2.COLOR_BGR2RGB)
            rgb_scale_percent = 15
            self.rgb_width = int(self.rgb_img1.shape[1] * rgb_scale_percent / 100)
            self.rgb_height = int(self.rgb_img1.shape[0] *rgb_scale_percent / 100)
            self.dim1 = (self.rgb_width, self.rgb_height)
            self.rgb_img = cv2.resize(self.rgb_img1, self.dim1, interpolation = cv2.INTER_AREA)
            #IR remask
            self.ir_img = np.zeros((512, 640), dtype = "uint8")
            self.array=tiff.imread(self.grabir)
            self.max = np.amax(self.array)
            self.min = np.amin(self.array)
            self.average = np.average(self.array)
            print(self.min)
            print(self.max)
            print(self.average)
            self.var = self.max-self.min
            for a in range (0,512):
                for b in range (0,640):
                    self.ir_img[a][b] = ( ( 255 * ( self.array[a][b] - self.min) ) ) // (self.max-self.min)
            self.ir_resized_width = int(self.ir_img.shape[1] * scale_percent // 100)
            self.ir_resized_height = int(self.ir_img.shape[0] * scale_percent // 100)
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
            self.AGC_LINEAR_button = Button(self.canvas1, text="Linear", command = self.Change, bg= 'navy', fg='white')
            self.AGC_LINEAR_button.place(x=112,y=0)
            self.AGC_NORMAL_button =  Button(self.canvas1, text="Normal", command = self.AGC_change, bg= 'navy', fg='white')
            self.AGC_NORMAL_button.place(x=155,y=0)
            self.entry_box = Entry(self.canvas1)
            self.entry_box.place(x=self.width+5, y=self.height + 80)
            self.tag_entry = Entry(self.canvas1)
            self.enter_class_label = Label(self.canvas1, text = "Enter COCO Class Here:",  fg = 'white', bg= 'navy')
            self.enter_class_label.place(x = self.width-450,y = self.height+80)
            self.tag_entry.place(x=self.width-300,y=self.height+80)
            self.tag_button = Button(self.canvas1, text = "Tag", command = self.Tag, bg = 'white', fg = 'navy')
            self.tag_button.place(x=self.width-257,y=self.height+110)
            self.entry_label = Label(self.canvas1, text="Jump to Image:", fg = 'white', bg= 'navy')
            self.entry_label.place(x=self.width-100, y=self.height + 80)
            self.entry_button = Button(self.canvas1, text="Jump", command = self.Jump, bg= 'white', fg='navy')
            self.entry_button.place(x=self.width+48, y=self.height + 110)
            self.rgbimage = Image.fromarray(self.rgb_img)
            self.photo = ImageTk.PhotoImage(self.rgbimage)
            self.error_label = Label(self.canvas1, text = "Dummy",  fg = 'white', bg= 'navy')
            self.canvas1_w = self.width/2
            self.canvas1_h = self.height/2 + 25
            self.canvas2_w =  self.width1/2
            self.canvas2_h = self.height1/2 +25
            self.irimage = Image.fromarray(self.ir_img1)
            self.photo1 = ImageTk.PhotoImage(self.irimage)
            self.canvas2 = self.canvas1.create_image(self.canvas2_w + self.width,self.canvas2_h,image=self.photo1)
            self.canvas1.create_image(self.canvas1_w, self.canvas1_h ,image=self.photo)
            self.coco_class_list = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "tennis racket", "bottle", "wine glass", "cup", "fork","knife","spoon", "bowl", "apple","banana", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed","dining table", "toilet", "tv", "laptop","mouse","remote","keyboard","cell phone","microwave","oven","toaster","sink","refrigerator","book","clock","vase","scissors","teddy bear","hair drier","toothbrush"]
            self.tag_error = Label(self.canvas1,text ="DUMMY",fg = 'red',bg='white')
    def Tag(self):
        os.chdir(self.filename1)
        self.tags = self.tag_entry.get()
        if self.tags not in self.coco_class_list:
            answer = messagebox.showerror(title = "Error", message ="Tag is not class in COCO.")
        else:
            self.basergb = self.new_rgb[self.counter]
            self.baseir = self.new_ir[self.counter]
            print(self.basergb)
            im = Image.open(self.basergb)
            exif_dict = piexif.load(im.info['exif'])
            print(exif_dict)
            try:
                current = exif_dict['0th'][11]
                current = (current.decode('utf-8',errors='replace'))
                exist = True
            except:
                exist = False
            if exist==True:
                answer = messagebox.askyesno(title = "Warning",message="Overwrite Current Tag: "+current)
                if answer == False:
                    return
                else:
                    exif_dict['0th'][11] = self.tags
            exif_bytes = piexif.dump(exif_dict)
            im.save(self.basergb,"JPEG",exif=exif_bytes)
    def Next(self):
        self.counter += 1
        while self.counter in self.counter_list:
            self.counter += 1
        if self.counter > (self.pair_amount-1):
            self.counter = 0
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
        answer = messagebox.showinfo(title = "Help", message ="RIGHT and LEFT arrow keys navigate through the images. Use the Tag Entry Box to tag images with COCO Classes")
    def Change(self):
        self.grabrgb = self.filename1 + str('/')+str(self.new_rgb[self.counter])
        self.grabir = self.filename1 + str('/')+str(self.new_ir[self.counter])
        self.rgb_img1 = cv2.cvtColor(cv2.imread(self.grabrgb), cv2.COLOR_BGR2RGB)
        self.rgb_img = cv2.resize(self.rgb_img1, self.dim1, interpolation = cv2.INTER_AREA)
        self.array=tiff.imread(self.grabir)
        self.max = np.amax(self.array)
        self.min = np.amin(self.array)
        self.var = self.max-self.min
        self.average = np.average(self.array)
        print(self.min)
        print(self.max)
        print(self.average)
        for a in range (0,512):
            for b in range (0,640):
                    self.ir_img[a][b] = ( ( 255 * ( self.array[a][b] - self.min) ) ) // (self.var)
        self.ir_img1 = cv2.resize(self.ir_img, self.dim, interpolation =cv2.INTER_AREA)
        self.rgbimage = Image.fromarray(self.rgb_img)
        self.photo = ImageTk.PhotoImage(self.rgbimage)
        self.canvas1.create_image(self.canvas1_w, self.canvas1_h ,image=self.photo)
        self.irimage = Image.fromarray(self.ir_img1)
        self.photo1 = ImageTk.PhotoImage(self.irimage)
        self.canvas2 = self.canvas1.create_image(self.canvas2_w + self.width,self.canvas2_h,image=self.photo1)
        self.rgblabel1.config(text = '{0}'.format(self.new_rgb[self.counter]) )
        self.irlabel1.config(text = '{0}'.format(self.new_ir[self.counter]))
        if (self.counter+1) >= 10:
            self.number_label.config(text = '{0} of {1}'.format(self.counter+1, self.pair_amount))
        if (self.counter+1) < 10:
            self.number_label.config(text = '0{0} of {1}'.format(self.counter+1, self.pair_amount))
    def AGC_change(self):
        for a in range (0,512):
            for b in range (0,640):
                    if self.array[a][b] <= self.average:
                        self.ir_img[a][b] = 128-((128 * abs(self.average-self.array[a][b])// self.average))
                    elif self.array[a][b] > self.average:
                        self.ir_img[a][b] = 128+((128 * abs(self.average-self.array[a][b])// self.average))
        self.ir_img1 = cv2.resize(self.ir_img, self.dim, interpolation =cv2.INTER_AREA)
        self.rgbimage = Image.fromarray(self.rgb_img)
        self.photo = ImageTk.PhotoImage(self.rgbimage)
        self.canvas1.create_image(self.canvas1_w, self.canvas1_h ,image=self.photo)
        self.irimage = Image.fromarray(self.ir_img1)
        self.photo1 = ImageTk.PhotoImage(self.irimage)
        self.canvas2 = self.canvas1.create_image(self.canvas2_w + self.width,self.canvas2_h,image=self.photo1)
    def AGC_change2(self):
        for a in range (0,512):
            for b in range (0,640):
                    if self.array[a][b] <= self.average:
                        if self.array[a][b] == self.min:
                            self.ir_img[a][b] = 0
                        else:
                            self.ir_img[a][b] = 128-((128 * abs(self.average-self.array[a][b])// self.average))
                    elif self.array[a][b] > self.average:
                        if self.array[a][b] == self.max:
                            self.ir_img[a][b] = 255
                        else:
                            self.ir_img[a][b] = 128+((128 * abs(self.average-self.array[a][b])// self.average))
        self.ir_img1 = cv2.resize(self.ir_img, self.dim, interpolation =cv2.INTER_AREA)
        self.rgbimage = Image.fromarray(self.rgb_img)
        self.photo = ImageTk.PhotoImage(self.rgbimage)
        self.canvas1.create_image(self.canvas1_w, self.canvas1_h ,image=self.photo)
        self.irimage = Image.fromarray(self.ir_img1)
        self.photo1 = ImageTk.PhotoImage(self.irimage)
        self.canvas2 = self.canvas1.create_image(self.canvas2_w + self.width,self.canvas2_h,image=self.photo1)
    def up_key(self,event):
        self.AGC_change()
    def down_key(self,event):
        self.AGC_change2()
    def next_key(self,event):
        self.Next()
    def back_key(self,event):
        self.Back()
class BOX_DOWNLOAD(Frame):
    def __init__(self,master):
        self.master = master
        master.title("FLIR BOX DOWNLOAD")
        master.iconbitmap('flam.ico')
        master.geometry("850x175")
        self.download_button

if __name__ == '__main__':
        root = Tk()
        my_gui = FLIR_DATA_COLLECTOR(root)
        w = 350 # width for the Tk root
        h = 200 # height for the Tk root
        ws = root.winfo_screenwidth() # width of the screen
        hs = root.winfo_screenheight() # height of the screen
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        def destroyer():
            root.quit()
            root.destroy()
            sys.exit()
        root.protocol("WM_DELETE_WINDOW",destroyer)
        root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        root.mainloop()
