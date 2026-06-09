import argparse
import csv
import zipfile
import numpy as np

import zipfile
import yaml
import math
import data as tibava_data
import os
import requests
import uuid
from xml.dom import minidom

movie_links = [
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/american_history_x.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/benjamin.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/big_fish_fix.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/forrest_fix.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/gattaca_1.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/gattaca_2_fix.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/godfather_fix.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/good_bad_ugly.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/hunger_games_1.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/hunger_games_2_fix.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/invictus_fix.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/lotr.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/pulp_fiction_fix.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/shawshank_1.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/shawshank_2.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/shining_fix.zip",
    "https://github.com/TIBHannover/DHd2026/raw/refs/heads/main/resources_fix/the_help_1.zip",
]

gt_links = [
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/americanx.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/benjamin.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/bigfish.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/forrest.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/gattaca1.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/gattaca2.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/godfather.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/goodbadugly.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/hungergames1.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/hunger_games2.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/invictus.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/lotr.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/pulpficiton.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/shawshank_escape1.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/shawshank_escape2.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/shining.xml",
    "/home/springsteinm/projects/tibava/scsmi26/FilmAnnotation/thehelp1.xml",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Process zip file path.")
    # parser.add_argument("zip_file", type=str, help="Path to the zip file")
    return parser.parse_args()


def extract_shots(dom):
    items = dom.getElementsByTagName("root")

    result_shots = {}
    for item in items:
        root_shots = item.getElementsByTagName("shots")

        for root_shot in root_shots:
            shots = root_shot.getElementsByTagName("shot")

            for shot in shots:
                # print(shot)
                start = int(shot.getAttribute("startFrame"))
                end = int(shot.getAttribute("endFrame"))
                shot_id = int(shot.getAttribute("id"))
                frames = []
                for x in shot.getElementsByTagName("frame"):
                    frames.append(int(x.getAttribute("id")))

                result_shots[shot_id] = {
                    "shot_id": shot_id,
                    "start": start,
                    "end": end,
                    "frames": frames,
                }

    return result_shots


def extract_scenes(dom):
    items = dom.getElementsByTagName("root")

    result_scenes = {}
    for item in items:
        root_scenes = item.getElementsByTagName("scenes")

        for root_scene in root_scenes:
            scenes = root_scene.getElementsByTagName("Scene")

            for scene in scenes:
                scene_id = int(scene.getAttribute("id"))
                shots = []
                for x in scene.getElementsByTagName("shot"):
                    shots.append(int(x.getAttribute("refId")))

                result_scenes[scene_id] = {"scene_id": scene_id, "shots": shots}
    return result_scenes


def extract_video_meta(dom):
    items = dom.getElementsByTagName("header")

    for item in items:
        root_videos = item.getElementsByTagName("video")
        for root_video in root_videos:
            return {"fps": float(root_video.getAttribute("fps"))}

    return None


def extract_actors(dom):
    items = dom.getElementsByTagName("header")

    result_actors = {}
    for item in items:
        actors = item.getElementsByTagName("actor")
        for actor in actors:
            actor_id = int(actor.getAttribute("id"))
            result_actors[actor_id] = {
                "actor_id": actor_id,
                "name": actor.getAttribute("name"),
                "type": actor.getAttribute("type"),
            }

    return result_actors


def extract_frames(dom):
    result_frames = {}  #

    root_frames = dom.getElementsByTagName("frames")

    for root_frame in root_frames:
        frames = root_frame.getElementsByTagName("frame")
        for frame in frames:
            time = int(frame.getAttribute("timeId"))
            frame_id = int(frame.getAttribute("id"))

            actors_list = []
            actors = frame.getElementsByTagName("actor")
            for actor in actors:
                actor_id = int(actor.getAttribute("refId"))
                onScreenParts = actor.getElementsByTagName("onScreenPart")
                actor_result = {"actor_id": actor_id}
                for part in onScreenParts:
                    if part.getAttribute("part") == "Head":
                        position = part.getElementsByTagName("position")
                        position_x = None
                        position_y = None
                        relHeight = None
                        for x in position:
                            position_x = float(x.getAttribute("x"))
                            position_y = float(x.getAttribute("y"))

                        scale = part.getElementsByTagName("scale")
                        for x in scale:
                            relHeight = float(x.getAttribute("relHeight"))

                        if position_x and position_y and relHeight:
                            head = {
                                "position_x": position_x,
                                "position_y": position_y,
                                "relHeight": relHeight,
                            }
                            actor_result["head"] = head
                actors_list.append(actor_result)

            distance = None
            properties = frame.getElementsByTagName("property")
            for property in properties:
                if property.getAttribute("name") == "distance":
                    distance = property.getAttribute("value")

            angle = None
            properties = frame.getElementsByTagName("property")
            for property in properties:
                if property.getAttribute("name") == "angle":
                    angle = property.getAttribute("value")

            result_frames[frame_id] = {
                "time": time,
                "frame_id": frame_id,
                "actors": actors_list,
                "distance": distance,
                "angle": angle,
            }

    return result_frames


def get_timelines(data_manager, link):
    with zipfile.ZipFile(link, "r") as zip_file:
        for name in zip_file.namelist():
            if name.startswith("timelines.yml"):
                with zip_file.open(name) as f:
                    for x in yaml.safe_load(f):
                        yield (x["id"], x["name"])


def data_iterator(data_manager, link):
    with zipfile.ZipFile(link, "r") as zip_file:
        for name in zip_file.namelist():
            if name.startswith("data/") and name.endswith(".zip"):
                with zip_file.open(name) as f:
                    with data_manager.load_from_io(f) as data:
                        yield data


def parse_data(data_manager, zip_buffer):
    timelines = list(get_timelines(data_manager, zip_buffer))

    actor_timelines = [x[0] for x in timelines if "GT: Actor" in x[1]]
    shots_timelines = [x[0] for x in timelines if "GT: Shots" in x[1]]

    end_times = []
    movie_shot_annotations = []
    movie_shot_start_end = []
    faces = {}
    gt_actors = {}
    gt_movie_shot_start_end = []
    embeddings_map = {}
    for i, data in enumerate(data_iterator(data_manager, zip_buffer)):
        # Perform your analysis here
        # if data.type == "FacesData":
        #    print(data)
        if data.type == "AnnotationData":
            for x in data.annotations:
                for label in x.labels:
                    if "Shot Size::" in label:
                        movie_shot_annotations.append([label.split("Shot Size::")[-1]])
                        movie_shot_start_end.append([x.start, x.end])
                        end_times.append(x.end)

            if data.id in shots_timelines:
                for x in data.annotations:
                    for label in x.labels:
                        gt_movie_shot_start_end.append([x.start, x.end])

            # wu et al actors
            if data.id in actor_timelines:
                for x in data.annotations:
                    gt_actors[uuid.uuid4()] = {
                        "name": x.labels[0],
                        "start": x.start,
                        "end": x.end,
                        "cluster": i,
                        "time": (x.start + x.end) / 2,
                    }
                    end_times.append(x.end)

        if data.type == "FacesData":
            for face in data.faces:
                faces[face.id] = {}
    for data in data_iterator(data_manager, zip_buffer):
        if data.type == "ImageEmbeddings":
            for emb in data.embeddings:
                embeddings_map[emb.id] = emb.ref_id
                faces[emb.ref_id]["time"] = emb.time
        if data.type == "BboxesData":
            for bbox in data.bboxes:
                faces[bbox.ref_id]["bbox"] = bbox.to_dict()

    for data in data_iterator(data_manager, zip_buffer):
        if data.type == "ClusterData":
            for i, cluster in enumerate(data.clusters):
                for id in cluster.embedding_ids:
                    faces[embeddings_map[id]]["cluster"] = i

    return {
        "shot_annotations": movie_shot_annotations,
        "shot_start_end": movie_shot_start_end,
        "faces": faces,
        "gt_actors": gt_actors,
        "gt_shot_start_end": gt_movie_shot_start_end,
        "end_time": max(end_times),
    }


def download_zip(url, output_path):

    filename = url.split("/")[-1]
    if os.path.exists(os.path.join("data/", filename)):
        return os.path.join("data/", filename)
    response = requests.get(url)
    os.makedirs("data", exist_ok=True)
    with open(os.path.join("data/", filename), "wb") as f:
        f.write(response.content)

    print(f"Downloaded {filename}")
    return os.path.join("data/", filename)


#################
# SRS
#################


def detect_shot_reverse_shot(shot_start_end, faces, min_length=3):

    shot_face_list = []

    for index, [shot_start, shot_end] in enumerate(shot_start_end):
        shot_faces = set()
        for face in faces.values():
            if (
                shot_start < face["time"]
                and face["time"] < shot_end
                and "cluster" in face
            ):
                shot_faces.add(face["cluster"])

        shot_face_list.append(list(shot_faces))

    results = []
    n = len(shot_face_list)
    i = 0

    while i < n - 2:
        # Check first two shots are single-person and different
        if len(shot_face_list[i]) >= 1 and len(shot_face_list[i + 1]) >= 1:
            A = shot_face_list[i][0]
            B = shot_face_list[i + 1][0]

            if A != B:
                start = i
                expected = A
                j = i

                # Follow alternating pattern
                while j < n and len(shot_face_list[j]) == 1:
                    current = shot_face_list[j][0]

                    if current != expected:
                        break

                    # Switch expected speaker
                    expected = B if expected == A else A
                    j += 1

                length = j - start

                if length >= min_length:
                    results.append((start, j - 1, (A, B)))
                    i = j  # skip past this block
                    continue

        i += 1

    return results


#################
# Opposition
#################


def iou_xywh(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    # Convert to (x1, y1, x2, y2)
    x1_max = x1 + w1
    y1_max = y1 + h1

    x2_max = x2 + w2
    y2_max = y2 + h2

    # Intersection rectangle
    inter_x1 = max(x1, x2)
    inter_y1 = max(y1, y2)
    inter_x2 = min(x1_max, x2_max)
    inter_y2 = min(y1_max, y2_max)

    # Compute intersection area
    inter_width = max(0, inter_x2 - inter_x1)
    inter_height = max(0, inter_y2 - inter_y1)
    inter_area = inter_width * inter_height

    # Areas of boxes
    area1 = w1 * h1
    area2 = w2 * h2

    # Union
    union_area = area1 + area2 - inter_area

    if union_area == 0:
        return 0

    return inter_area / union_area


def left_right_cls(bbox):
    l_iou = iou_xywh([bbox["x"], bbox["y"], bbox["w"], bbox["h"]], [0, 0, 0.5, 1.0])
    r_iou = iou_xywh([bbox["x"], bbox["y"], bbox["w"], bbox["h"]], [0.5, 0, 0.5, 1.0])
    return l_iou, r_iou


def preprocess_prediction_for_opposition(shot_start_end, faces):

    shot_face_left_right_list = []
    for index, [shot_start, shot_end] in enumerate(shot_start_end):
        shot_faces = set()
        shot_left_right = {}
        for face in faces.values():
            if (
                shot_start < face["time"]
                and face["time"] < shot_end
                and "cluster" in face
                and "bbox" in face
            ):
                l_r = left_right_cls(face["bbox"])
                shot_faces.add(face["cluster"])

                if face["cluster"] not in shot_left_right:
                    shot_left_right[face["cluster"]] = [0.0, 0.0]
                shot_left_right[face["cluster"]][0] += l_r[0]
                shot_left_right[face["cluster"]][1] += l_r[1]

        shot_results = []
        for shot_face in shot_faces:
            shot_results.append(
                {
                    "cluster": shot_face,
                    "lr": "left"
                    if shot_left_right[shot_face][0] > shot_left_right[shot_face][1]
                    else "right",
                }
            )

        shot_face_left_right_list.append(shot_results)

    return shot_face_left_right_list


def preprocess_gt_for_opposition(shot_start_end, frames, fps):

    shot_face_left_right_list = []
    for index, [shot_start, shot_end] in enumerate(shot_start_end):
        shot_faces = set()
        shot_left_right = {}
        for frame in frames.values():
            f_time = frame["time"] / fps
            # print("######", frame)
            for actor in frame["actors"]:
                # print("#########", actor)
                if shot_start < f_time and f_time < shot_end and "head" in actor:
                    l_r = actor["head"]["position_x"]
                    shot_faces.add(actor["actor_id"])

                    if actor["actor_id"] not in shot_left_right:
                        shot_left_right[actor["actor_id"]] = []
                    shot_left_right[actor["actor_id"]].append(l_r)

        shot_results = []
        for shot_face in shot_faces:
            shot_results.append(
                {
                    "cluster": shot_face,
                    "lr": "left"
                    if np.mean(shot_left_right[shot_face]) < 0.5
                    else "right",
                }
            )

        shot_face_left_right_list.append(shot_results)

    return shot_face_left_right_list


def preprocess_gt_for_intensification(shot_start_end, frames, fps):

    distance_list = []
    for index, [shot_start, shot_end] in enumerate(shot_start_end):
        shot_distance = set()
        for frame in frames.values():
            f_time = frame["time"] / fps
            # print("######", frame)
            distance = frame["distance"]
            if not distance:
                continue
            if shot_start < f_time and f_time < shot_end:
                shot_distance.add(distance)

        if len(shot_distance) < 1:
            distance_list.append([])
        else:
            distance_list.append(list(shot_distance))
    return distance_list


def detect_opposition(shots, min_length=4):
    results = []
    n = len(shots)
    i = 0

    while i < n - 2:
        # Check first two shots are single-person and different
        if len(shots[i]) == 1 and len(shots[i + 1]) == 1:
            A = shots[i][0]["cluster"]
            B = shots[i + 1][0]["cluster"]

            A_lr = shots[i][0]["lr"]
            B_lr = shots[i + 1][0]["lr"]
            if A != B and A_lr != B_lr:
                start = i
                expected = A
                expected_lr = A_lr
                j = i

                # Follow alternating pattern
                while j < n and len(shots[j]) == 1:
                    current = shots[j][0]["cluster"]
                    current_lr = shots[j][0]["lr"]

                    if current != expected or current_lr != expected_lr:
                        break

                    # Switch expected speaker
                    expected = B if expected == A else A
                    expected_lr = B_lr if expected_lr == A_lr else A_lr
                    j += 1

                length = j - start

                if length >= min_length:
                    results.append((start, j - 1, (A, B)))
                    i = j  # skip past this block
                    continue

        i += 1

    return results


def detect_frameshare(shots, min_length=2):
    results = []
    n = len(shots)
    i = 0

    while i < n - 2:
        # Check first two shots are single-person and different
        if len(shots[i]) == 1 and len(shots[i + 1]) == 1:
            A = shots[i][0]["cluster"]
            B = shots[i + 1][0]["cluster"]

            A_lr = shots[i][0]["lr"]
            B_lr = shots[i + 1][0]["lr"]
            if A != B and A_lr == B_lr:
                start = i
                expected = A
                expected_lr = A_lr
                j = i

                # Follow alternating pattern
                while j < n and len(shots[j]) == 1:
                    current = shots[j][0]["cluster"]
                    current_lr = shots[j][0]["lr"]

                    if current != expected or current_lr != expected_lr:
                        break

                    # Switch expected speaker
                    expected = B if expected == A else A
                    expected_lr = B_lr if expected_lr == A_lr else A_lr
                    j += 1

                length = j - start

                if length >= min_length:
                    results.append((start, j - 1, (A, B)))
                    i = j  # skip past this block
                    continue

        i += 1

    return results


SHOT_SIZE_LABELS = {
    "Extreme Close-Up": 0,
    "Close-Up": 1,
    "Medium Shot": 2,
    "Full Shot": 3,
    "Long Shot": 4,
    "p_ECU": 0,
    "p_CU": 1,
    "p_MS": 2,
    "p_FS": 3,
    "p_LS": 4,
    "XCU": 0,  # Extreme Close-Up
    "BCU": 1,  # Big Close-Up
    "CU": 2,  # Close-Up
    "MCU": 3,  # Medium Close-Up
    "MS": 4,  # Medium Shot
    "MLS": 5,  # Medium Long Shot
    "LS": 6,  # Long Shot
    "VLS": 7,  # Very Long Shot
    "EST": 8,  # Establishing Shot
}

labels = ["Extreme Close-Up", "Close-Up", "Medium Shot", "Full Shot", "Long Shot"]


def norm_shot_size(shot_sizes):
    normalized = []
    for shot_size in shot_sizes:
        normalized.append(SHOT_SIZE_LABELS[shot_size])
    return np.mean(normalized)


def detect_shot_intensification(shots, min_length=2):
    results = []
    n = len(shots)
    i = 0

    while i < n - 2:
        sequence = []
        if len(shots[i]) == 0 or len(shots[i + 1]) == 0:
            i += 1
            continue
        shot_size_shot_1 = norm_shot_size(shots[i])
        shot_size_shot_2 = norm_shot_size(shots[i + 1])

        # Check first two shots

        if shot_size_shot_1 > shot_size_shot_2:
            start = i
            expected = norm_shot_size(shots[i + 1])
            j = i + 2

            # Follow pattern
            while j < n:
                if len(shots[j]) == 0:
                    j += 1
                    continue
                current = norm_shot_size(shots[j])

                sequence.append(current)

                if current > expected:
                    break

                expected = norm_shot_size(shots[j])
                j += 1

            length = j - start

            if length >= min_length:
                results.append((start, j - 1, sequence))
                i = j  # skip past this block
                continue

        i += 1

    return results


def detect_shot_samesize(shots, min_length=2):
    results = []
    n = len(shots)
    i = 0

    while i < n - 2:
        sequence = []
        if len(shots[i]) == 0 or len(shots[i + 1]) == 0:
            i += 1
            continue
        shot_size_shot_1 = norm_shot_size(shots[i])
        shot_size_shot_2 = norm_shot_size(shots[i + 1])

        # Check first two shots

        if shot_size_shot_1 == shot_size_shot_2:
            start = i
            expected = norm_shot_size(shots[i + 1])
            j = i + 2

            # Follow pattern
            while j < n:
                if len(shots[j]) == 0:
                    j += 1
                    continue
                current = norm_shot_size(shots[j])

                sequence.append(current)

                if current != expected:
                    break

                expected = norm_shot_size(shots[j])
                j += 1

            length = j - start

            if length >= min_length:
                results.append((start, j - 1, sequence))
                i = j  # skip past this block
                continue

        i += 1

    return results


def main():
    args = parse_args()

    data_manager = tibava_data.DataManager()
    results = {
        "srs": [],
        "oppo": [],
        "frameshare": [],
        "intensification": [],
        "samesize": [],
    }
    for link, gt in zip(movie_links, gt_links):
        print(link, gt)
        doc = minidom.parse(gt)

        gt_data = {
            "meta": extract_video_meta(doc),
            "shots": extract_shots(doc),
            "scenes": extract_scenes(doc),
            "actors": extract_actors(doc),
            "frames": extract_frames(doc),
        }

        filename = download_zip(link, "data/")
        data = parse_data(data_manager, filename)

        ################
        # SRS
        ################

        d_srs_vec = np.zeros(int(data["end_time"] * 1000))
        d_srs = detect_shot_reverse_shot(data["shot_start_end"], data["faces"])
        for x in d_srs:
            start_time = data["shot_start_end"][x[0]][0]
            end_time = data["shot_start_end"][x[1]][1]
            d_srs_vec[int(start_time * 1000) : int(end_time * 1000)] = 1

        gt_srs_vec = np.zeros(int(data["end_time"] * 1000))
        gt_srs = detect_shot_reverse_shot(data["gt_shot_start_end"], data["gt_actors"])
        for x in gt_srs:
            start_time = data["gt_shot_start_end"][x[0]][0]
            end_time = data["gt_shot_start_end"][x[1]][1]
            gt_srs_vec[int(start_time * 1000) : int(end_time * 1000)] = 1

        # Calculate correlation matrix
        matrix = np.corrcoef(d_srs_vec, gt_srs_vec)

        # Extract the correlation coefficient between x and y
        pearson_corr = matrix[0, 1]
        if not np.isnan(pearson_corr):
            results["srs"].append(pearson_corr)
        print(
            f"SRS d: {len(d_srs)} gt: {len(gt_srs)} ===> {pearson_corr} (filename: {filename})"
        )

        ################
        # Opposition
        ################

        d_oppo_vec = np.zeros(int(data["end_time"] * 1000))
        d_oppo_data = preprocess_prediction_for_opposition(
            data["shot_start_end"], data["faces"]
        )
        d_oppo = detect_opposition(d_oppo_data, min_length=2)
        for x in d_oppo:
            start_time = data["shot_start_end"][x[0]][0]
            end_time = data["shot_start_end"][x[1]][1]
            d_oppo_vec[int(start_time * 1000) : int(end_time * 1000)] = 1

        gt_oppo_vec = np.zeros(int(data["end_time"] * 1000))
        gt_oppo_data = preprocess_gt_for_opposition(
            data["shot_start_end"], gt_data["frames"], gt_data["meta"]["fps"]
        )
        gt_oppo = detect_opposition(gt_oppo_data, min_length=2)
        for x in gt_oppo:
            start_time = data["shot_start_end"][x[0]][0]
            end_time = data["shot_start_end"][x[1]][1]
            gt_oppo_vec[int(start_time * 1000) : int(end_time * 1000)] = 1

        # Calculate correlation matrix
        matrix = np.corrcoef(d_oppo_vec, gt_oppo_vec)
        pearson_corr = matrix[0, 1]
        if not np.isnan(pearson_corr):
            results["oppo"].append(pearson_corr)
        print(
            f"oppo d: {len(d_oppo)} gt: {len(gt_oppo)} ===> {pearson_corr} (filename: {filename})"
        )

        ################
        # Frameshare
        ################

        d_frameshare_vec = np.zeros(int(data["end_time"] * 1000))
        d_frameshare = detect_frameshare(d_oppo_data, min_length=2)
        for x in d_frameshare:
            start_time = data["shot_start_end"][x[0]][0]
            end_time = data["shot_start_end"][x[1]][1]
            d_frameshare_vec[int(start_time * 1000) : int(end_time * 1000)] = 1

        gt_frameshare_vec = np.zeros(int(data["end_time"] * 1000))
        gt_frameshare = detect_frameshare(gt_oppo_data, min_length=2)
        for x in gt_frameshare:
            start_time = data["shot_start_end"][x[0]][0]
            end_time = data["shot_start_end"][x[1]][1]
            gt_frameshare_vec[int(start_time * 1000) : int(end_time * 1000)] = 1

        # Calculate correlation matrix
        matrix = np.corrcoef(d_frameshare_vec, gt_frameshare_vec)
        pearson_corr = matrix[0, 1]
        if not np.isnan(pearson_corr):
            results["frameshare"].append(pearson_corr)
        print(
            f"frameshare d: {len(d_frameshare)} gt: {len(gt_frameshare)} ===> {pearson_corr} (filename: {filename})"
        )

        ################
        # Intensification
        ################

        d_intensification_vec = np.zeros(int(data["end_time"] * 1000))
        d_intensification = detect_shot_intensification(data["shot_annotations"])
        for x in d_intensification:
            start_time = data["shot_start_end"][x[0]][0]
            end_time = data["shot_start_end"][x[1]][1]
            d_intensification_vec[int(start_time * 1000) : int(end_time * 1000)] = 1

        gt_intensification_data = preprocess_gt_for_intensification(
            data["shot_start_end"], gt_data["frames"], gt_data["meta"]["fps"]
        )

        gt_intensification_vec = np.zeros(int(data["end_time"] * 1000))
        gt_intensification = detect_shot_intensification(gt_intensification_data)
        for x in gt_intensification:
            start_time = data["shot_start_end"][x[0]][0]
            end_time = data["shot_start_end"][x[1]][1]
            gt_intensification_vec[int(start_time * 1000) : int(end_time * 1000)] = 1

        # Calculate correlation matrix
        matrix = np.corrcoef(d_intensification_vec, gt_intensification_vec)

        # Extract the correlation coefficient between x and y
        pearson_corr = matrix[0, 1]
        if not np.isnan(pearson_corr):
            results["intensification"].append(pearson_corr)
        print(
            f"Intensification d: {len(d_intensification)} gt: {len(gt_intensification)} ===> {pearson_corr} (filename: {filename})"
        )
        ################
        # Same Size
        ################

        d_samesize_vec = np.zeros(int(data["end_time"] * 1000))
        d_samesize = detect_shot_samesize(data["shot_annotations"])
        for x in d_samesize:
            start_time = data["shot_start_end"][x[0]][0]
            end_time = data["shot_start_end"][x[1]][1]
            d_samesize_vec[int(start_time * 1000) : int(end_time * 1000)] = 1

        gt_samesize_vec = np.zeros(int(data["end_time"] * 1000))
        gt_samesize = detect_shot_samesize(gt_intensification_data)
        for x in gt_samesize:
            start_time = data["shot_start_end"][x[0]][0]
            end_time = data["shot_start_end"][x[1]][1]
            gt_samesize_vec[int(start_time * 1000) : int(end_time * 1000)] = 1

        # Calculate correlation matrix
        matrix = np.corrcoef(d_samesize_vec, gt_samesize_vec)

        # Extract the correlation coefficient between x and y
        pearson_corr = matrix[0, 1]
        if not np.isnan(pearson_corr):
            results["samesize"].append(pearson_corr)
        print(
            f"Same Size d: {len(d_samesize)} gt: {len(gt_samesize)} ===> {pearson_corr} (filename: {filename})"
        )

    print("srs: ", np.mean(results["srs"]))
    print("oppo: ", np.mean(results["oppo"]))
    print("frameshare: ", np.mean(results["frameshare"]))
    print("intensification: ", np.mean(results["intensification"]))
    print("samesize: ", np.mean(results["samesize"]))


if __name__ == "__main__":
    main()
