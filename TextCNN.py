from BasicModule import BasicModule
import torch as t
import numpy as np
from torch import nn

kernel_sizes =  [1,3,5]
kernel_sizes2 = [1,3,5]

class MultiCNNTextBNDeep(BasicModule): 
    def __init__(self, vocab_size, embedding_dim, content_dim, pooling_out_dim,linear_hidden_size,num_classes):
        super(MultiCNNTextBNDeep, self).__init__()
        self.model_name = 'MultiCNNTextBNDeep'
        #self.opt=opt
        self.encoder = nn.Embedding(vocab_size,embedding_dim)

        content_convs = [ nn.Sequential(
                                nn.Conv1d(in_channels = embedding_dim,
                                        out_channels = content_dim,
                                        kernel_size = kernel_size),
                                nn.BatchNorm1d(content_dim),
                                nn.ReLU(inplace=True),

                                nn.Conv1d(in_channels = content_dim,
                                        out_channels =content_dim,
                                        kernel_size = kernel_size),
                                nn.BatchNorm1d(content_dim),
                                nn.ReLU(inplace=True),
                                nn.AdaptiveAvgPool1d(pooling_out_dim)
                            )
            for kernel_size in kernel_sizes ]

        self.content_convs = nn.ModuleList(content_convs)

        self.fc = nn.Sequential(
            nn.Linear(len(kernel_sizes)*pooling_out_dim*content_dim,linear_hidden_size),
            #nn.BatchNorm1d(linear_hidden_size),
            nn.ReLU(inplace=True),
            nn.Linear(linear_hidden_size,num_classes)
        )
        

        #if embedding_path:
            #self.encoder.weight.data.copy_(t.from_numpy(np.load(embedding_path)['vector']))

    def forward(self,content):
        content = self.encoder(content)
        content_out = [ content_conv(content.permute(0,2,1)) for content_conv in self.content_convs]
        conv_out = t.cat(content_out,dim=1)
        #print(conv_out.size())
        reshaped = conv_out.view(conv_out.size(0), -1)
        logits = self.fc((reshaped))
        return logits
 
if __name__ == '__main__':
    m = MultiCNNTextBNDeep(30000,50,256,512, 256,5)
    #title = t.autograd.Variable(t.arange(0,500).view(1,500)).long()
    print(t.arange(0,1000).view(4,250))
    content = t.autograd.Variable(t.arange(0,1000).view(4,250)).long()
    o = m(content)
    print(o.size())