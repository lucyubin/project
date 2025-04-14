# Package Installation
!pip install nltk
!pip install --upgrade pip
!pip install konlpy
!pip install wordcloud
!pip install --upgrade gensim
!pip install matplotlib

import pandas as pd
from konlpy.tag import Kkma
kkma = Kkma()
import nltk
from nltk import FreqDist
from konlpy.tag import Okt; t = Okt()
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from wordcloud import WordCloud, STOPWORDS

# Specify the working directory
file_path = 'D:/*/'

# 1. Load Data
# Read Excel data
data_hs = pd.read_excel(file_path + '*.xlsx', sheet_name=0)

# Combine title + keyword + abstract
df_hs = pd.DataFrame() # Create an empty dataframe
df_hs['year'] = data_hs['연도'] # Get the year
df_hs['words'] = data_hs['제목'] + ' ' + data_hs['키워드'] + ' ' + data_hs['초록'] # Merge title, keyword, and abstract with a space separator
df_hs['words'] = df_hs['words'].str.replace('\n', ' ') # Replace newline characters with spaces

# 2. Morphological Analysis
# Concatenate multiple rows into a single string to generate word cloud
combined_text = ' '.join(df_hs['words'].astype(str))
tokens_ko = t.nouns(combined_text) # Extract nouns

ko = nltk.Text(tokens_ko, name = 'keyword analysis') 
print(len(ko.tokens)) # The length of token
print(len(set(ko.tokens))) # The number of unique token
ko.vocab() # Print words and their frequencies

# 3. Frequency analysis
font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
rc('font', family=font_name)

# Generate word frequency graph
plt.figure(figsize=(12,6))
ko.plot(50) # Print most frequent 50 words
plt.show()

# Print word frequency
freq_dist = FreqDist(ko.tokens)
df_freq_dist = pd.DataFrame(freq_dist.items(), columns=['단어', '빈도']).sort_values(by='빈도', ascending=False)
df_freq_dist.to_csv(file_path + 'word_frequency.csv', index=False, encoding='cp949')

stop_words = ['것', '수', '및', '위', '등', '이', '비', '의', '그']
ko = [each_word for each_word in ko if each_word not in stop_words]

# Re-generate word frequency graph
ko = nltk.Text(ko, name='keyword analysis')
plt.figure(figsize=(12,6))
ko.plot(50)
plt.show()

# 4. Generate Word Cloud
data = ko.vocab().most_common(150)
wordcloud = WordCloud(font_path='c:/Windows/Fonts/malgun.ttf',
                     relative_scaling = 0.2,
                     background_color='white',
                     ).generate_from_frequencies(dict(data))
plt.figure(figsize=(12,8))
plt.imshow(wordcloud)
plt.axis("off")
plt.show()
