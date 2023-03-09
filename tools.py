from langchain.agents import tool
from langchain.agents import initialize_agent
from langchain.llms import PromptLayerOpenAI

import shotstack_sdk as shotstack
import os, sys
import requests
import time

import pickle
from collections import OrderedDict

from shotstack_sdk.model.soundtrack  import Soundtrack
from shotstack_sdk.model.image_asset import ImageAsset
from shotstack_sdk.model.video_asset import VideoAsset
from shotstack_sdk.api               import edit_api
from shotstack_sdk.model.clip        import Clip
from shotstack_sdk.model.crop        import Crop
from shotstack_sdk.model.track       import Track
from shotstack_sdk.model.timeline    import Timeline
from shotstack_sdk.model.output      import Output
from shotstack_sdk.model.edit        import Edit
from shotstack_sdk.model.title_asset import TitleAsset
from shotstack_sdk.model.transition import Transition

video_and_image_clip_dict = OrderedDict()
subtitle_clip_dict = OrderedDict()
text_clip_dict = OrderedDict()
tracks = []

timeline = Timeline(background="#000000", tracks=tracks)
output = Output(format="mp4", resolution="sd")


# with open('./render/clips.pkl', 'rb') as f:
#     video_and_image_clip_dict, subtitle_clip_dict, text_clip_dict = pickle.load(f)
# with open('./render/tracks.pkl', 'rb') as f:
#     saved_tracks = pickle.load(f)


@tool("change_timeline_background_color")
def change_timeline_background_color(query: str) -> str:
    """change the timeline's background color. For example, to change the timeline background color to Silver, the query should be '#C0C0C0'.
    Always remember to set the color using hexadecimal color notation, for example 'white' is '#FFFFFF'. """

    color = query[1:-1]
    timeline.background = color
    return None


@tool("add_timeline_soundtrack")
def add_timeline_soundtrack(query: str) -> str:
    """add a music or audio soundtrack mp3 file for the timeline. For example, to add a music with url 'https://s3-ap-northeast-1.amazonaws.com/my-bucket/music.mp3', 
    the query should be 'https://s3-ap-northeast-1.amazonaws.com/my-bucket/music.mp3'."""

    url = query[1:-1]
    timeline.soundtrack.src = url
    return None


@tool("change_timeline_soundtrack_effect")
def change_timeline_soundtrack_effect(query: str) -> str:
    """change the timeline's soundtrack effect. For example, to change effect to 'fadeInFadeOut', 
    the query should be 'fadeInFadeOut', which means fade volume in and out."""

    effect = query[1:-1]

    if timeline.soundtrack != None:
        timeline.soundtrack.effect = effect
        return None
    else:
        return "The timeline soundtrack not exists, skip and continue to the next step."


@tool("change_timeline_soundtrack_volume")
def change_timeline_soundtrack_volume(query: str) -> str:
    """change the timeline's soundtrack volume.
    Set the volume for the soundtrack between 0 and 1 where 0 is muted and 1 is full volume (defaults to 1).
    For example, to change soundtrack's volume to 0.3, the query should be '0.3'."""

    vol = query[1:-1]

    if timeline.soundtrack != None:
        timeline.soundtrack.volume = float(vol)
        return None
    else:
        return "The timeline soundtrack not exists, skip and continue to the next step."


@tool("change_output_format")
def change_output_format(query: str) -> str:
    """change the output format. For example, to change output format to 'mp4', 
    the query should be 'mp4'."""

    format = query[1:-1]
    output.format = format
    return None


@tool("change_output_resolution")
def change_output_resolution(query: str) -> str:
    """change the output resolution. For example, to change output resolution to 'hd', 
    the query should be 'hd'. The resolution can be 'preview', 'mobile', 'sd', 'hd', '1080'."""

    reso = query[1:-1]
    output.resolution = reso
    return None


@tool("change_output_aspectRatio")
def change_output_aspectRatio(query: str) -> str:
    """change the output aspect ratio (shape) of the video. For example, to change output aspect ratio to '4:5', 
    the query should be '4:5'."""

    ratio = query[1:-1]
    output.aspectRatio = ratio
    return None


@tool("change_output_fps")
def change_output_fps(query: str) -> str:
    """change the output fps of the video. Override the default frames per second.
    For example, to change output fps to '23.976', 
    the query should be '23.976'."""

    fps = query[1:-1]
    output.fps = float(fps)
    return None


@tool("change_output_quality")
def change_output_quality(query: str) -> str:
    """change the output quality. For example, to change output quality to 'low', 
    the query should be 'low'."""

    qua = query[1:-1]
    output.quality = qua
    return None

@tool("set_output_repeat")
def set_output_repeat(query: str) -> str:
    """Loop settings for gif files. query is 'True' to loop and repeat, 'False' to play only once."""

    repeat = query[1:-1]
    output.repeat = bool(repeat)
    return None


@tool("set_output_mute")
def set_output_mute(query: str) -> str:
    """Mute the audio of the output video. query equals 'True' to mute, 'False' to un-mute."""

    mute = query[1:-1]
    output.mute = bool(mute)
    return None


@tool("choose_poster_from_timeline")
def choose_poster_from_timeline(query: str) -> str:
    """Generate a poster image for the video project from a specific point on the timeline. 
    For example, to capture the frame at 12.8 sec for video's poster image, the query should be '12.8'.
    Always remember to set the time using float, for example 8 seconds should be 8.0.
    """

    frame = query[1:-1]
    output.poster.capture = float(frame)
    return None


@tool("choose_thumbnail_from_timeline")
def choose_thumbnail_from_timeline(query: str) -> str:
    """Generate a thumbnail image for the video project from a specific point on the timeline. 
    For example, to capture the frame at 12.8 sec for video's thumbnail image, the query should be '12.8'.
    Always remember to set the time using float, for example 8 seconds should be 8.0.
    """

    frame = query[1:-1]
    output.thumbnail.capture = float(frame)
    output.thumbnail.scale = 1.0
    return None


@tool("add_text")
def add_text(query: str) -> str:
    """add text. For example, to add a text with content 'Tim's Vlog', starting from 2.5s and lasting for 4.5s,
    the query should be 'Tim's Vlog, 2.5, 4.5'. Always remember to set the time to 'start time(sec), last length(sec)' format,
    for example starting from 4.7s and ending at 5.2s should be transformed to '4.7, 0.5' because 0.5s = 5.2s - 4.7s.
    Always remember to set the time using float, for example 8 seconds should be 8.0."""

    content, st, lt = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        if text_clip_dict[content].start == float(st) and text_clip_dict[content].length == float(lt):
            return "The text has already been added in the project, skip and continue to the next step."
    else:
        text_asset = TitleAsset(style="minimal", text=content, size="x-large")
        text_clip = Clip(asset=text_asset, start=float(st), length=float(lt))
        text_clip_dict[content] = text_clip
        return None


@tool("change_text_color")
def change_text_color(query: str) -> str:
    """change the text color. For example, to change the 'how are you' text's color to yellow, the query should be 'how are you, #FFCA28'.
    Always remember to set the text color using hexadecimal color notation, for example 'white' is '#FFFFFF'. """

    content, color = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].asset.color = color
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("change_text_size")
def change_text_size(query: str) -> str:
    """change the text size. For example, to change the 'how are you' text's size to x-small, the query should be 'how are you, x-small'."""

    content, size = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].asset.size = size
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("change_text_background_color")
def change_text_background_color(query: str) -> str:
    """change the text's background color. For example, to change the 'max-o-man' text's color to Cyan, the query should be 'max-o-man, #00FFFF'.
    Always remember to set the background color using hexadecimal color notation, for example 'white' is '#FFFFFF'."""

    content, color = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].asset.background = color
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("change_text_style")
def change_text_style(query: str) -> str:
    """change the text's style. For example, to change the text 'take me to oblivion' style to 'sketchy', 
    the query should be 'take me to oblivion, sketchy'."""
    
    content, style = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].asset.style = style
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("change_text_effect")
def change_text_effect(query: str) -> str:
    """change the text's effect. For example, to change the text 'take me to oblivion' effect to 'zoomOut', 
    the query should be 'take me to oblivion, zoomOut'."""
    
    content, effect = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].effect = effect
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("change_text_opacity")
def change_text_opacity(query: str) -> str:
    """change the text's opacity. For example, to change the text 'take me to oblivion' opacity to 0.4, 
    the query should be 'take me to oblivion, 0.4'. Sets the opacity of the Clip where 1 is opaque and 0 is transparent."""
    
    content, opa = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].opacity = float(opa) 
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("rotate_text")
def rotate_text(query: str) -> str:
    """rotate the text by the specified angle in degrees. The angle to rotate the text can be 0 to 360, or 0 to -360. 
    Using a positive number rotates the clip clockwise, negative numbers counter-clockwise.
    For example, to rotate the text 'macos windows' 45 degrees clockwise, 
    the query should be 'macos windows, 45'."""
    
    content, deg = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].transform.rotate.angle = int(deg)
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("skew_text")
def skew_text(query: str) -> str:
    """Skew a text so its edges are sheared at an angle. Use values between 0 and 3. 
    Over 3 the clip will be skewed almost flat.
    For example, to skew the text 'macos windows' for 0.5 along it's x axis, and skew for 1.5 along it's y axis, 
    the query should be 'macos windows, 0.5, 1.5'.
    If only one axis chonsen, then set the other axis number to 0 for no skewing."""
    
    content, x, y = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].transform.skew.x = float(x)
        text_clip_dict[content].transform.skew.y = float(y)
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("flip_text")
def flip_text(query: str) -> str:
    """Flip a text vertically or horizontally.
    For example, to flip the text 'macos windows' horizontally, 
    the query should be 'macos windows, True, False'. Or to flip it vertically, the query is 'macos windows, False, True' then.
    Always set the query format to 'text_content, is_vertically_flip, is_horizontally_flip'.
    If flip for both vertically and horizontally, 'True, True' is good."""
    
    content, hor, ver = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].transform.flip.horizontal = bool(hor)
        text_clip_dict[content].transform.flip.vertical = bool(ver)
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("change_text_position")
def change_text_position(query: str) -> str:
    """change the text's position. For example, to change the text 'take me to oblivion' position to 'topRight', 
    the query should be 'take me to oblivion, topRight'."""
    
    content, pos = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].asset.position = pos
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("change_text")
def change_text(query: str) -> str:
    """change the text content to 'query'. For example, to change the 'helloWorld' text's content to 'CoffeeTime',
    the query should be 'helloWorld, CoffeeTime'."""

    content_old, content_new = query[1:-1].replace(", ", ",").split(",")

    if content_old in text_clip_dict.keys():
        text_clip_dict[content_old].asset.text = content_new
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("change_text_time")
def change_text_time(query: str) -> str:
    """change the text's start time and length. For example, to change the text 'Take Five' start time to 2 sec, with length 3 sec, 
    the query should be "Take Five, 2.0, 3.0".
    Always remember to set the time to "start_time, length" in seconds, for example, 
    start at 1s and end at 5s should be transformed to '1.0, 4.0', because 4s = 5s - 1s.
    Always remember to set the time using float, for example 8 seconds should be 8.0."""

    content, st, lt = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].start = float(st)
        text_clip_dict[content].length = float(lt)
        return None
    else:
        return "The text not exist, skip and continue to the next step."\


@tool("change_text_offset")
def change_text_offset(query: str) -> str:
    """change the text's offset. Offset the location of the title relative to its position on the screen.
    For example, to change the text 'Take Five' offset to x = 0.1 and y = -0.2, 
    the query should be 'Take Five, 0.1, -0.2'.
    Always remember to set the offset to 'x_offset, y_offset'. Always remember to set the offset using float."""

    content, x, y = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].asset.offset.x = float(x)
        text_clip_dict[content].asset.offset.y = float(y)
        return None
    else:
        return "The text not exist, skip and continue to the next step."


@tool("add_text_transition")
def add_text_transition(query: str) -> str:
    """add a transition for text. For example to add a 'shuffleLeftBottom' transition in the end of the text 'call on me',
    the query should be 'call on me, shuffleLeftBottom, out', and to add a 'zoom' transition in the start of the text 'holy grail',
    the query should be 'holy grail, zoom, in'. There are only 'in' and 'out' transitions."""

    content, trans, io = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        if io == 'in':
            text_transition = Transition(_in=trans)
            text_clip_dict[content].transition = text_transition
            return None
        elif io == 'out':
            text_transition = Transition(out=trans)
            text_clip_dict[content].transition = text_transition
            return None
        else:
            return "The transition type not 'in' or 'out', skip and continue to the next step."
    else:
        return "The video not exist, skip and continue to the next step."


@tool("add_subtitle")
def add_subtitle(query: str) -> str:
    """add subtitle. For example, to add a subtitle with content 'without a second glance', starting from 2.5s and lasting for 0.5s,
    the query should be 'Tim's Vlog, 2.5, 0.5'. Always remember to set the time to 'start time(sec), last length(sec)' format,
    for example starting from 4.7s and ending at 5.2s should be transformed to '4.7, 0.5' because 0.5s = 5.2s - 4.7s.
    Always remember to set the time using float, for example 8 seconds should be 8.0."""

    content, st, lt = query[1:-1].replace(", ", ",").split(",")

    if content in subtitle_clip_dict.keys():
        if subtitle_clip_dict[content].start == float(st) and subtitle_clip_dict[content].length == float(lt):
            return "The subtitle has already been added in the project, skip and continue to the next step."
    else:
        subtitle_asset = TitleAsset(style="subtitle", text=content, size="medium", position="bottom")
        subtitle_clip = Clip(asset=subtitle_asset, start=float(st), length=float(lt))
        subtitle_clip_dict[content] = subtitle_clip
        return None


@tool("change_subtitle_style")
def change_subtitle_style(query: str) -> str:
    """change the subtitle's style. For example, to change the subtitle 'the splitting of our species' style to 'sketchy', 
    the query should be 'the splitting of our species, sketchy'."""
    
    content, style = query[1:-1].replace(", ", ",").split(",")

    if content in subtitle_clip_dict.keys():
        subtitle_clip_dict[content].asset.style = style
        return None
    else:
        return "The subtitle not exist, skip and continue to the next step."


@tool("change_subtitle")
def change_subtitle(query: str) -> str:
    """change the subtitle content to 'query'. For example, to change the 'started from the bottom' subtitle's content to 'now we here',
    the query should be 'started from the bottom, now we here'."""

    content_old, content_new = query[1:-1].replace(", ", ",").split(",")

    if content_old in subtitle_clip_dict.keys():
        subtitle_clip_dict[content_old].asset.text = content_new
        return None
    else:
        return "The subtitle not exist, skip and continue to the next step."


@tool("change_subtitle_time")
def change_subtitle_time(query: str) -> str:
    """change the subtitle's start time and length. For example, to change the caption 'Take Five' start time to 2 sec, with length 3 sec, 
    the query should be "Take Five, 2.0, 3.0".
    Always remember to set the time to "start_time, length" in seconds, for example, 
    start at 1s and end at 5s should be transformed to '1.0, 4.0', because 4s = 5s - 1s.
    Always remember to set the time using float, for example 8 seconds should be 8.0."""

    content, st, lt = query[1:-1].replace(", ", ",").split(",")

    if content in subtitle_clip_dict.keys():
        subtitle_clip_dict[content].start = float(st)
        subtitle_clip_dict[content].length = float(lt)
        return None
    else:
        return "The subtitle not exist, skip and continue to the next step."


@tool("change_subtitle_position")
def change_subtitle_position(query: str) -> str:
    """change the subtitle's position. For example, to change the subtitle 'take me to oblivion' position to 'topRight', 
    the query should be 'take me to oblivion, topRight'."""
    
    content, pos = query[1:-1].replace(", ", ",").split(",")

    if content in subtitle_clip_dict.keys():
        subtitle_clip_dict[content].asset.position = pos
        return None
    else:
        return "The subtitle not exist, skip and continue to the next step."


@tool("change_subtitle_color")
def change_subtitle_color(query: str) -> str:
    """change the subtitle color. For example, to change the 'give me reason' subtitle's color to orange, the query should be 'give me reason, #FFA500'.
    Always remember to set the text color using hexadecimal color notation, for example 'white' is '#FFFFFF'. """

    content, color = query[1:-1].replace(", ", ",").split(",")

    if content in subtitle_clip_dict.keys():
        subtitle_clip_dict[content].asset.color = color
        return None
    else:
        return "The subtitle not exist, skip and continue to the next step."


@tool("change_subtitle_size")
def change_subtitle_size(query: str) -> str:
    """change the subtitle size. For example, to change the 'in a worse case before' subtitle's size to x-small, the query should be 'in a worse case before, x-small'."""

    content, size = query[1:-1].replace(", ", ",").split(",")

    if content in subtitle_clip_dict.keys():
        subtitle_clip_dict[content].asset.size = size
        return None
    else:
        return "The subtitle not exist, skip and continue to the next step."


@tool("change_subtitle_background_color")
def change_subtitle_background_color(query: str) -> str:
    """change the subtitle's background color. For example, to change the 'time machine' subtitle's color to Maroon, the query should be 'time machine, #800000'.
    Always remember to set the background color using hexadecimal color notation, for example 'white' is '#FFFFFF'."""

    content, color = query[1:-1].replace(", ", ",").split(",")

    if content in subtitle_clip_dict.keys():
        subtitle_clip_dict[content].asset.background = color
        return None
    else:
        return "The subtitle not exist, skip and continue to the next step."


@tool("change_subtitle_offset")
def change_subtitle_offset(query: str) -> str:
    """change the subtitle's offset. Offset the location of the subtitle relative to its position on the screen.
    For example, to change the subtitle 'a strange animal' offset to x = 0.1 and y = -0.2, 
    the query should be 'a strange animal, 0.1, -0.2'.
    Always remember to set the offset to 'x_offset, y_offset'. Always remember to set the offset using float."""

    content, x, y = query[1:-1].replace(", ", ",").split(",")

    if content in text_clip_dict.keys():
        text_clip_dict[content].asset.offset.x = float(x)
        text_clip_dict[content].asset.offset.y = float(y)
        return None
    else:
        return "The subtitle not exist, skip and continue to the next step."


@tool("add_video")
def add_video(query: str) -> str:
    """add a video. For example, to add a video from url 'https://s3-ap-southeast-2.amazonaws.com/shotstack-assets/footage/skater.hd.mp4', 
    starting from 45.7s and lasting for 66.3s, and the user wants to give it a name 'skater', then the query should be 'https://s3-ap-southeast-2.amazonaws.com/shotstack-assets/footage/skater.hd.mp4, skater, 45.7, 66.3'. 
    Always remember to set the time to 'start time(sec), last length(sec)' format,
    for example starting from 4.7s and ending at 5.2s should be transformed to '4.7, 0.5' because 0.5s = 5.2s - 4.7s.
    Always remember to set the time using float, for example 8 seconds should be 8.0.
    Use add_video only if video url and video name are given."""

    url, video_name, st, lt = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        if video_and_image_clip_dict[video_name].start == float(st) and video_and_image_clip_dict[video_name].length == float(lt):
            return "The video has already been added in the project, skip and continue to the next step."
    else:
        video_asset = VideoAsset(src=url)
        video_clip = Clip(asset=video_asset, start=float(st), length=float(lt))
        video_and_image_clip_dict[video_name] = video_clip
        return None


@tool("change_video_volume")
def change_video_volume(query: str) -> str:
    """change the video's volume.
    Set the volume for the video between 0 and 1 where 0 is muted and 1 is full volume (defaults to 1).
    For example, to change the video with name 'dancing_disco' volume to 0.3, the query should be 'dancing_disco, 0.3'."""

    video_name, vol = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].asset.volume = float(vol)
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("change_video_volume_effect")
def change_video_volume_effect(query: str) -> str:
    """change the video's volume effect.
    For example, to change the video with name 'minecraft' volume effect to 'fadeOut', the query should be 'minecraft, fadeOut'."""

    video_name, effect = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].asset.volumeEffect = effect
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("trim_video")
def trim_video(query: str) -> str:
    """trim the video starting from 'query' seconds. Videos will start from the in trim point.
    The video will play until the file ends or the Clip length is reached. For example, to trim the video named 'skater' starting from 12 seconds,
    the query should be 'skater, 12.0'.
    Always remember to set the time using float, for example 8 seconds should be 8.0."""
    
    video_name, st = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].asset.trim = float(st)
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("crop_video")
def crop_video(query: str) -> str:
    """crop the video. Crop the sides of video asset by a relative amount. The size of the crop is specified using a scale between 0 and 1, relative to the screen width.
       For example, to crop 0.15 of the right and half of the bottom for video 'assasin creed', the query should be 'assasin creed, 0, 0.5, 0, 0.15'.
       Always remember the format of query is 'video_name, top_crop_ratio, bottom_crop_ratio, left_crop_ratio, right_crop_ratio'."""
    
    video_name, top, bottom, left, right = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_crop = Crop(top=float(top), bottom=float(bottom), left=float(left), right=float(right))
        video_and_image_clip_dict[video_name].asset.crop = video_crop
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("add_video_transition")
def add_video_transition(query: str) -> str:
    """add a transition for video. For example to add a 'shuffleLeftBottom' transition in the end of the video named 'skater',
    the query should be 'skater, shuffleLeftBottom, out', and to add a 'zoom' transition in the start of the video named 'flower',
    the query should be 'flower, zoom, in'. There are only 'in' and 'out' transitions."""

    video_name, trans, io = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        if io == 'in':
            video_transition = Transition(_in=trans)
            video_and_image_clip_dict[video_name].transition = video_transition
            return None
        elif io == 'out':
            video_transition = Transition(out=trans)
            video_and_image_clip_dict[video_name].transition = video_transition
            return None
        else:
            return "The transition type not 'in' or 'out', skip and continue to the next step."
    else:
        return "The video not exist, skip and continue to the next step."


@tool("change_video_time")
def change_video_time(query: str) -> str:
    """change the video's start time and length. For example, to change the video named 'sky' start time to 7 sec, with length 20 sec, 
    the query should be "sky, 7.0, 20.0".
    Always remember to set the time to "start_time, length" in seconds, for example, 
    start at 1s and end at 5s should be transformed to '1.0, 4.0', because 4s = 5s - 1s.
    Always remember to set the time using float, for example 8 seconds should be 8.0."""

    video_name, st, lt = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].start = float(st)
        video_and_image_clip_dict[video_name].length = float(lt)
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("scale_video")
def scale_video(query: str) -> str:
    """Scale the video to a fraction of the viewport size, i.e. setting the scale to 0.5 will scale video to half the size of the viewport. 
    This is useful for picture-in-picture video. For example, to scale the video to 0.7 with name as 'blue planet',
    the query should be 'blue planet, 0.7'."""

    video_name, scale = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].scale = float(scale)
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("set_video_position")
def set_video_position(query: str) -> str:
    """Place the video in one of nine predefined positions of the viewport.
    For example, to set the video 'blue planet' position at 'bottomLeft',
    the query should be 'blue planet, bottomLeft'."""

    video_name, pos = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].position = pos
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("change_video_offset")
def change_video_offset(query: str) -> str:
    """change the video's offset. Offset the location of the video relative to its position on the screen.
    For example, to change the video 'ark game' offset to x = 0.1 and y = -0.2, 
    the query should be 'ark game, 0.1, -0.2'.
    Always remember to set the offset to 'x_offset, y_offset'. Always remember to set the offset using float."""

    video_name, x, y = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].offset.x = float(x)
        video_and_image_clip_dict[video_name].offset.y = float(y)
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("change_video_effect")
def change_video_effect(query: str) -> str:
    """change the video's effect. For example, to change the video 'kitty' effect to 'zoomOut', 
    the query should be 'kitty, zoomOut'."""
    
    video_name, effect = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].effect = effect
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("add_video_filter")
def add_video_filter(query: str) -> str:
    """add a filter to the video. For example, to add a 'greyscale' filter to the video 'space bebop',
    the query should be 'space bebop, greyscale'."""
    
    video_name, filter = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].filter = filter
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("set_video_opacity")
def set_video_opacity(query: str) -> str:
    """Sets the opacity of the video where 1 is opaque and 0 is transparent. For example, to set the video 'space bebop' opacity to 0.35,
    the query should be 'space bebop, 0.35'. Always remember to set the opacity using float."""
    
    video_name, opa = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].opacity = float(opa)
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("rotate_video")
def rotate_video(query: str) -> str:
    """rotate the video by the specified angle in degrees. The angle to rotate the video can be 0 to 360, or 0 to -360. 
    Using a positive number rotates the clip clockwise, negative numbers counter-clockwise.
    For example, to rotate the video 'bigbang theory' 60 degrees clockwise, 
    the query should be 'bigbang theory, 60'."""
    
    video_name, deg = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].transform.rotate.angle = int(deg)
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("skew_video")
def skew_video(query: str) -> str:
    """Skew a video so its edges are sheared at an angle. Use values between 0 and 3. 
    Over 3 the clip will be skewed almost flat.
    For example, to skew the video 'bigbang theory' for 0.5 along it's x axis, and skew for 1.5 along it's y axis, 
    the query should be 'bigbang theory, 0.5, 1.5'.
    If only one axis chonsen, then set the other axis number to 0 for no skewing."""
    
    video_name, x, y = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].transform.skew.x = float(x)
        video_and_image_clip_dict[video_name].transform.skew.y = float(y)
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("flip_video")
def flip_video(query: str) -> str:
    """Flip a video vertically or horizontally.
    For example, to flip the video 'friends' horizontally, 
    the query should be 'friends, True, False'. Or to flip it vertically, the query is 'friends, False, True' then.
    Always set the query format to 'video_name, is_vertically_flip, is_horizontally_flip'.
    If flip for both vertically and horizontally, 'True, True' is good."""
    
    video_name, hor, ver = query[1:-1].replace(", ", ",").split(",")

    if video_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[video_name].transform.flip.horizontal = bool(hor)
        video_and_image_clip_dict[video_name].transform.flip.vertical = bool(ver)
        return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("video_move_foward")
def video_move_foward(query: str) -> str:
    """Move the video one layer forward in the Layer. The query should be video name."""
    
    video_name = query[1:-1]
    video_list = list(video_and_image_clip_dict.items())

    if video_name in video_and_image_clip_dict.keys():
        video_index = video_list.index(video_name)

        if video_index == 0:
            return "The video is already in the first layer, skip and continue to the next step."
        else:
            video_list[video_index], video_list[video_index-1] = video_list[video_index-1], video_list[video_index]
            return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("video_move_backward")
def video_move_backward(query: str) -> str:
    """Move the video one layer backward in the Layer. The query should be video name."""
    
    video_name = query[1:-1]
    video_list = list(video_and_image_clip_dict.items())

    if video_name in video_and_image_clip_dict.keys():
        video_index = video_list.index(video_name)

        if video_index == len(video_list)-1:
            return "The video is already in the first layer, skip and continue to the next step."
        else:
            video_list[video_index], video_list[video_index+1] = video_list[video_index+1], video_list[video_index]
            return None
    else:
        return "The video not exist, skip and continue to the next step."


@tool("add_image")
def add_image(query: str) -> str:
    """add a image. For example, to add an image from url 'https://s3-ap-southeast-2.amazonaws.com/shotstack-assets/examples/images/pexels/pexels-photo-712850.jpeg', 
    starting from 45.7s and lasting for 66.3s, and the user gives it a name 'green_sea', the query should be 'https://s3-ap-southeast-2.amazonaws.com/shotstack-assets/examples/images/pexels/pexels-photo-712850.jpeg, green_sea, 45.7, 66.3'. 
    Always remember to set the time to 'start time(sec), last length(sec)' format,
    for example starting from 4.7s and ending at 5.2s should be transformed to '4.7, 0.5' because 0.5s = 5.2s - 4.7s.
    Always remember to set the time using float, for example 8 seconds should be 8.0.
    Use add_image only if image url and image name is given."""

    url, image_name, st, lt = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        if video_and_image_clip_dict[image_name].start == float(st) and video_and_image_clip_dict[image_name].length == float(lt):
            return "The image has already been added in the project, skip and continue to the next step."
    else:
        image_asset = ImageAsset(src=url)
        image_clip = Clip(asset=image_asset, start=float(st), length=float(lt))
        video_and_image_clip_dict[image_name] = image_clip
        return None


@tool("crop_image")
def crop_image(query: str) -> str:
    """crop the image. Crop the sides of an image asset by a relative amount. The size of the crop is specified using a scale between 0 and 1, relative to the screen width.
       For example, to crop 0.15 of the right and half of the bottom for image 'pen case', the query should be 'pen case, 0, 0.5, 0, 0.15'.
       Always remember the format of query is 'image_name, top_crop_ratio, bottom_crop_ratio, left_crop_ratio, right_crop_ratio'."""
    
    image_name, top, bottom, left, right = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        image_crop = Crop(top=float(top), bottom=float(bottom), left=float(left), right=float(right))
        video_and_image_clip_dict[image_name].asset.crop = image_crop
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("add_image_transition")
def add_image_transition(query: str) -> str:
    """add a transition for image. For example to add a 'shuffleLeftBottom' transition in the end of the image named 'tea',
    the query should be 'tea, shuffleLeftBottom, out', and to add a 'zoom' transition in the start of the image named 'flower',
    the query should be 'flower, zoom, in'. There are only 'in' and 'out' transitions."""
    
    image_name, trans, io = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        if io == 'in':
            image_transition = Transition(_in=trans)
            video_and_image_clip_dict[image_name].transition = image_transition
            return None
        elif io == 'out':
            image_transition = Transition(out=trans)
            video_and_image_clip_dict[image_name].transition = image_transition
            return None
        else:
            return "The transition type not 'in' or 'out', skip and continue to the next step."
    else:
        return "The image not exist, skip and continue to the next step."



@tool("change_image_time")
def change_image_time(query: str) -> str:
    """change the image's start time and length. For example, to change the image named 'aa' start time to 7 sec, with length 20 sec, 
    the query should be "aa, 7.0, 20.0".
    Always remember to set the time to "start_time, length" in seconds, for example, 
    start at 1s and end at 5s should be transformed to '1.0, 4.0', because 4s = 5s - 1s.
    Always remember to set the time using float, for example 8 seconds should be 8.0."""

    image_name, st, lt = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[image_name].start = float(st)
        video_and_image_clip_dict[image_name].length = float(lt)
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("scale_image")
def scale_image(query: str) -> str:
    """Scale the image to a fraction of the viewport size, i.e. setting the scale to 0.5 will scale image to half the size of the viewport. 
    This is useful for scaling images such as logos and watermarks. For example, to scale the image to 0.7 with name as 'blue planet',
    the query should be 'blue planet, 0.7'."""

    image_name, scale = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[image_name].scale = float(scale)
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("set_image_position")
def set_image_position(query: str) -> str:
    """Place the image in one of nine predefined positions of the viewport.
    For example, to set the image 'blue planet' position at 'bottomLeft',
    the query should be 'blue planet, bottomLeft'."""

    image_name, pos = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[image_name].position = pos
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("change_image_offset")
def change_image_offset(query: str) -> str:
    """change the image's offset. Offset the location of the image relative to its position on the screen.
    For example, to change the image 'capture' offset to x = 0.1 and y = -0.2, 
    the query should be 'capture, 0.1, -0.2'.
    Always remember to set the offset to 'x_offset, y_offset'. Always remember to set the offset using float."""

    image_name, x, y = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[image_name].offset.x = float(x)
        video_and_image_clip_dict[image_name].offset.y = float(y)
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("change_image_effect")
def change_image_effect(query: str) -> str:
    """change the image's effect. For example, to change the image 'pepper' effect to 'zoomOut', 
    the query should be 'pepper, zoomOut'."""
    
    image_name, effect = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[image_name].effect = effect
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("add_image_filter")
def add_image_filter(query: str) -> str:
    """add a filter to the image. For example, to add a 'greyscale' filter to the image 'phonechat',
    the query should be 'phonechat, greyscale'."""
    
    image_name, filter = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[image_name].filter = filter
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("set_image_opacity")
def set_image_opacity(query: str) -> str:
    """Sets the opacity of the image where 1 is opaque and 0 is transparent. For example, to set the image 'space bebop' opacity to 0.35,
    the query should be 'space bebop, 0.35'. Always remember to set the opacity using float."""
    
    image_name, opa = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[image_name].opacity = float(opa)
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("rotate_image")
def rotate_image(query: str) -> str:
    """rotate the image by the specified angle in degrees. The angle to rotate the image can be 0 to 360, or 0 to -360. 
    Using a positive number rotates the clip clockwise, negative numbers counter-clockwise.
    For example, to rotate the image 'birds' 60 degrees clockwise, 
    the query should be 'birds, 60'."""
    
    image_name, deg = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[image_name].transform.rotate.angle = int(deg)
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("skew_image")
def skew_image(query: str) -> str:
    """Skew a image so its edges are sheared at an angle. Use values between 0 and 3. 
    Over 3 the clip will be skewed almost flat.
    For example, to skew the image 'bigbang theory' for 0.5 along it's x axis, and skew for 1.5 along it's y axis, 
    the query should be 'bigbang theory, 0.5, 1.5'.
    If only one axis chonsen, then set the other axis number to 0 for no skewing."""
    
    image_name, x, y = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[image_name].transform.skew.x = float(x)
        video_and_image_clip_dict[image_name].transform.skew.y = float(y)
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("flip_image")
def flip_image(query: str) -> str:
    """Flip a image vertically or horizontally.
    For example, to flip the image 'banana' horizontally, 
    the query should be 'banana, True, False'. Or to flip it vertically, the query is 'banana, False, True' then.
    Always set the query format to 'image_name, is_vertically_flip, is_horizontally_flip'.
    If flip for both vertically and horizontally, 'True, True' is good."""
    
    image_name, hor, ver = query[1:-1].replace(", ", ",").split(",")

    if image_name in video_and_image_clip_dict.keys():
        video_and_image_clip_dict[image_name].transform.flip.horizontal = bool(hor)
        video_and_image_clip_dict[image_name].transform.flip.vertical = bool(ver)
        return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("image_move_foward")
def image_move_foward(query: str) -> str:
    """Move the image one layer forward in the Layer. The query should be image name."""
    
    image_name = query[1:-1]
    image_list = list(video_and_image_clip_dict.items())

    if image_name in video_and_image_clip_dict.keys():
        image_index = image_list.index(image_name)

        if image_index == 0:
            return "The image is already in the first layer, skip and continue to the next step."
        else:
            image_list[image_index], image_list[image_index-1] = image_list[image_index-1], image_list[image_index]
            return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("image_move_backward")
def image_move_backward(query: str) -> str:
    """Move the image one layer backward in the Layer. The query should be image name."""
    
    image_name = query[1:-1]
    image_list = list(video_and_image_clip_dict.items())

    if image_name in video_and_image_clip_dict.keys():
        image_index = image_list.index(image_name)

        if image_index == len(image_list)-1:
            return "The image is already in the last layer, skip and continue to the next step."
        else:
            image_list[image_index], image_list[image_index+1] = image_list[image_index+1], image_list[image_index]
            return None
    else:
        return "The image not exist, skip and continue to the next step."


@tool("render_video")
def render_video(query: str) -> str:
    """rendering the video. query is not important."""

    host = "https://api.shotstack.io/stage"

    if os.getenv("SHOTSTACK_HOST") is not None:
        host = os.getenv("SHOTSTACK_HOST")
    if os.getenv("SHOTSTACK_KEY") is None:
        sys.exit("API Key is required. Set using: export SHOTSTACK_KEY=your_key_here") 

    configuration = shotstack.Configuration(host=host)
    configuration.api_key['DeveloperKey'] = os.getenv("SHOTSTACK_KEY")

    with shotstack.ApiClient(configuration) as api_client:
        api_instance = edit_api.EditApi(api_client)
        
        for text_clip in text_clip_dict.values():
            text_track = Track(clips=[text_clip])
            tracks.append(text_track)
        for subtitle_clip in subtitle_clip_dict.values():
            subtitle_track = Track(clips=[subtitle_clip])
            tracks.append(subtitle_track)
        for video_and_image_clip in video_and_image_clip_dict.values():
            video_and_image_track = Track(clips=[video_and_image_clip])
            tracks.append(video_and_image_track)

        timeline.tracks = tracks
        edit = Edit(timeline=timeline, output=output)

        try:
            api_response = api_instance.post_render(edit)
            message = api_response['response']['message']
            id = api_response['response']['id']

        
            print('\n' + f"{message}" + '\n')

            if id is None:
                sys.exit("Please provide the UUID of the render task.")  
            try:
                while True:
                    api_response = api_instance.get_render(id, data=False, merged=True)
                    status = api_response['response']['status']
                    print('Status: ' + status.upper() + '\n')

                    if status == "done":
                        url = api_response['response']['url']
                        print(f"Asset URL: {url}")

                        r = requests.get(url)
                        with open('./render/video.mp4', 'wb') as f:
                            f.write(r.content)
                            
                        # with open('./render/tracks.pkl', 'wb') as f:
                        #     pickle.dump(tracks, f)
                        # with open('./render/clips.pkl', 'wb') as f:
                        #     pickle.dump((video_and_image_clip_dict, subtitle_clip_dict, text_clip_dict), f)

                        break

                    elif status == 'failed':
                        break
                    else:
                        time.sleep(10)

            except Exception as e:
                print(f"Unable to resolve API call: {e}") 

        except Exception as e:
            print(f"Unable to resolve API call: {e}")

    return "video rendered successfully."


llm1 = PromptLayerOpenAI(temperature=0, pl_tags=["shotstack_subagent"])
text_agent = initialize_agent([add_text, change_text_color, change_text_background_color, change_text_style, change_text, change_text_size, change_text_effect, change_text_opacity, rotate_text, skew_text, flip_text, change_text_position, change_text_time, change_text_offset, add_text_transition], llm1, agent="zero-shot-react-description", verbose=True)

llm2 = PromptLayerOpenAI(temperature=0, pl_tags=["shotstack_subagent"])
subtitle_agent = initialize_agent([add_subtitle, change_subtitle, change_subtitle_time, change_subtitle_color, change_subtitle_style, change_subtitle_position, change_subtitle_size, change_subtitle_background_color, change_subtitle_offset], llm2, agent="zero-shot-react-description", verbose=True)

llm3 = PromptLayerOpenAI(temperature=0, pl_tags=["shotstack_subagent"])
video_agent = initialize_agent([add_video, change_video_volume, change_video_volume_effect, trim_video, add_video_transition, crop_video, change_video_time, scale_video, set_video_position, change_video_offset, change_video_effect, add_video_filter, set_video_opacity, rotate_video, skew_video, flip_video, video_move_foward, video_move_backward], llm3, agent="zero-shot-react-description", verbose=True)

llm4 = PromptLayerOpenAI(temperature=0, pl_tags=["shotstack_subagent"])
image_agent = initialize_agent([add_image, crop_image, add_image_transition, change_image_time, scale_image, set_image_position, change_image_offset, change_image_effect, add_image_filter, set_image_opacity, rotate_image, skew_image, flip_image, image_move_foward, image_move_backward], llm4, agent="zero-shot-react-description", verbose=True)

llm5 = PromptLayerOpenAI(temperature=0, pl_tags=["shotstack_subagent"])
timeline_config_agent = initialize_agent([change_timeline_background_color, add_timeline_soundtrack, change_timeline_soundtrack_effect, change_timeline_soundtrack_volume, choose_poster_from_timeline, choose_thumbnail_from_timeline], llm5, agent="zero-shot-react-description", verbose=True)

llm6 = PromptLayerOpenAI(temperature=0, pl_tags=["shotstack_subagent"])
output_config_agent = initialize_agent([change_output_format, change_output_resolution, change_output_aspectRatio, change_output_fps, change_output_quality, set_output_repeat, set_output_mute], llm6, agent="zero-shot-react-description", verbose=True)
