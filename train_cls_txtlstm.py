from __future__ import print_function

import os
import argparse

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.backends.cudnn as cudnn
from torch.autograd import Variable
import numpy as np
import pandas as pd
import time

import dataloader
import TextLSTM
import torch.utils.data as data

parser = argparse.ArgumentParser(description='PyTorch TextCNN Training')
parser.add_argument('--lr', default=0.1, type=float, help='learning rate')
parser.add_argument('--resume', '-r', action='store_true', help='resume from checkpoint')
parser.add_argument('--mname',default='TextLSTM-ICO', type=str, help='model name for save')
parser.add_argument('--csvdir',default='./wp_analysis.csv', type=str, help='for ICO white paper list')
parser.add_argument('--article_dir',default='./txt', type=str, help='index direction for save')
parser.add_argument('--vocab_size',default=21224, type=str, help='vocab size')
parser.add_argument('--emb_dim',default=50, type=str, help='emb_dim size')
parser.add_argument('--hidden_size',default=500, type=str, help='hiddensize')
parser.add_argument('--num_layers',default=3, type=str, help='num of LSTM layers')
parser.add_argument('--linear_dim',default=512, type=str, help='linear hidden size')
parser.add_argument('--num_classes',default=5, type=str, help='emb_dim size')
args = parser.parse_args()

#device = 'cuda' if torch.cuda.is_available() else 'cpu'
device = 'cpu'
best_acc = 0
start_epoch = 0
train_data = dataloader.Myarticles(args.csvdir,args.article_dir,validation=False)
test_data = dataloader.Myarticles(args.csvdir,args.article_dir,validation=True)

train_loader =data.DataLoader(train_data,batch_size=1,shuffle=True)
test_loader =data.DataLoader(test_data,batch_size=1,shuffle=False)

print('==> Loading Network structure..\n')
args.vocab_size = len(train_data.word2idx)
net = TextLSTM.LSTMText(args.vocab_size,args.emb_dim,args.hidden_size,args.num_layers, args.linear_dim,args.num_classes)
net = net.to(device)

print('==> Loading cuda...\n')

criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=args.lr, momentum=0.9, weight_decay=1e-4)

savepath='./train/'+str(args.mname)
if not os.path.exists(savepath):
    os.makedirs(savepath)

def train(epoch):
    print('\nEpoch: %d' % epoch)
    net.train()
    train_loss = 0
    correct = 0
    total = 0
    start_time=time.time()
    for batch_idx, (inputs, targets) in enumerate(train_loader):
        inputs, targets = inputs.to(device), targets.long().to(device)
        optimizer.zero_grad()
        outputs = net(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        train_loss += loss.item()
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()
        accuracy=100.*correct/total
        #progress_bar(batch_idx, len(trainloader), 'Loss: %.3f | Acc: %.3f%% (%d/%d)'
        #    % (train_loss/(batch_idx+1), accuracy, correct, total))
        print('batch %s of total batch %s' % (batch_idx, len(train_loader)), 'Loss: %.3f | Acc: %.3f%% (%d/%d)' % (train_loss/(batch_idx+1), accuracy, correct, total))

    end_time=time.time()
    epoch_time=end_time-start_time
    data=[epoch,accuracy,train_loss/(batch_idx+1),epoch_time]
    print('trainloss:{},accuracy:{},time_used:{}'.format(train_loss/(batch_idx+1),accuracy,epoch_time))

    state = {
            'net': net.state_dict(),
            'acc': accuracy,
            'epoch': epoch,
        }

    return data


def test(epoch):
    global best_acc
    net.eval()
    test_loss = 0
    correct = 0
    total = 0
    start_time=time.time()
    for batch_idx, (inputs, targets) in enumerate(test_loader):
        inputs, targets = inputs.to(device), targets.to(device)
        outputs = net(inputs)
        loss = criterion(outputs, targets)

        test_loss += loss.item()
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()
        accuracy=100.*correct/total

    end_time=time.time()
    epoch_time=end_time-start_time
    print('batch %s of total batch %s' % (batch_idx, len(test_loader)), 'Loss: %.3f | Acc: %.3f%% (%d/%d)' % (test_loss/(batch_idx+1), accuracy, correct, total))
    #progress_bar(batch_idx, len(testloader), 'Loss: %.3f | Acc: %.3f%% (%d/%d)'
    #        % (test_loss/(batch_idx+1), 100.*correct/total, correct, total))

    data=[epoch,accuracy,test_loss/(batch_idx+1),epoch_time]
    print('testloss:{},accuracy:{},time_used:{}'.format(test_loss/(batch_idx+1),accuracy,epoch_time))
    # Save checkpoint.
    acc = 100.*correct/total
    if acc > best_acc:
        print('Saving..best_record')
        state = {
            'net': net.state_dict(),
            'acc': acc,
            'epoch': epoch,
        }
        if not os.path.isdir('checkpoint'):
            os.mkdir('checkpoint')
        savepath='./train/'+str(args.mname)+'/best_check.plk'
        torch.save(state, savepath)
        best_acc = acc
    return data

a=[1,2,3,4]
trainnp=np.array(a)
testnp=np.array(a)

for epoch in range(start_epoch, start_epoch+90):
    nd=train(epoch)
    trainnp=np.vstack((trainnp,np.array(nd)))
    ed=test(epoch)
    testnp=np.vstack((testnp,np.array(ed)))


savepath='./train/'+str(args.mname)+'train.csv'
train_data=pd.DataFrame(trainnp,columns=['epoch','accuracy','loss','epoch_time'])
train_data.to_csv(savepath)
savepath='./train/'+str(args.mname)+'test.csv'
test_data=pd.DataFrame(testnp,columns=['epoch','accuracy','loss','epoch_time'])
test_data.to_csv(savepath)

print('\n\nadjust learning rate to 0.01')
#learning rate change
args.lr=0.01

criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=args.lr, momentum=0.9, weight_decay=1e-4)

for epoch in range(90+start_epoch, 90+start_epoch+60):
    nd=train(epoch)
    trainnp=np.vstack((trainnp,np.array(nd)))
    ed=test(epoch)
    testnp=np.vstack((testnp,np.array(ed)))

savepath='./train/'+str(args.mname)+'train.csv'
train_data=pd.DataFrame(trainnp,columns=['epoch','accuracy','loss','epoch_time'])
train_data.to_csv(savepath)
savepath='./train/'+str(args.mname)+'test.csv'
test_data=pd.DataFrame(testnp,columns=['epoch','accuracy','loss','epoch_time'])
test_data.to_csv(savepath)

print('best accuracy is :{}'.format(best_acc))