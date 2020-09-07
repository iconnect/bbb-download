__author__ = 'CreateWebinar.com'

# Python wrapper around the ffmpeg utility
import os
import shutil

FFMPEG = 'ffmpeg -loglevel verbose '
VID_ENCODER = 'libx264'


def set_logfile(file):
    global logfile
    logfile = file


def mux_slideshow_audio(video_file, audio_file, out_file):
    command = '%s -i %s -i %s -map 0 -map 1 -codec copy -shortest %s 2>> %s' % (
        FFMPEG, video_file, audio_file, out_file, logfile)
    os.system(command)


def extract_audio_from_video(video_file, out_file):
    command = '%s -i %s -ab 160k -ac 2 -ar 44100 -vn %s 2>> %s' % (FFMPEG, video_file, out_file, logfile)
    os.system(command)

# "-filter_complex '[2:v]setpts=PTS-STARTPTS,pad=iw*2:ih:color=white[l];[3:v]setpts=PTS-STARTPTS[r];[l][r]overlay=x=W-w:shortest=1[vout] -map [vout] "


def dual_view_from(left_part, right_part, out_file):
    if os.path.exists(right_part):
        left_filter = 'setpts=PTS-STARTPTS,pad=iw*2:ih:color=white'
        right_filter = 'scale2ref=w=iw/2:h=ih'
        combined_filter = 'overlay=x=W-w:shortest=1'
        filter_complex = '[0:v]%s[ref];[1:v]setpts=PTS-STARTPTS[2nd];[2nd][ref]%s[r][l];[l][r]%s[vout]' % (left_filter, right_filter, combined_filter)
        command = '%s -i %s -i %s -filter_complex "%s" -map [vout] -map 0:a -aspect 32:9 %s 2>> %s' % (FFMPEG, left_part, right_part, filter_complex, out_file, logfile)
        os.system(command)

def create_video_from_image(image, duration, out_file):
    print "*************** create_video_from_image ******************"
    print image, "\n", duration, "\n", out_file
    command = '%s -loop 1 -r 5 -f image2 -i %s -c:v %s -t %s -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s 2>> %s' % (
        FFMPEG, image, VID_ENCODER, duration, out_file, logfile)
    os.system(command)


def concat_videos(video_list, out_file):
    command = '%s -f concat -safe 0 -i %s -c copy %s 2>> %s' % (FFMPEG, video_list, out_file, logfile)
    os.system(command)


def mp4_to_ts(input, output):
    command = '%s -i %s -c copy -bsf:v h264_mp4toannexb -f mpegts %s 2>> %s' % (FFMPEG, input, output, logfile)
    os.system(command)


def concat_ts_videos(input, output):
    command = '%s -i %s -c copy -bsf:a aac_adtstoasc %s 2>> %s' % (FFMPEG, input, output, logfile)
    os.system(command)


def rescale_image(image, height, width, out_file):
    if height < width:
        command = '%s -i %s -vf pad=%s:%s:0:oh/2-ih/2 %s -y 2>> %s' % (FFMPEG, image, width, height, out_file, logfile)
    else:
        command = '%s -i %s -vf pad=%s:%s:0:ow/2-iw/2 %s -y 2>> %s' % (FFMPEG, image, width, height, out_file, logfile)

    os.system(command)


def trim_video(video_file, start, end, out_file):
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


def trim_video_by_seconds(video_file, start, end, out_file):
    command = '%s -ss %s -i %s -c copy -t %s %s 2>> %s' % (FFMPEG, start, video_file, end, out_file, logfile)
    os.system(command)


def trim_audio(audio_file, start, end, out_file):
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


def trim_audio_start(dictionary, length, full_audio, audio_trimmed):
    times = dictionary.keys()
    times.sort()
    trim_audio(full_audio, int(round(times[0])), int(length), audio_trimmed)


def trim_video_start(dictionary, length, full_vid, video_trimmed):
    times = dictionary.keys()
    times.sort()
    trim_video(full_vid, int(round(times[2])), int(length), video_trimmed)


def mp3_to_aac(mp3_file, aac_file):
    command = '%s -i %s -c:a aac %s 2>> %s' % (FFMPEG, mp3_file, aac_file, logfile)
    os.system(command)


def webm_to_mp4(webm_file, mp4_file):
    command = '%s -i %s -qscale 0 %s 2>> %s' % (FFMPEG, webm_file, mp4_file, logfile)
    os.system(command)


def audio_to_video(audio_file, image_file, video_file):
    command = '%s -loop 1 -i %s -i %s -c:v libx264 -tune stillimage -c:a libfdk_aac -pix_fmt yuv420p -shortest %s' % (
    FFMPEG, image_file, audio_file, video_file)
    os.system(command)
