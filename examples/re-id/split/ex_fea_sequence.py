#from classify_video import *
import numpy as np
import glob
caffe_root = '../../../'
import sys
sys.path.insert(0,caffe_root + 'python')
import caffe
caffe.set_mode_gpu()
caffe.set_device(1)
import pickle
import h5py
import random
from scipy.io import loadmat

def initialize_transformer(image_mean, is_flow):
  shape = (10, 3, 160, 60)
  transformer = caffe.io.Transformer({'data': shape})
  channel_mean = np.zeros((3,160,60))
  for channel_index, mean_val in enumerate(image_mean):
    channel_mean[channel_index, ...] = mean_val
  transformer.set_mean('data', channel_mean)
  transformer.set_raw_scale('data', 255)
  transformer.set_channel_swap('data', (2, 1, 0))
  transformer.set_transpose('data', (2, 0, 1))
  transformer.set_is_flow('data', is_flow)
  return transformer

RGB_frames = '/media/yanyichao/5A487B64487B3DB7/re_id/prid/data_lstm/'
color_path = '/media/yanyichao/5A487B64487B3DB7/re_id/prid/fea/lbp_color/'
fea_dim = 58950
#RGB_frames = '/home/yanyichao/data/cub_org/train_test_filter_new_org_sort_vgg_bbox/'
ucf_mean_RGB = np.zeros((3,1,1))
#ucf_mean_flow = np.zeros((3,1,1))
#ucf_mean_flow[:,:,:] = 128
ucf_mean_RGB[0,:,:] = 104
ucf_mean_RGB[1,:,:] = 117
ucf_mean_RGB[2,:,:] = 123
transformer_RGB = initialize_transformer(ucf_mean_RGB, False)

lstm_model = 'deploy_lstm.prototxt'
RGB_lstm = 'models/_iter_25000.caffemodel'
RGB_lstm_net =  caffe.Net(lstm_model, RGB_lstm, caffe.TEST)

def LRCN_ex_fea(frames_sequence, net, transformer,mat_path, num_frames, is_flow):
  clip_length = 10
  offset = 1
  output_predictions = np.zeros((clip_length,512))
  color_fea_input = loadmat(mat_path)
  color_fea_r = color_fea_input['tmp_fea']
  caffe_in = np.zeros((clip_length, fea_dim))
  clip_clip_markers = np.ones((clip_length,1,1,1))
  clip_clip_markers[0:1,:,:,:] = 0
  f = random.randint(0,1)
  rand_frame = int(random.random()*(num_frames-clip_length)+1)
  for i in range(1):
    k=0
    for j in range(rand_frame, rand_frame+clip_length):
      caffe_in[k] = color_fea_r[j]
      k=k+1
    out = net.forward_all(color_fea=caffe_in.reshape((clip_length, fea_dim, 1, 1)), clip_markers=np.array(clip_clip_markers))
    output_predictions[i:i+clip_length] = np.mean(out['lstm1'],1)
  return output_predictions

video_list = 'train_lstm.txt'
f = open(video_list, 'r')
f_lines = f.readlines()
f.close()
true_pred = 0
all_test = 0
all_fea = np.zeros((len(f_lines), 10,512))
itr = 20
for it in range(itr):
    for ix, line in enumerate(f_lines):
        video = line.split(' ')[0]
        l = int(line.split(' ')[1])
        video1 = line.split(' ')[0].split('/')[1]
        frames = glob.glob('%s%s/*.png' %(RGB_frames, video))
        num_frames = len(frames)
        frames_sequence = frames[0][0:-9] + '_%04d.png'
        color_mat_path = color_path+video1+'.mat'
        print "processing the %d th image" % ix
        tmp_fea = \
             LRCN_ex_fea(frames_sequence, RGB_lstm_net, transformer_RGB,color_mat_path, num_frames, False)
    #np.save("/home/yanyichao/data/cub_org/list/test_ss_new/tmp_fea.npy",tmp_fea)
        all_fea[ix] = tmp_fea
    f_all = h5py.File('train_25k_'+str(it)+'.h5', "w")
    f_all.create_dataset('train_set', data = all_fea)
    f_all.close()
