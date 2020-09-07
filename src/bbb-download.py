#!/usr/bin/env python2

__author__ = 'CreateWebinar.com'
__email__ = 'support@createwebinar.com'

from xml.dom import minidom
import sys
import os
import shutil
import zipfile
import re
import time

# Python script that produces downloadable material from a published bbb recording.

# Catch exception so that the script can be also called manually like: python download.py meetingId,
# in addition to being called from the bbb control scripts.
assetsPath = sys.argv[1]

ASSETS_PATH = assetsPath
LOGS = ASSETS_PATH + "/log"
source_dir = ASSETS_PATH + "/"
temp_dir = source_dir + 'temp/'
target_dir = source_dir + 'download/'
audio_path = 'audio/'
events_file = 'shapes.svg'
LOGFILE = LOGS + "/preprocessing.log"
source_events = ASSETS_PATH + '/events.xml'
# Deskshare
SOURCE_DESKSHARE = source_dir + 'deskshare.webm'
TMP_DESKSHARE_FILE = temp_dir + 'deskshare.mp4'
SOURCE_WEBCAMS   = source_dir + 'webcams.webm'
FFMPEG = 'ffmpeg -loglevel verbose '
VID_ENCODER = 'libx264'

## START OF Inlined ffmpeg module
def ffmpeg_set_logfile(file):
    global logfile
    logfile = file


def ffmpeg_mux_slideshow_audio(video_file, audio_file, out_file):
    command = '%s -i %s -i %s -map 0 -map 1 -codec copy -shortest %s 2>> %s' % (
        FFMPEG, video_file, audio_file, out_file, logfile)
    os.system(command)


def ffmpeg_extract_audio_from_video(video_file, out_file):
    command = '%s -i %s -ab 160k -ac 2 -ar 44100 -vn %s 2>> %s' % (FFMPEG, video_file, out_file, logfile)
    os.system(command)

def ffmpeg_dual_view_from(left_part, right_part, out_file):
    if os.path.exists(right_part):
        left_filter = 'setpts=PTS-STARTPTS,pad=iw*2:ih:color=white'
        right_filter = 'scale2ref=w=iw/2:h=ih'
        combined_filter = 'overlay=x=W-w:shortest=1'
        filter_complex = '[0:v]%s[ref];[1:v]setpts=PTS-STARTPTS[2nd];[2nd][ref]%s[r][l];[l][r]%s[vout]' % (left_filter, right_filter, combined_filter)
        command = '%s -i %s -i %s -filter_complex "%s" -map [vout] -map 0:a -aspect 32:9 %s 2>> %s' % (FFMPEG, left_part, right_part, filter_complex, out_file, logfile)
        os.system(command)

def ffmpeg_create_video_from_image(image, duration, out_file):
    print "*************** create_video_from_image ******************"
    print image, "\n", duration, "\n", out_file
    command = '%s -loop 1 -r 5 -f image2 -i %s -c:v %s -t %s -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s 2>> %s' % (
        FFMPEG, image, VID_ENCODER, duration, out_file, logfile)
    os.system(command)


def ffmpeg_concat_videos(video_list, out_file):
    command = '%s -f concat -safe 0 -i %s -c copy %s 2>> %s' % (FFMPEG, video_list, out_file, logfile)
    os.system(command)


def ffmpeg_mp4_to_ts(input, output):
    command = '%s -i %s -c copy -bsf:v h264_mp4toannexb -f mpegts %s 2>> %s' % (FFMPEG, input, output, logfile)
    os.system(command)


def ffmpeg_concat_ts_videos(input, output):
    command = '%s -i %s -c copy -bsf:a aac_adtstoasc %s 2>> %s' % (FFMPEG, input, output, logfile)
    os.system(command)


def ffmpeg_rescale_image(image, height, width, out_file):
    if height < width:
        command = '%s -i %s -vf pad=%s:%s:0:oh/2-ih/2 %s -y 2>> %s' % (FFMPEG, image, width, height, out_file, logfile)
    else:
        command = '%s -i %s -vf pad=%s:%s:0:ow/2-iw/2 %s -y 2>> %s' % (FFMPEG, image, width, height, out_file, logfile)

    os.system(command)


def ffmpeg_trim_video(video_file, start, end, out_file):
    start_h = start / 3600
    start_m = start / 60 - start_h * 60
    start_s = start % 60

    end_h = end / 3600
    end_m = end / 60 - end_h * 60
    end_s = end % 60

    str1 = '%d:%d:%d' % (start_h, start_m, start_s)
    str2 = '%d:%d:%d' % (end_h, end_m, end_s)
    command = '%s -ss %s -t %s -i %s -vcodec copy -acodec copy %s 2>> %s' % (
    FFMPEG, str1, str2, video_file, out_file, logfile)
    os.system(command)

def ffmpeg_trim_video_by_seconds(video_file, start, end, out_file):
    command = '%s -ss %s -i %s -c copy -t %s %s 2>> %s' % (FFMPEG, start, video_file, end, out_file, logfile)
    os.system(command)


def ffmpeg_trim_audio(audio_file, start, end, out_file):
    temp_file = 'temp.mp3'
    start_h = start / 3600
    start_m = start / 60 - start_h * 60
    start_s = start % 60

    end_h = end / 3600
    end_m = end / 60 - end_h * 60
    end_s = end % 60

    str1 = '%d:%d:%d' % (start_h, start_m, start_s)
    str2 = '%d:%d:%d' % (end_h, end_m, end_s)
    command = '%s -ss %s -t %s -i %s %s 2>> %s' % (FFMPEG, str1, str2, audio_file, temp_file, logfile)
    os.system(command)
    mp3_to_aac(temp_file, out_file)
    os.remove(temp_file)


def ffmpeg_trim_audio_start(dictionary, length, full_audio, audio_trimmed):
    times = dictionary.keys()
    times.sort()
    trim_audio(full_audio, int(round(times[0])), int(length), audio_trimmed)


def trim_video_start(dictionary, length, full_vid, video_trimmed):
    times = dictionary.keys()
    times.sort()
    trim_video(full_vid, int(round(times[2])), int(length), video_trimmed)


def ffmpeg_mp3_to_aac(mp3_file, aac_file):
    command = '%s -i %s -c:a aac %s 2>> %s' % (FFMPEG, mp3_file, aac_file, logfile)
    os.system(command)


def ffmpeg_webm_to_mp4(webm_file, mp4_file):
    command = '%s -i %s -qscale 0 %s 2>> %s' % (FFMPEG, webm_file, mp4_file, logfile)
    os.system(command)


def ffmpeg_audio_to_video(audio_file, image_file, video_file):
    command = '%s -loop 1 -i %s -i %s -c:v libx264 -tune stillimage -c:a libfdk_aac -pix_fmt yuv420p -shortest %s' % (
    FFMPEG, image_file, audio_file, video_file)
    os.system(command)

## END OF Inlined ffmpeg module


def extract_timings(bbb_version):
    doc = minidom.parse(events_file)
    dictionary = {}
    total_length = 0
    j = 0

    for image in doc.getElementsByTagName('image'):
        path = image.getAttribute('xlink:href')

        if j == 0 and '2.0.0' > bbb_version:
            path = u'/usr/local/bigbluebutton/core/scripts/logo.png'
            j += 1

        in_times = str(image.getAttribute('in')).split(' ')
        out_times = image.getAttribute('out').split(' ')

        temp = float(out_times[len(out_times) - 1])
        if temp > total_length:
            total_length = temp

        occurrences = len(in_times)
        for i in range(occurrences):
            dictionary[float(in_times[i])] = temp_dir + str(path)

    return dictionary, total_length


def create_slideshow(dictionary, length, result, bbb_version):
    video_list = 'video_list.txt'
    f = open(video_list, 'w')

    times = dictionary.keys()
    times.sort()

    ffmpeg_webm_to_mp4(SOURCE_DESKSHARE, TMP_DESKSHARE_FILE)

    print >> sys.stderr, "-=create_slideshow=-"
    for i, t in enumerate(times):
        # print >> sys.stderr, (i, t)

        # if i < 1 and '2.0.0' > bbbversion:
        #   continue

        tmp_name = '%d.mp4' % i
        tmp_ts_name = '%d.ts' % i
        image = dictionary[t]

        if i == len(times) - 1:
            duration = length - t
        else:
            duration = times[i + 1] - t

        out_file = temp_dir + tmp_name
        out_ts_file = temp_dir + tmp_ts_name

        if "deskshare.png" in image:
            print >> sys.stderr, (0, i, t, duration)
            ffmpeg_trim_video_by_seconds(TMP_DESKSHARE_FILE, t, duration, out_file)
            ffmpeg_mp4_to_ts(out_file, out_ts_file)
        else:
            print >> sys.stderr, (1, i, t, duration)
            ffmpeg_create_video_from_image(image, duration, out_ts_file)

        f.write('file ' + out_ts_file + '\n')
    f.close()

    ffmpeg_concat_videos(video_list, result)
    os.remove(video_list)


def get_presentation_dims(presentation_name):
    doc = minidom.parse(events_file)
    images = doc.getElementsByTagName('image')

    for el in images:
        name = el.getAttribute('xlink:href')
        pattern = presentation_name
        if re.search(pattern, name):
            height = int(el.getAttribute('height'))
            width = int(el.getAttribute('width'))
            return height, width


def rescale_presentation(new_height, new_width, dictionary, bbb_version):
    times = dictionary.keys()
    times.sort()
    for i, t in enumerate(times):
        # ?
        #print >> sys.stderr, "_rescale_presentation_"
        #print >> sys.stderr, (i, t)

        if i < 1 and '2.0.0' > bbb_version:
            continue

        #print >> sys.stderr, "_rescale_presentation_after_skip_"
        #print >> sys.stderr, (i, t)

        ffmpeg_rescale_image(dictionary[t], new_height, new_width, dictionary[t])


def check_presentation_dims(dictionary, dims, bbb_version):
    names = dims.keys()
    heights = []
    widths = []

    for i in names:
        temp = dims[i]
        heights.append(temp[0])
        widths.append(temp[1])

    height = max(heights)
    width = max(widths)

    dim1 = height % 2
    dim2 = width % 2

    new_height = height
    new_width = width

    if dim1 or dim2:
        if dim1:
            new_height += 1
        if dim2:
            new_width += 1

    rescale_presentation(new_height, new_width, dictionary, bbb_version)


def prepare(bbb_version):
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)

    if not os.path.exists('audio'):
        global audio_path
        audio_path = temp_dir + 'audio/'
        os.mkdir(audio_path)
        ffmpeg_extract_audio_from_video(SOURCE_WEBCAMS, audio_path + 'audio.ogg')

    shutil.copytree("presentation", temp_dir + "presentation")
    dictionary, length = extract_timings(bbb_version)
    # debug
    print >> sys.stderr, "dictionary"
    print >> sys.stderr, (dictionary)
    print >> sys.stderr, "length"
    print >> sys.stderr, (length)
    dims = get_different_presentations(dictionary)
    # debug
    print >> sys.stderr, "dims"
    print >> sys.stderr, (dims)
    check_presentation_dims(dictionary, dims, bbb_version)
    return dictionary, length, dims


def get_different_presentations(dictionary):
    times = dictionary.keys()
    print >> sys.stderr, "times"
    print >> sys.stderr, (times)
    presentations = []
    dims = {}
    for t in times:
        # ?if t < 1:
        # ?    continue

        name = dictionary[t].split("/")[-1]
        # debug
        print >> sys.stderr, "name"
        print >> sys.stderr, (name)
        if name not in presentations:
            presentations.append(name)
            dims[name] = get_presentation_dims(name)

    return dims


def cleanup():
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)


def copy_mp4(result, dest):
    if os.path.exists(result):
        shutil.copy2(result, dest)


def bbbversion():
    global bbb_ver
    bbb_ver = 0
    s_events = minidom.parse(source_events)
    for event in s_events.getElementsByTagName('recording'):
        bbb_ver = event.getAttribute('bbb_version')
    return bbb_ver


def main():
    ffmpeg_set_logfile(LOGFILE)
    if not os.path.exists(LOGS):
        os.makedirs(LOGS)
    sys.stderr = open(LOGFILE, 'a')
    print >> sys.stderr, "\n<-------------------" + time.strftime("%c") + "----------------------->\n"

    bbb_version = bbbversion()
    print >> sys.stderr, "bbb_version: " + bbb_version

    os.chdir(source_dir)

    dictionary, length, dims = prepare(bbb_version)

    audio = audio_path + 'audio.ogg'
    audio_trimmed = temp_dir + 'audio_trimmed.m4a'
    left_part = target_dir + 'left.mp4'
    result = target_dir + 'meeting.mp4'
    slideshow = temp_dir + 'slideshow.mp4'

    try:
        create_slideshow(dictionary, length, slideshow, bbb_version)
        ffmpeg_trim_audio_start(dictionary, length, audio, audio_trimmed)
        ffmpeg_mux_slideshow_audio(slideshow, audio_trimmed, left_part)
        ffmpeg_dual_view_from(left_part, SOURCE_WEBCAMS, result)
        copy_mp4(result, source_dir + "master.mp4")
    finally:
        print >> sys.stderr, "Cleaning up temp files..."
        cleanup()
        print >> sys.stderr, "Done"


if __name__ == "__main__":
    main()
