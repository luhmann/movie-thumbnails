import subprocess
import json
import os
import argparse
import cv2
import shutil
import math
import colorsys
from dominantColor import colorz
from operator import itemgetter
from PIL import Image, ImageFilter, ImageStat, ImageChops

parser = argparse.ArgumentParser(description='Tries to find a good thumbnail for a video')
parser.add_argument('--src', dest='src', default=None, help='The source video')
args = parser.parse_args()

command = 'ffmpeg -ss %s -i %s -vf "select=gt(scene\,0.4)" -r 1 -frames:v 1 %s'
input_file = args.src
output_file = 'thumb_%s.tif'
num_thumbs = 10
num_out = 3
thumbs = {}
score_points = {
    'face': 100,
    'sat' : 100,
    'sharpness': 150,
    'bri': 50,
    'con': 100
}

base_dir = os.path.dirname(os.path.realpath(__file__))
input_filepath = os.path.join(base_dir, input_file)
work_folder = os.path.join(base_dir, 'tmp')
analyze_folder = os.path.join(work_folder, 'analyze')
output_folder = os.path.join(base_dir, 'out')


def get_length(filename):
    result = subprocess.Popen(
        ["ffprobe", '-v', 'quiet', '-hide_banner', '-show_streams', '-print_format', 'json', filename, ],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    info = json.loads(result.stdout.read())
    return int(float(info['streams'][0]['duration']))


def prepare_folder(folder):
    shutil.rmtree(folder)
    os.makedirs(folder)
    os.makedirs(analyze_folder)
    if os.path.isdir(output_folder) is False:
        os.makedirs(output_folder)


def generate_thumbs(num, output_file):
    duration = get_length(input_filepath)
    duration_part = duration / num_thumbs

    for i in range(0, num):
        cur_filename = (output_file % i)
        cur_filepath = os.path.join(work_folder, cur_filename)
        thumbs[cur_filepath] = { 'score': 0 }
        cur_command = command % (i * duration_part, input_file, cur_filepath)
        print cur_command

        p = subprocess.Popen(cur_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = p.communicate()[0]

        print output

# Returns overall perceived brightness of the image, as defined in luma
def brightness(stat):
   r,g,b = stat.mean
   return math.sqrt(0.241 * (r ** 2) + 0.691 * (g ** 2) + 0.068 * (b ** 2)) / 255

def saturation_dominant_colors(image):
    copy = image
    colors = colorz(copy)

    saturation_indicator = 0

    for color in colors:
        color = [float(x)/255 for x in color]
        hls_color = colorsys.rgb_to_hls(color[0], color[1], color[2])
        luminance = hls_color[1] * 100
        saturation = hls_color[2] * 100
        saturation_indicator += luminance + saturation

    print saturation_indicator
    return saturation_indicator / 600


def has_face(image):
    """
        image is expected to be a opencv image
    """
    cascade = cv2.CascadeClassifier(os.path.join(base_dir, 'lib', 'haarcascade_frontalface_alt.xml'))
    rects = cascade.detectMultiScale(image, 1.3, 4, cv2.cv.CV_HAAR_SCALE_IMAGE, (20, 20))
    return len(rects) > 0

def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)

def calculate_contrast(stats):
    return stats.extrema[0][0]/255 + stats.extrema[0][1]/255 + stats.stddev[0]/255

def analyze():
    print thumbs
    for file, info in thumbs.iteritems():
        if os.path.isfile(file):
            filename = os.path.splitext(os.path.basename(file))[0]
            print filename

            # open image
            im = Image.open(file)

            # extract original size so we can add it back again
            info['width'] = im.size[0]
            info['height'] = im.size[1]
            print 'Initial Score: %s' % info['score']

            # crop all black borders
            im = trim(im)
            cv_handle = cv2.imread(file, 0)

            # if the crop left nothing left (one colored image, continue)
            if im is None:
                continue

            # # edges = cv2.Canny(cv_handle, 100, 200)
            # hist = cv2.calcHist([cv_handle],[0],None,[256],[0,256])
            # #print hist
            # # cv2.imwrite(os.path.join(analyze_folder, filename + '_canny' +'.jpg'), edges)

            # check if image contains a face
            if has_face(cv_handle) is True:
                info['score'] += score_points['face']
                print 'Has Face - Score: %s' % info['score']

            # check saturation of dominant colors
            sat = saturation_dominant_colors(im) * score_points['sat']
            print 'Saturation Score %s' % sat
            info['score'] += sat

            # check perceived brightness
            v = ImageStat.Stat(im)
            b = brightness(v) * score_points['bri']
            print 'Brightness score: %s' % b
            info['score'] += b

            # check sharpness
            im = im.convert('L')
            bw = ImageStat.Stat(im)

            im = im.filter(ImageFilter.FIND_EDGES)
            edges = ImageStat.Stat(im)
            sha = edges.rms[0]/100 * score_points['sharpness']
            print 'Sharpness score: %s' % sha
            info['score'] += sha

            # check contrast
            con = calculate_contrast(bw) * score_points['con']
            print 'Contrast score: %s' % con
            info['score'] += con

            print '# Score: %s' % info['score']
            #im.save(os.path.join(analyze_folder, filename + '.jpg'), 'JPEG')

def output():
    best = sorted(thumbs.items(),key = lambda x :x[1]['score'],reverse = True)
    print best

    for i in range(0, num_out):
        thumb = best[i][0]
        name = input_file + '_' + str(i) + '_' + os.path.basename(thumb) + '.jpg'

        if os.path.isfile(thumb) is False:
            continue

        im = Image.open(thumb)
        im.save(os.path.join(output_folder, name), 'JPEG')


def fire():
    prepare_folder(work_folder)
    generate_thumbs(num_thumbs, output_file)
    # analyze()
    output()

fire()
