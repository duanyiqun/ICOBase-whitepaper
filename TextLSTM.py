from BasicModule import BasicModule
import torch as t
import numpy as np
from torch import nn


def kmax_pooling(x, dim, k):
    index = x.topk(k, dim = dim)[1].sort(dim = dim)[0]
    return x.gather(dim, index)

class LSTMText(BasicModule): 
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_layers, linear_hidden_size, num_classes):
        super(LSTMText, self).__init__()
        self.model_name = 'LSTMText'
        self.kmax_pooling_dim = 200
        self.encoder = nn.Embedding(vocab_size, embedding_dim)
        self.content_lstm =nn.LSTM(  input_size = embedding_dim,
                            hidden_size = hidden_size,
                            num_layers = num_layers,
                            bias = True,
                            batch_first = False,
                            # dropout = 0.5,
                            bidirectional = True
                            )

        # self.dropout = nn.Dropout()
        self.fc = nn.Sequential(
            nn.Linear(self.kmax_pooling_dim*(hidden_size*2),linear_hidden_size),
            #nn.BatchNorm1d(linear_hidden_size),
            nn.ReLU(inplace=True),
            nn.Linear(linear_hidden_size,num_classes)
        )
        # self.fc = nn.Linear(3 * (opt.title_dim+opt.content_dim), opt.num_classes)
        #if opt.embedding_path:
            #self.encoder.weight.data.copy_(t.from_numpy(np.load(opt.embedding_path)['vector']))
 
    def forward(self, content):
        content = self.encoder(content)
        content_out = self.content_lstm(content.permute(1,0,2))[0].permute(1,2,0)
        content_conv_out = kmax_pooling((content_out),2,self.kmax_pooling_dim)
        #conv_out = t.cat(content_conv_out,dim=1)
        reshaped = content_conv_out.view(content_conv_out.size(0), -1)
        logits = self.fc((reshaped))
        return logits

    # def get_optimizer(self):  
    #    return  t.optim.Adam([
    #             {'params': self.title_conv.parameters()},
    #             {'params': self.content_conv.parameters()},
    #             {'params': self.fc.parameters()},
    #             {'params': self.encoder.parameters(), 'lr': 5e-4}
    #         ], lr=self.opt.lr)
    # # end method forward


 
if __name__ == '__main__':
    m = LSTMText(vocab_size = 22124, embedding_dim = 200, hidden_size = 500, num_layers = 3, linear_hidden_size = 512, num_classes = 5)
    content = t.autograd.Variable(t.arange(0,300).view(1,300)).long()
    o = m(content)
    print(o.size())
