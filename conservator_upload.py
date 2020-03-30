#!/usr/bin/env python

import enum
import json
import logging
import os
import re
import subprocess
import time
from collections import OrderedDict
from graphqlclient import GraphQLClient
from graphql_operations import try_graphql_query
from conservator_operations import ConservatorOperations

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

    def __init__(self, client, project_name, local_folder, logger=None, **kwargs):
        self.client = client
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
        print("INFO:Uploading "+dir_entry.path+' to collection id '+collection_id)
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
            print("WARNING:Removing imcomplete upload for file "+dir_entry.path)
            remove_ok = self.remove_video(file_info['id'])
            if not remove_ok:
                self.logger.warning("Unable to remove incomplete video '%s'",
                                    file_info['filename'])
                print("WARNING:Unable to remove incomplete video "+file_info['filename'])

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
            print("WARNING:Skipping video "+dir_entry.path+" in state "+file_state)
            self.bad_count += 1
            return
        elif file_state == "completed":
            # Video already uploaded.
            self.logger.warning("Skipping already-uploaded file '%s'", dir_entry.path)
            print("WARNING:Skipping already-uploaded file "+dir_entry.path)
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
                print("WARNING:Failed to request signed video upload URL for "+dir_entry.name)
                remove_ok = self.remove_video(file_info['id'])
                if remove_ok is False:
                    self.logger.warning("Failed to remove not-yet-uploaded file '%s'!",
                                     dir_entry.name)
                    print("WARNING:Failed to remove not-yet-uploaded file "+dir_entry.name+"!")
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
                print("WARNING:"+curl_status.args+" returned non-zero exit code ("+curl_status.returncode+"):"+curl_status.stderr)
                return
            else:
                # Check the output for server-side errors.
                if "<ERROR>" in curl_status.stdout:
                    self.logger.warning("Server reported upload error: %s", curl_status.stdout)
                    print("WARNING:Server reported upload error:"+curl_status.stdout)
                    return
                else:
                    self.logger.debug("Server reply to file upload: %s", curl_status.stdout)
                    print("DEBUG:Server reply to file upload:"+curl_status.stdout)

        # Process the video and update video status.
        self.process_video(file_info['id'])
        # Update video state.
        file_info = self.get_video_info(file_info['id'])
        if not file_info:
            file_info = self.get_image_info(file_info['id'])
        file_state = file_info['state']
        if file_state == "processing":
            self.logger.debug("Currently processing file: %s", file_info['filename'])
            print("DEBUG:Currently processing file:"+file_info['filename'])
        else:
            self.logger.debug("Video '%s' state: %s", file_info['filename'], file_state)
            print("DEBUG:Video "+file_info['filename']+" state:"+file_state)
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
        print("INFO:Uploading files in "+local_dir+" to collection id "+collection_id)
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
        print("INFO:Checking upload processing status..")
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
        print("Waiting for processing to complete for all files..", flush=True)
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
        print("\tSuccessfully uploaded: {}".format(done_count), flush=True)
        print("\tTimed out:             {}".format(timeout_count), flush=True)
        print("\tFailed:                {}".format(bad_count + self.bad_count), flush=True)
        print("\tDuplicates skipped:    {}".format(self.skip_count))


if __name__ == "__main__":
    import argparse

    CLIENT = GraphQLClient('https://www.flirconservator.com/graphql')
    #client.inject_token('Bearer <API_KEY_HERE>')
    CLIENT.inject_token('uuCsYJK7UwFTo8_CPc97VQ')

    PARSER = argparse.ArgumentParser(description="Upload videos to Conservator")
    PARSER.add_argument(
        "--recursive", action="store_true",
        help="Upload files from subfolders, preserving folder structure on Conservator")
    PARSER.add_argument(
        "--dry_run", action='store_true',
        help="Skip actually uploading files")
    PARSER.add_argument(
        "--resume", action='store_true',
        help="Skip files that already exist in Conservator")
    PARSER.add_argument(
        "project_name", help="The Conservator project into which files will be uploaded")
    PARSER.add_argument(
        "local_folder", help="Directory containing files to be uploaded")
    ARGS = PARSER.parse_args()

    ARG_DICT = vars(ARGS)

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    LOGGER = logging.getLogger("conservator_upload")
    LOGGER.setLevel(logging.INFO)

    UPLOADER = ConservatorUploader(CLIENT, logger=LOGGER, **ARG_DICT)
    UPLOADER.upload()
