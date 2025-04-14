import time
import requests
import html2text
from bs4 import BeautifulSoup

# Abstract Gallery 총 페이지 수. 변경할 것:년도, 페이지 수 (2018년 124, 2019년 121, 2020 98)
for page in range(98):
    url = "https://aag.secure-abstracts.com/AAG%20Annual%20Meeting%202020/abstracts-gallery?query=&searchContent=False&type=&topic=&page=" + str(page+1) + "&poster=&affiliation=&availability=ShowAll"
    html = requests.get(url)
    
    # html을 text 파일로 저장
    contents = html.text
   
    # 크롤링할 처음 부분, 마지막 부분 지정
    start = 533
    end = contents.find("li class", start, len(contents))
    extract_url1 = contents[start:end]

    # '\n'로 한 문장 뒤에 엔터
    a = extract_url1.split("\n")
    b = [word for word in a if "gallery" in word]

    # 텍스트 파일로 저장. 'a'는 이어 붙이는 기능
    f = open("./2020.txt", 'a', 
             encoding="utf-8")
    f.writelines(b)
    f.close()
    
    time.sleep(5)
    
url = "https://aag.secure-abstracts.com/AAG%20Annual%20Meeting%202018/abstracts-gallery?query=&searchContent=False&type=&topic=&page=1&poster=&affiliation=&availability=ShowAll"
html = requests.get(url)

print(html)
print(html.text)

# html을 txt로 
h = html2text.HTML2Text()
contents = h.handle(html.text)

# contents의 앞부분과 뒷부분 잘라내기
start = 2786
end = contents.find("* * *", start, len(contents))
extract_url1 = contents[start:end]

count1 = extract_url1.count("####")

# extract_url1을 txt 파일로 저장
f = open("./test1.txt", 'w', encoding="utf-8")
f.writelines(extract_url1)
f.close()

# str을 '\n' 구분 기호로 분리하여 리스트로 저장
type(extract_url1)

a = extract_url1.split("\n")
print(a)

# "abstracts-gallery"를 포함하는 문장 추출
word_list = a
search = "gallery"
b = [word for word in word_list if search in word]
print(b)
    
# 리스트를 다시 문자열로
c = '\n'.join(b)

f = open("./test2.txt", 'a', encoding="utf-8")
f.writelines(c)
f.close()

f = open("./2019_ab.txt", 'r')

# 텍스트 파일을 리스트 형태로 불러오기
test_list = f.readlines()
for line in test_list:
    print(line.strip('\n')) #\n없이 불러오기

# 공백 없이 list를 str로 변경
test_str = "".join(test_list)

# '\n'을 ''으로 대체
test_str2 = test_str.replace("\n", "")


# Replace 함수로 한 줄씩 띄우기
test_str3 = test_str2.replace("Authors:", "\nAuthors::")
test_str4 = test_str3.replace("Topics:", "\nTopics::")
test_str5 = test_str4.replace("Keywords:", "\nKeywords::")
test_str6 = test_str5.replace("Session Type:", "\nSession Type::")
test_str7 = test_str6.replace("Day:", "\nDay::")
test_str8 = test_str7.replace("Start / End Time:", "\nStart / End Time::")
test_str9 = test_str8.replace("Room:", "\nRoom::")
test_str10 = test_str9.replace("Presentation File:", "\nPresentation File::")
test_str11 = test_str10.replace("####", "\nTitle::")
test_str12 = test_str11.replace("-----", "\nAbstract:: ")
#print(test_str12)

f = open("./2019_abstract.txt", "a", encoding="utf-8")
f.write(test_str12)
f.close()
