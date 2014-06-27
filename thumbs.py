import subprocess
import json
import os

command = 'ffmpeg -ss %s -i %s -vf "select=gt(scene\,0.4)" -r 1 -frames:v 1 %s'
input_file = 'original.mp4'
output_file = 'thumb_%s.jpg'
num_thumbs = 10

base_dir = os.path.dirname(os.path.realpath(__file__))
input_filepath = os.path.join(base_dir, input_file)

def getLength(filename):
  result = subprocess.Popen(["ffprobe", '-v', 'quiet', '-hide_banner', '-show_streams', '-print_format', 'json', filename,], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
  info = json.loads(result.stdout.read())
  return int(float(info['streams'][0]['duration']))

duration = getLength(input_filepath)
duration_part = duration/num_thumbs

for i in range(0,num_thumbs):
  cur_command = command % (i*duration_part, input_file, output_file % i)
  print cur_command

  p = subprocess.Popen(cur_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  output = p.communicate()[0]

  print output
