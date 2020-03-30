#!/usr/bin/env python
"""
Provide one place for common Conservator API tasks for easy re-use in multiple
modules.
"""
import json
import logging
import re
from graphql_operations import try_graphql_query

def next_sublist(full_list, n):
    """
    Helper generator function for breaking up lists that are too large.

    :param full_list: A list to be broken into smaller lists.
    :type full_list: list
    :param n: The maximum size of returned smaller lists.
    :type n: int
    """
    for i in range(0, len(full_list), n):
        yield full_list[i:i+n]


class ConservatorOperations(object):
    """
    Execute graphql queries to communicate with Conservator.
    """
    VIDEO_REFERENCE_JSON_RE = re.compile(r"[^{]*({[^}]+})[^}]*$", re.MULTILINE)
    FRAME_QUERY_LIMIT = 1000

    def __init__(self, client, logger=None):
        self.client = client
        self.logger = logger
        if self.logger is None:
            self.logger = logging.getLogger("ConservatorOperations")

    def create_dataset(self, dataset_name):
        """
        Create new dataset in Conservator with the given name.

        The ID of a matching dataset returned by this method can then be used
        to add (and subsequently, retrieve) its frames.

        :param dataset_name: The name of dataset to create
        :type dataset_name: str
        :returns: String containing unique id of new dataset
        :rtype: str
        """
        dataset_id = None

        existing_dataset = self.get_dataset_by_name(dataset_name)
        if existing_dataset:
            self.logger.warning("Refusing to re-create existing dataset '%s'.",
                                dataset_name)
            return existing_dataset["id"]
        create_dataset_input = {"name": dataset_name}
        var_data = {"input": create_dataset_input}
        res = try_graphql_query(self.client, """
        mutation newDataset($input: CreateDatasetInput!) {
          createDataset(input: $input) {
            id
          }
        }
        """, json.dumps(var_data), self.logger)
        #print(json.dumps(res, indent=4))

        if 'createDataset' in res['data']:
            dataset_id = res['data']['createDataset']['id']
        return dataset_id

    def get_dataset_by_name(self, dataset_name):
        """
        Retrieve information from Conservator about the first dataset matching
        the supplied name.

        The ID of a matching dataset returned by this method can then be used
        to retrieve its frames.

        :param dataset_name: The name of a dataset to retrieve information
                             about.
        :type dataset_name: str
        :returns: A dict containing fields retrieved from Conservator.
        :rtype: dict
        """
        var_data = {"name": dataset_name}
        res = try_graphql_query(self.client, """
        query datasetByName($name: String!) {
          datasets(searchText: $name) {
            id
            name
            frameCount
          }
        }
        """, json.dumps(var_data), self.logger)
        #print(json.dumps(res, indent=4))
        dataset_info = {}
        if 'datasets' in res['data']:
            for dset_info in res['data']['datasets']:
                if dset_info['name'] == dataset_name:
                    dataset_info = dset_info
                    break
        return dataset_info

    def get_dataset_info(self, dataset_id, frame_count):
        """
        Collect information about the requested number of frames from a
        dataset, in the order in which they were added to the dataset.

        :param dataset_id: The ID of a Conservator dataset
        :type dataset_id: str
        :param frame_count: The number of frames to retrieve.
        :type frame_count: int
        :returns: A dict containing fields retrieved from Conservator.
        :rtype: dict
        """
        dataset_frames = []
        query_pages = int(frame_count / self.FRAME_QUERY_LIMIT)
        remainder = frame_count % self.FRAME_QUERY_LIMIT
        if remainder:
            query_pages += 1
        var_data = {"id": dataset_id}
        for page_n in range(query_pages):
            var_data['page'] = page_n
            var_data['limit'] = self.FRAME_QUERY_LIMIT
            res = try_graphql_query(self.client, """
            query datasetFramesById($id: ID!, $page: Int!, $limit: Int!) {
              datasetFramesOnly(id: $id, page: $page, limit: $limit) {
                datasetFrames {
                  id
                  frameId
                  frameIndex
                  video {
                    id
                  }
                }
                totalCount
              }
            }
            """, json.dumps(var_data), self.logger)
            # print(json.dumps(res, indent=4))
            if 'datasetFramesOnly' in res['data']:
                for a_dset_frame in res['data']['datasetFramesOnly']['datasetFrames']:
                    frame_info = {"frameId": a_dset_frame['frameId']}
                    frame_info['frameIndex'] = a_dset_frame['frameIndex']
                    frame_info['videoId'] = a_dset_frame['video']['id']
                    dataset_frames.append(frame_info)
        return dataset_frames

    def get_dataset_frame_info_by_id(self, frame_id):
        """
        Request information about a given dataset frame ID from Conservator.

        :param frame_id: The ID of a Conservator video frame.
        :type frame_id: str
        :returns: A dict containing fields retrieved from Conservator.
        :rtype: dict
        """
        dest_search_info = None
        var_data = {"id": frame_id}
        res = try_graphql_query(self.client, """
        query frameDetailsFromId($id: ID!) {
          datasetFrame(id: $id) {
            id
            frameId
            frameIndex
            videoId
          }
        }
        """, json.dumps(var_data), self.logger)
        #print(json.dumps(res, indent=4))
        if res and ('datasetFrame' in res['data']):
            dest_search_info = res['data']['datasetFrame']
        return dest_search_info

    def get_brief_video_info_by_id(self, video_id):
        """
        Look up a video ID found in a dataset, and return information about it.

        :param video_id: The ID of a Conservator video.
        :type video_id: str
        :returns: A dict containing fields retrieved from Conservator.
        :rtype: dict
        """
        video_info = {}
        var_data = {"id": video_id}
        res = try_graphql_query(self.client, """
        query videoInfoFromID($id: String!) {
          video(id: $id) {
            name
            description
            framesCount
            assetType
          }
        }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        if res and ('video' in res['data']):
            video_info = res['data']['video']
        return video_info

    def get_full_video_info_by_name(self, filename):
        """
        Search Conservator for a list of files matching the given filename.  If
        matching videos are found, return information about them in a list.

        :param filename: A substring to match Conservator video names against.
        :type filename: str
        :returns: A dict containing fields retrieved from Conservator.
        :rtype: dict
        """
        dest_search_info = None
        var_data = {"name": filename}
        res = try_graphql_query(self.client, """
        query videoFromName($name: String!) {
          videos(searchText: $name) {
            name
            filename
            id
            userId
            framesCount
            fileSize
            createdAt
            modifiedAt
            description
            width
            height
            state
            tags
            collections
          }
        }
        """, json.dumps(var_data), self.logger)
        #print(json.dumps(res, indent=4))
        if res and ('videos' in res['data']):
            dest_search_info = res['data']['videos']
        return dest_search_info

    def get_full_video_info_by_id(self, video_id):
        """
        Request information about a given video ID from Conservator, and return
        it in a single-value list.

        :param video_id: The ID of a Conservator video.
        :type video_id: str
        :returns: A dict containing fields retrieved from Conservator.
        :rtype: dict
        """
        dest_search_info = None
        var_data = {"id": video_id}
        res = try_graphql_query(self.client, """
        query videoDetailsFromId($id: String!) {
          video(id: $id) {
            name
            filename
            id
            userId
            framesCount
            fileSize
            createdAt
            modifiedAt
            description
            width
            height
            state
            tags
            collections
          }
        }
        """, json.dumps(var_data), self.logger)
        #print(json.dumps(res, indent=4))
        if res and ('video' in res['data']):
            dest_search_info = [res['data']['video']]
        return dest_search_info

    def extract_video_reference_json(self, description):
        """
        Given the description string from a video file, extract a JSON video
        reference, if present.

        :param description: The description associated with a Conservator
                            video.
        :type description: str
        :returns: A JSON object representing a JSON string found in the
                  description, or None if none was found.
        :rtype: dict | None
        """
        embedded_json = None
        if description:
            embedded_json_match = self.VIDEO_REFERENCE_JSON_RE.match(description)
            if embedded_json_match:
                json_str = embedded_json_match.group(1)
                try:
                    embedded_json = json.loads(json_str)
                except json.decoder.JSONDecodeError as exc:
                    self.logger.warning("Bad JSON string found: '%s'", str(exc))
        return embedded_json

    def get_frame_from_video_by_index(self, video_id, frame_index):
        """
        Given a video ID and a frame index into the video, return information
        about the specified frame.

        :param video_id: The ID of a Conservator video.
        :type video_id: str
        :param frame_index: The frame number to retrieve information about.
        :type frame_index: int
        :returns: A dict containg information about the frame.
        :rtype: dict
        """
        frame_info = {}
        var_data = {"id": video_id, "frameindex": frame_index}
        res = try_graphql_query(self.client, """
        query videoFrameInfoFromIndex($id: String!, $frameindex: Int!) {
          video(id: $id) {
            frames(frameIndex: $frameindex) {
              id
              height
              width
            }
          }
        }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        if res and ('video' in res['data']) and res['data']['video']['frames']:
            frame_info = res['data']['video']['frames'][0]
        return frame_info

    def get_project_id(self, project_name):
        """
        Given a project name, find its Conservator ID.
        """
        # Projects are toplevel collections.
        res = try_graphql_query(self.client, """
        query allProjects {
          collections(parentId: null) {
            name
            id
          }
        }
        """, logger=self.logger)
        proj_id = None
        if res and ("collections" in res['data']):
            for project_info in res['data']['collections']:
                if project_info['name'] == project_name:
                    proj_id = project_info['id']
                    break
        return proj_id

    def get_image_counts(self, collection_id):
        """
        Collect immediate counts of videos and images in a collection, as well
        as counts that include all subfolders.
        """
        var_data = {"id": collection_id}
        res = try_graphql_query(self.client, """
        query imageCountRecursive($id: ID!) {
          collection(id: $id) {
            recursiveVideoCount
            videoCount
            recursiveImageCount
            imageCount
          }
        }
        """, json.dumps(var_data), self.logger)
        #print(res)
        item_counts = None
        if res and ("collection" in res["data"]):
            item_counts = res['data']['collection']
        return item_counts

    def get_image_info_list(self, collection_id, row_count=20, page_offset=0):
        """
        Query info about all images in a collection.
        """
        var_data = {"collid": collection_id, "limit": row_count, "page": page_offset}
        res = try_graphql_query(self.client, """
        query getImagesInFolder($collid: ID!, $limit: Int!, $page: Int!) {
          images(collectionId: $collid, limit: $limit, page: $page) {
            id
            tags
            filename
            description
            assetType
          }
        }
        """, json.dumps(var_data), self.logger)
        #print(json.dumps(res, indent=4))
        images = None
        if res and ("images" in res['data']):
            images = res['data']['images']
        return images

    def get_video_info_list(self, collection_id, row_count=20, page_offset=0):
        """
        Query info about all videos in a collection.
        """
        var_data = {"collid": collection_id, "limit": row_count, "page": page_offset}
        res = try_graphql_query(self.client, """
        query getVideosInFolder($collid: ID!, $limit: Int!, $page: Int!) {
          videos(collectionId: $collid, limit: $limit, page: $page) {
            id
            tags
            filename
            description
            assetType
          }
        }
        """, json.dumps(var_data), self.logger)
        #print(json.dumps(res, indent=4))
        videos = None
        if res and ("videos" in res['data']):
            videos = res['data']['videos']
        return videos

    def get_subfolder_info_list(self, folder_id):
        """
        Find information about a collection's child folders.
        """
        var_data = {"parentid": folder_id}
        res = try_graphql_query(self.client, """
        query subFolders($parentid: ID!) {
          collections(parentId: $parentid) {
            id
            name
            path
          }
        }
        """, json.dumps(var_data), self.logger)
        collections = None
        if res and ("collections" in res['data']):
            collections = res['data']['collections']
        return collections

    def add_frames_to_dataset(self, dataset_id, frame_id_list):
        """
        Associate the given frame IDs with the given dataset ID.

        :param dataset_id: The ID of a Conservator dataset
        :type dataset_id: str
        :param frame_id_list: A list of Conservator frame IDs to be added
        :type frame_id_list: list
        :returns: tuple of dataset's name and new frame count
        :rtype: 2-tuple
        """
        name = ""
        new_framecount = 0

        for sublist in next_sublist(frame_id_list, 20):
            add_frames_input = {"datasetId": dataset_id, "frameIds": sublist}
            var_data = {"framesinput": add_frames_input}
            # addFramesToDataset
            res = try_graphql_query(self.client, """
            mutation newDatasetFrames($framesinput: AddFramesToDatasetInput!) {
              addFramesToDataset(input: $framesinput) {
                name
                frameCount
              }
            }
            """, json.dumps(var_data), self.logger)
            # print(json.dumps(res, indent=4))

            if res and ('addFramesToDataset' in res['data']):
                name = res['data']['addFramesToDataset']['name']
                new_framecount += res['data']['addFramesToDataset']['frameCount']
        return name, new_framecount

    def add_videos_to_dataset(self, dataset_id, video_id_list, frame_skip=None):
        """
        Add frames from the given video IDs to the given dataset ID.

        :param dataset_id: The ID of a Conservator dataset.
        :type dataset_id: str
        :param video_id_list: A list of video IDs to add to the dataset.
        :type video_id_list: list
        :param frame_skip: Skip this many frames between frames added to the
                           dataset.
        :type frame_skip: None | int
        :returns: A tuple of the dataset's name and new frame count.
        :rtype: 2-tuple
        """
        # addVideosToDataset
        add_videos_input = {"datasetId":dataset_id, "videoIds": video_id_list,
                            "frameSkip": frame_skip}
        var_data = {"videosinput": add_videos_input}
        res = try_graphql_query(self.client, """
        mutation newDatasetVideos($videosinput: AddVideosToDatasetInput!) {
          addVideosToDataset(input: $videosinput) {
            name
            frameCount
          }
        }
        """, json.dumps(var_data), self.logger)
        # print(json.dumps(res, indent=4))
        name = ""
        new_framecount = 0
        if res and ('addVideosToDataset' in res['data']):
            name = res['data']['addVideosToDataset']['name']
            new_framecount = res['data']['addVideosToDataset']['frameCount']
        return name, new_framecount
