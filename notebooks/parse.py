import argparse
import math
import os
from turtle import pos
from xml.dom import minidom

import pympi


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("filenames", nargs="+")

    parser.add_argument("-o", "--output-path")
    args = parser.parse_args()

    return args


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


def add_scenes_to_elan(eaf, data):
    # create scene annotations
    eaf.add_tier("GT: Scenes")
    for scene_id, scene in data["scenes"].items():
        scenes_times = []
        for shot_in_scene in scene["shots"]:
            for shot_id, shot in data["shots"].items():
                if shot_in_scene == shot_id:
                    start = shot["start"]
                    end = shot["end"]

                    found = False
                    for x in scenes_times:
                        if x["start"] - 1 == end:
                            x["start"] = start
                            found = True
                        if x["end"] + 1 == start:
                            x["end"] = end
                            found = True
                    if not found:
                        scenes_times.append({"start": start, "end": end})
        for scene_times in scenes_times:
            eaf.add_annotation(
                "GT: Scenes",
                round((1 / data["meta"]["fps"]) * scene_times["start"] * 1000),
                round((1 / data["meta"]["fps"]) * scene_times["end"] * 1000),
                f"Scene {scene_id}",
            )


def add_shots_to_elan(eaf, data):

    eaf.add_tier("GT: Shots")
    for shot_id, shot in data["shots"].items():
        eaf.add_annotation(
            "GT: Shots",
            round((1 / data["meta"]["fps"]) * shot["start"] * 1000),
            round((1 / data["meta"]["fps"]) * shot["end"] * 1000),
            f"Shot {shot_id}",
        )


def add_actors_to_elan(eaf, data):
    actors_times = {}
    for actor_id, actor in data["actors"].items():
        actors_times[actor_id] = []
        eaf.add_tier(f"GT: Actor {actor['name']}")

    for shot_id, shot in data["shots"].items():
        shot_start_time = shot["start"]
        shot_end_time = shot["end"]
        for i, frame_id in enumerate(shot["frames"]):
            frame_time = data["frames"][frame_id]["time"]

            for a in data["frames"][frame_id]["actors"]:
                if len(shot["frames"]) > i + 1:
                    next_frame_id = shot["frames"][i + 1]
                    next_frame_time = data["frames"][next_frame_id]["time"]

                    end_time = (next_frame_time + frame_time) / 2
                    end_time = math.floor(end_time)
                else:
                    end_time = shot_end_time

                if 0 == i:
                    start_time = shot_start_time
                else:
                    prev_frame_id = shot["frames"][i - 1]
                    prev_frame_time = data["frames"][prev_frame_id]["time"]

                    start_time = (prev_frame_time + frame_time) / 2
                    start_time = math.floor(start_time) + 1

                actor_id = a["actor_id"]
                actors_times[actor_id].append([start_time, end_time])

    for actor_id, times in actors_times.items():
        merged_times = []
        start_time = None
        end_time = None
        for start_end_time in times:
            if start_time is None and end_time is None:
                start_time = start_end_time[0]
                end_time = start_end_time[1]
                continue

            if start_end_time[0] == end_time + 1:
                end_time = start_end_time[1]
            else:
                merged_times.append([start_time, end_time])
                start_time = start_end_time[0]
                end_time = start_end_time[1]

        if start_time is not None and end_time is not None:
            merged_times.append([start_time, end_time])
        actors_times[actor_id] = merged_times

    for actor_id, times in actors_times.items():
        actor_name = data["actors"][actor_id]["name"]
        for start_end_time in times:
            eaf.add_annotation(
                f"GT: Actor {actor_name}",
                round((1 / data["meta"]["fps"]) * start_end_time[0] * 1000),
                round((1 / data["meta"]["fps"]) * start_end_time[1] * 1000),
                f"{actor_name}",
            )


def add_distances_to_elan(eaf, data):
    eaf.add_tier("GT: Distance")

    distances = []
    for shot_id, shot in data["shots"].items():
        shot_start_time = shot["start"]
        shot_end_time = shot["end"]
        for i, frame_id in enumerate(shot["frames"]):
            frame_time = data["frames"][frame_id]["time"]
            distance = data["frames"][frame_id]["distance"]
            if distance is None:
                continue

            if len(shot["frames"]) > i + 1:
                next_frame_id = shot["frames"][i + 1]
                next_frame_time = data["frames"][next_frame_id]["time"]

                end_time = (next_frame_time + frame_time) / 2
                end_time = math.floor(end_time)
            else:
                end_time = shot_end_time

            if 0 == i:
                start_time = shot_start_time
            else:
                prev_frame_id = shot["frames"][i - 1]
                prev_frame_time = data["frames"][prev_frame_id]["time"]

                start_time = (prev_frame_time + frame_time) / 2
                start_time = math.floor(start_time) + 1
            distances.append([start_time, end_time, distance])

    merged_times = []
    start_time = None
    end_time = None
    distance = ""
    for start_end_time in distances:
        if start_time is None and end_time is None:
            start_time = start_end_time[0]
            end_time = start_end_time[1]
            distance = start_end_time[2]
            continue

        if start_end_time[0] == end_time + 1 and start_end_time[2] == distance:
            end_time = start_end_time[1]
        else:
            merged_times.append([start_time, end_time, distance])
            start_time = start_end_time[0]
            end_time = start_end_time[1]
            distance = start_end_time[2]

    if start_time is not None and end_time is not None:
        merged_times.append([start_time, end_time, distance])
    distances = merged_times

    for start_end_time in distances:
        eaf.add_annotation(
            "GT: Distance",
            round((1 / data["meta"]["fps"]) * start_end_time[0] * 1000),
            round((1 / data["meta"]["fps"]) * start_end_time[1] * 1000),
            f"{start_end_time[2]}",
        )


def add_angle_to_elan(eaf, data):
    eaf.add_tier("GT: Angle")

    angles = []
    for shot_id, shot in data["shots"].items():
        shot_start_time = shot["start"]
        shot_end_time = shot["end"]
        for i, frame_id in enumerate(shot["frames"]):
            frame_time = data["frames"][frame_id]["time"]
            angle = data["frames"][frame_id]["angle"]
            if angle is None:
                continue

            if len(shot["frames"]) > i + 1:
                next_frame_id = shot["frames"][i + 1]
                next_frame_time = data["frames"][next_frame_id]["time"]

                end_time = (next_frame_time + frame_time) / 2
                end_time = math.floor(end_time)
            else:
                end_time = shot_end_time

            if 0 == i:
                start_time = shot_start_time
            else:
                prev_frame_id = shot["frames"][i - 1]
                prev_frame_time = data["frames"][prev_frame_id]["time"]

                start_time = (prev_frame_time + frame_time) / 2
                start_time = math.floor(start_time) + 1
            angles.append([start_time, end_time, angle])

    merged_times = []
    start_time = None
    end_time = None
    angle = ""
    for start_end_time in angles:
        if start_time is None and end_time is None:
            start_time = start_end_time[0]
            end_time = start_end_time[1]
            angle = start_end_time[2]
            continue

        if start_end_time[0] == end_time + 1 and start_end_time[2] == angle:
            end_time = start_end_time[1]
        else:
            merged_times.append([start_time, end_time, angle])
            start_time = start_end_time[0]
            end_time = start_end_time[1]
            angle = start_end_time[2]

    if start_time is not None and end_time is not None:
        merged_times.append([start_time, end_time, angle])
    distances = merged_times

    for start_end_time in distances:
        eaf.add_annotation(
            "GT: Angle",
            round((1 / data["meta"]["fps"]) * start_end_time[0] * 1000),
            round((1 / data["meta"]["fps"]) * start_end_time[1] * 1000),
            f"{start_end_time[2]}",
        )


def main():
    args = parse_args()

    if args.output_path:
        os.makedirs(args.output_path, exist_ok=True)

    for filename in args.filenames:
        eaf = pympi.Elan.Eaf()
        eaf.remove_tier("default")
        basename = os.path.splitext(os.path.basename(filename))[0]
        doc = minidom.parse(filename)

        data = {
            "meta": extract_video_meta(doc),
            "shots": extract_shots(doc),
            "scenes": extract_scenes(doc),
            "actors": extract_actors(doc),
            "frames": extract_frames(doc),
        }
        add_scenes_to_elan(eaf, data)
        add_shots_to_elan(eaf, data)
        add_actors_to_elan(eaf, data)
        add_actors_to_elan(eaf, data)
        add_distances_to_elan(eaf, data)
        add_angle_to_elan(eaf, data)

        if args.output_path:
            eaf.to_file(os.path.join(args.output_path, f"{basename}.eaf"))


if __name__ == "__main__":
    main()
