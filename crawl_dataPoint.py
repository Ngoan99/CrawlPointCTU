import requests
from bs4 import BeautifulSoup

import time
import numpy as np
import pandas as pd

import infor

##show all to display in pandas
pd.set_option('display.max_rows', None)

##get information to login
username = infor.username
password = infor.passwd

##fake browsers visit
headers = {"user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.194 Safari/537.36"}

payload = {
    'txtDinhDanh': username,
    'txtMatKhau': password,
    'f6e7a9414bec': '9B1709027tbuxkttyt',
    'f2711251a4f': '5%24PTNgoan2510tkyx3',
}

##form data to post
kqht_data = {"hdDonVi": "Khoa+Công+nghệ"}
query_data = {"cmbKhoaHoc": "%", "cmbHocKy": "%"}

##link to access
urls = [
    "https://qldt.ctu.edu.vn/htql/sinhvien/dang_nhap.php",                  ## Login page
    "https://qldt.ctu.edu.vn/htql/sinhvien/hindex.php",                     ## Main page
    "https://qldt.ctu.edu.vn/htql/sinhvien/qldiem/codes/index.php",         ## KQHT
    "https://qldt.ctu.edu.vn/htql/sinhvien/qldiem/codes/index.php?mID=201"  ## View point page
]

##access to link
with requests.Session() as s:
    ## Login
    response = s.post(urls[0], data=payload, headers=headers)
    ##Navigate to Main page
    response = s.get(urls[1], headers=headers)
    time.sleep(0.1)
    ##Navigate to kqht page
    response = s.post(urls[2], data=kqht_data, headers=headers)
    time.sleep(0.1)
    ## Get all kqht with table format
    response = s.post(urls[3], data=query_data, headers=headers)
    time.sleep(0.1)

    if response.status_code != 200:
        print('---------Get data failed--------------')
 
##read html and process raw data 
dfs = pd.read_html(response.content)
tables = [df.drop(0, axis='rows') for df in dfs[5::3]]
rawData = pd.concat(tables)

##set the column name
name_columns = dfs[5].loc[0, :]
rawData.columns = name_columns

##remove the first column and set the order number for rows
rawData.drop(labels=['Stt'],axis=1,inplace=True)
rawData.index = np.arange(1,rawData.shape[0]+1,1)

##remove data about SHCVHT and set the order number for rows
Data = rawData[rawData['Mã HP']!='SHCVHT']
Data.index = np.arange(1,Data.shape[0]+1,1)

##find duplicated rows 
same1 = Data.loc[Data.duplicated(subset=['Mã HP'], keep='first'),:]
same2 = Data.loc[Data.duplicated(subset=['Mã HP'], keep='last'),:]

##save information of subjects more than 1 time
item1 = [list(same1.index),list(same1['Điểm số'])]
item2 = [list(same2.index),list(same2['Điểm số'])]
Idx_get=[]
Idx_rem=[]

##select rows where that have greater score data
for i in range(len(item1[0])):
    if item1[1][i] <= item2[1][i]:
        Idx_rem.append(item1[0][i])
        Idx_get.append(item1[0][i])
    else:
        Idx_rem.append(item2[0][i])
        Idx_get.append(item1[0][i])

remIdx = np.array(Idx_rem)-1
remIdx = list(remIdx)
getIdx = np.array(Idx_get)
getIdx = list(getIdx)

bulkhead = pd.DataFrame(['-']*same1.shape[1]).T
bulkhead.columns = name_columns[1:]
filted = Data.ix[getIdx]
frames = [same2, bulkhead, same1, bulkhead, filted]
Re_learn = pd.concat(frames)
Re_learn = Re_learn.reset_index().iloc[:, 1:] 
RE = Re_learn.style.set_properties(**{'background-color': 'black', 'color': 'green'},
                              subset=pd.IndexSlice[Re_learn.shape[0]- filted.shape[0]:, :])

##save re_learn data as excel file
RE.to_excel("Re_LearnDATA.xlsx", index = False)

##remove duplicated rows that have smaller score data and set the order number for rows
Data =Data.drop(Data.index[[[remIdx]]])
Data.index = np.arange(1,Data.shape[0]+1,1)

##save full data as excel file
Data.to_excel("FullDATA.xlsx", index = True)

##remove the courses that do not have accumulated points
Accum = Data[Data['Tích lũy'] == '*']
Accum.to_excel("AccumDATA.xlsx", index = True)

##remove conditional courese
Final = Accum[Accum['Điều kiện'] != "x"] 
Final.index = np.arange(1,Final.shape[0]+1,1)

##get items data to accumulate GPA
credits = list(Final['Tín chỉ'])
scores = list(Final['Điểm chữ'])
    ##convert letter score to score
for idx, sco in enumerate(scores):
    if sco =='A':
        scores[idx] = 4
    if sco =='B+':
        scores[idx] = 3.5
    if sco =='B':
        scores[idx] = 3
    if sco =='C+':
        scores[idx] = 2.5
    if sco =='C':
        scores[idx] = 2
    if sco =='D+':
        scores[idx] = 1.5
    if sco =='D':
        scores[idx] = 1    
Exchane = scores

##insert Exchane column into Accum and set the order number for rows
Final.insert(loc=6, column='Điểm quy đổi', value=Exchane)
Final.index = np.arange(1,Final.shape[0]+1,1)

##save accumulated data as csv file
Final.to_excel("DATA.xlsx", index = True)

##caculate GPA
numerator = 0
denominator = 0
for i in range(len(credits)):
    numerator += float(credits[i])*Exchane[i]
    denominator += float(credits[i])

GPA = numerator/denominator
print('GPA = ', GPA)




