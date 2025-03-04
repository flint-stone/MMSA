"""
From: https://github.com/thuiar/Self-MM
Paper: Learning Modality-Specific Representations with Self-Supervised Multi-Task Learning for Multimodal Sentiment Analysis
"""
# self supervised multimodal multi-task learning network

import torch
import torch.nn as nn
import torch.nn.functional as F
import time
from torch.nn.utils.rnn import pack_padded_sequence
import numpy as np

from ..subNets import BertTextEncoder

__all__ = ['SELF_MM']

class SELF_MM(nn.Module):
    def __init__(self, args):
        super(SELF_MM, self).__init__()
        # text subnets
        self.aligned = args.need_data_aligned
        self.text_model = BertTextEncoder(use_finetune=args.use_finetune, transformers=args.transformers, pretrained=args.pretrained)

        # audio-vision subnets
        audio_in, video_in = args.feature_dims[1:]
        self.audio_model = AuViSubNet(audio_in, args.a_lstm_hidden_size, args.audio_out, \
                            num_layers=args.a_lstm_layers, dropout=args.a_lstm_dropout)
        self.video_model = AuViSubNet(video_in, args.v_lstm_hidden_size, args.video_out, \
                            num_layers=args.v_lstm_layers, dropout=args.v_lstm_dropout)

        # the post_fusion layers
        self.post_fusion_dropout = nn.Dropout(p=args.post_fusion_dropout)
        self.post_fusion_layer_1 = nn.Linear(args.text_out + args.video_out + args.audio_out, args.post_fusion_dim)
        self.post_fusion_layer_2 = nn.Linear(args.post_fusion_dim, args.post_fusion_dim)
        self.post_fusion_layer_3 = nn.Linear(args.post_fusion_dim, 1)

        # the classify layer for text
        self.post_text_dropout = nn.Dropout(p=args.post_text_dropout)
        self.post_text_layer_1 = nn.Linear(args.text_out, args.post_text_dim)
        self.post_text_layer_2 = nn.Linear(args.post_text_dim, args.post_text_dim)
        self.post_text_layer_3 = nn.Linear(args.post_text_dim, 1)

        # the classify layer for audio
        self.post_audio_dropout = nn.Dropout(p=args.post_audio_dropout)
        self.post_audio_layer_1 = nn.Linear(args.audio_out, args.post_audio_dim)
        self.post_audio_layer_2 = nn.Linear(args.post_audio_dim, args.post_audio_dim)
        self.post_audio_layer_3 = nn.Linear(args.post_audio_dim, 1)

        # the classify layer for video
        self.post_video_dropout = nn.Dropout(p=args.post_video_dropout)
        self.post_video_layer_1 = nn.Linear(args.video_out, args.post_video_dim)
        self.post_video_layer_2 = nn.Linear(args.post_video_dim, args.post_video_dim)
        self.post_video_layer_3 = nn.Linear(args.post_video_dim, 1)

    def forward(self, text, audio, video, precision="tf32"):
        audio, audio_lengths = audio
        video, video_lengths = video

        batch_size = 0
        device = None
        if text is not None:
            batch_size = text.size(dim=0)
            device = text.device
        elif audio is not None:
            batch_size = audio.size(dim=0)
            device = audio.device
        else:
            batch_size = video.size(dim=0)
            device = video.device
            
        #mask_len = torch.sum(text[:,1,:], dim=1, keepdim=True)
        text_lengths = batch_size #mask_len.squeeze(1).int().detach().cpu()
        # print(f"handling time audio {audio.size()} {audio_lengths} video {video.size()} {video_lengths} text {text.size()} {text_lengths}")
       
        #start = time.time()
        datatype = (torch.half if precision == "fp16" else torch.float32)
        print(f"data type {audio.dtype} {video.dtype} {text.dtype}")
        if text is None:
            text = torch.zeros([batch_size, 768], dtype=datatype, device=device)
        else:
            text = self.text_model(text)[:,0,:]
        if self.aligned:
            audio = self.audio_model(audio, text_lengths)
            # audio = torch.zeros([text.data.shape[0], text_lengths], dtype=torch.float32, device=text.device)
            video = self.video_model(video, text_lengths)
            # video = torch.zeros([text.data.shape[0], 32], dtype=torch.float32, device=text.device)
        else:
            if audio is None:
                audio = torch.zeros([batch_size, 16], dtype=datatype, device=device)
            else:
                audio = self.audio_model(audio, audio_lengths)
            if video is None:
                video = torch.zeros([batch_size, 32], dtype=datatype, device=device)
            else:
                video = self.video_model(video, video_lengths)
        #print(f"batch size {batch_size}")
        # text = torch.zeros([video.data.shape[0], 768], dtype=torch.float32, device=text.device)
        # print(f"handling time {time.time() - start} audio {audio.size()} video {video.size()} text {text.size()} text_lengths {len(text_lengths.data)} audio_lengths {len(audio_lengths.data)} video_lengths {len(video_lengths.data)} batch_size {batch_size}")
        #handling time 0.023541688919067383 torch.Size([16, 16]) torch.Size([16, 32]) torch.Size([16, 768]) torch.float32
        # print(f"time average {np.mean(times_infer)} std {np.std(times_infer)} mem average {np.mean(mem_peaks)} B std {np.std(mem_peaks)} B")
        # fusion
        fusion_h = torch.cat([text, audio, video], dim=-1)
        fusion_h = self.post_fusion_dropout(fusion_h)
        fusion_h = F.relu(self.post_fusion_layer_1(fusion_h), inplace=False)
        # # text
        text_h = self.post_text_dropout(text)
        text_h = F.relu(self.post_text_layer_1(text_h), inplace=False)
        # audio
        audio_h = self.post_audio_dropout(audio)
        audio_h = F.relu(self.post_audio_layer_1(audio_h), inplace=False)
        # vision
        video_h = self.post_video_dropout(video)
        video_h = F.relu(self.post_video_layer_1(video_h), inplace=False)

        # classifier-fusion
        x_f = F.relu(self.post_fusion_layer_2(fusion_h), inplace=False)
        output_fusion = self.post_fusion_layer_3(x_f)

        # classifier-text
        x_t = F.relu(self.post_text_layer_2(text_h), inplace=False)
        output_text = self.post_text_layer_3(x_t)

        # classifier-audio
        x_a = F.relu(self.post_audio_layer_2(audio_h), inplace=False)
        output_audio = self.post_audio_layer_3(x_a)

        # classifier-vision
        x_v = F.relu(self.post_video_layer_2(video_h), inplace=False)
        output_video = self.post_video_layer_3(x_v)

        res = {
            'M': output_fusion, 
            'T': output_text,
            'A': output_audio,
            'V': output_video,
            'Feature_t': text_h,
            'Feature_a': audio_h,
            'Feature_v': video_h,
            'Feature_f': fusion_h,
        }
        return res

class AuViSubNet(nn.Module):
    def __init__(self, in_size, hidden_size, out_size, num_layers=1, dropout=0.2, bidirectional=False):
        '''
        Args:
            in_size: input dimension
            hidden_size: hidden layer dimension
            num_layers: specify the number of layers of LSTMs.
            dropout: dropout probability
            bidirectional: specify usage of bidirectional LSTM
        Output:
            (return value in forward) a tensor of shape (batch_size, out_size)
        '''
        super(AuViSubNet, self).__init__()
        self.rnn = nn.LSTM(in_size, hidden_size, num_layers=num_layers, dropout=dropout, bidirectional=bidirectional, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.linear_1 = nn.Linear(hidden_size, out_size)

    def forward(self, x, lengths):
        '''
        x: (batch_size, sequence_len, in_size)
        '''
        packed_sequence = pack_padded_sequence(x, lengths, batch_first=True, enforce_sorted=False)
        _, final_states = self.rnn(packed_sequence)
        h = self.dropout(final_states[0].squeeze(0))
        y_1 = self.linear_1(h)
        return y_1
