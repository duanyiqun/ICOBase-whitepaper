import os  
import re
import string

import torch
import torch.utils.data as data
import pandas as pd 
import nltk
from nltk.stem import SnowballStemmer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import numpy as np
import pickle
import enchant
from torch.autograd import Variable

from string import digits

#### Please download nltk resources before using this file. 
#nltk.download("stopwords")
#print(stopwords.words('english'))
#nltk.download('wordnet')
#wordnet_lematizer = WordNetLemmatizer()
#print(wordnet_lematizer.lemmatize('good'))
#nltk.download('averaged_perceptron_tagger')
#print(nltk.pos_tag(['do','yes']))

class Myarticles(data.Dataset):
    def __init__(self, csvfile_path, txt_folder_path, glove_path='/Users/duanyiqun/Downloads/Textcls/glove.6B', validation=False):
        self.glove_path =glove_path
        #self.glove_init()
        #self.w2v = self.init_word2vec()
        self.articles = self.Creat_article_list(csvfile_path)
        #if validation:
        #    self.articles = self.articles[200:250]
        #else:
        #    self.articles = self.articles[0:200]
        self.articles = self.articles[0:250]
        self.folderpath = txt_folder_path
        self.snowball_stemmer = SnowballStemmer('english')
        self.wordnet_lematizer = WordNetLemmatizer()
        self.delset = str.maketrans('', '', string.punctuation)
        self.remove_digits = str.maketrans('', '', digits)
        self.spelldict = enchant.Dict("en_US")
        self.init_word2idx()
        
        
    def est_dict(self,article_list):
        temp = []
        for index, _ in enumerate(article_list):
            filepath = os.path.join(self.folderpath,self.articles[index][0])
            print('analyze article {}'.format(index))
            with open(filepath) as f:
                article = f.read()
            article = self.CleanLines(article)
            article = self.SenToken(article)
            article = self.tokenize_to_word(article)
            article = self.spell_check_words(article)
            article = self.steamize_words(article)
            temp = temp + article[0]
        vocab = set(temp)
        word_to_ix = {word: i for i, word in enumerate(vocab)}
        pickle.dump(word_to_ix, open(f'word2_idx.pkl', 'wb'))    
    
    def save_wdx(self):
        self.est_dict(self.articles)
    
    def init_word2idx(self):
        self.word2idx = pickle.load(open(f'word2_idx.pkl', 'rb'))
        print('sucessfully load word dictionary with shape{}'.format(len(self.word2idx)))

    def __getitem__(self, index):
        filepath = os.path.join(self.folderpath,self.articles[index][0])
        with open(filepath) as f:
            article = f.read()
        article = self.CleanLines(article)
        article = self.SenToken(article)
        article = self.tokenize_to_word(article)
        article = self.spell_check_words(article)
        article = self.steamize_words(article)
        article = self.vectorize(article)
        sample = Variable(torch.from_numpy(article[0]))
        target = self.articles[index][1]
        return sample, target

    def Creat_article_list(self, csvfile, label= 'Basic '):
        df = pd.read_csv(csvfile)
        article_list = []
        for idx, cont in enumerate(df['Basics ']):
            if cont != 'NA':
                article_list.append([df['Name'][idx],cont])
        return article_list
    
    def SenToken(self,raw):#分割成句子
        sent_tokenizer=nltk.data.load('tokenizers/punkt/english.pickle')
        sents = sent_tokenizer.tokenize(raw)
        return  sents
    
    def CleanLines(self,line):
        #cleanline = re.sub('[:*~@^&()_+|\/><,.!\']', '', line)
        #delset = str.maketrans('', '', string.punctuation)
        cleanline = line.translate(self.delset)
        #cleanline = re.sub('0123456789', '', cleanline)
        #remove_digits = str.maketrans('', '', digits)
        cleanline = cleanline.translate(self.remove_digits)
        return cleanline
    
    def tokenize_to_word(self, article):
        words_tokenized =[]
        for sentence in article:
            sentence = self.CleanLines(sentence)
            sentence = nltk.word_tokenize(sentence)
            words_tokenized.append(sentence)
        return words_tokenized

    def steamize_words(self,article):

        for idx, sentence in enumerate(article):
            for ind, word in enumerate(sentence):
                word = self.snowball_stemmer.stem(word)
                sentence[ind] = self.wordnet_lematizer.lemmatize(word)
            sentence = [word for word in sentence if word not in stopwords.words('english')]
            article[idx] = sentence
        return article
    
    def spell_check_words(self,article):
        for idx, sentence in enumerate(article):
            for ind, word in enumerate(sentence):
                if not self.spelldict.check(word):
                    if self.spelldict.suggest(word) != []:
                        sentence[ind] = self.spelldict.suggest(word)[0]
                    else:
                        sentence[ind] = ' '
            article[idx] = sentence
        return article
    
    def vectorize(self,article):
        temp = []
        for idx, sentence in enumerate(article):
            for ind, word in enumerate(sentence):
                sentence[ind] = self.word2idx[word]
            temp.append(sentence)
        return np.array(temp)

    
    def tag_mask(self,article):
        mask = []
        for idx, sentence in enumerate(article):
            mask.append(nltk.pos_tag(sentence))
        return mask

    """
    def glove_init(self):
        words = []
        idx = 0
        word2idx = {}
        vectors = bcolz.carray(np.zeros(1), rootdir=f'{self.glove_path}/6B.50.dat', mode='w')

        with open(f'{self.glove_path}/glove.6B.50d.txt', 'rb') as f:
            #idx =0
            for l in f:
                line = l.decode().split()
                word = line[0]
                words.append(word)
                word2idx[word] = idx
                idx += 1
                vect = np.array(line[1:]).astype(np.float)
                vectors.append(vect)
                #print(idx+1)
    
        vectors = bcolz.carray(vectors[1:].reshape((400001, 50)), rootdir=f'{self.glove_path}/6B.50.dat', mode='w')
        vectors.flush()
        pickle.dump(words, open(f'{self.glove_path}/6B.50_words.pkl', 'wb'))
        pickle.dump(word2idx, open(f'{self.glove_path}/6B.50_idx.pkl', 'wb'))
    
    def init_word2vec(self):
        vectors = bcolz.open(f'{self.glove_path}/6B.50.dat')[:]
        words = pickle.load(open(f'{self.glove_path}/6B.50_words.pkl', 'rb'))
        word2idx = pickle.load(open(f'{self.glove_path}/6B.50_idx.pkl', 'rb'))
        glove = {w: vectors[word2idx[w]] for w in words}
        return glove 
    
    def word2map(self, article):
        matrix_len = 0
        for idx, sentence in enumerate(article):
            if matrix_len<len(sentence):
                matrix_len = len(sentence)
        vecarticle = []
        for idx, sentence in enumerate(article):        
            #words_found = 0
            weights_matrix = np.zeros((matrix_len, 50))
            for i, word in enumerate(sentence):
                try: 
                    weights_matrix[i] = self.w2v[word]
                    words_found += 1
                except:
                    print('key not founded, initialized random weights')
                    weights_matrix[i] = np.random.normal(scale=0.6, size=(50, ))  
            vecarticle.append(weights_matrix)
        
        return vecarticle
    """
    def __len__(self):
        return len(self.articles)

if __name__ == '__main__':
    article = Myarticles('./wp_analysis.csv','./txt')
    test_loader = data.DataLoader(article,batch_size=1,shuffle=False)
    article.save_wdx()
    for sample, target in test_loader:
        print(sample)
        print(target)




########################test###################
