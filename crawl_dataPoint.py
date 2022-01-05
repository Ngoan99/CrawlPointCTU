import time
import getpass as gp
import requests
import numpy as np
from bs4 import BeautifulSoup
import pandas as pd
#show all to display in pandas
pd.set_option('display.max_rows', None)

#get information to login
username = str(input('Enter user name: '))
password = gp.getpass('Enter password: ')

login_data = {
    'txtDinhDanh': username,
    'txtMatKhau': password,
    'f6e7a9414bec': '8B1709027531kkt5a',
    'f2711251a4f': '5%24PTNgoan2510ktkyx',
}

#form data to post
kqht_data = {"hdDonVi": "Khoa+Công+nghệ"}
query_data = {"cmbKhoaHoc": "%", "cmbHocKy": "%"}

#fake browsers visit
headers = {"user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.194 Safari/537.36"}

#link to access
urls = [
    "https://qldt.ctu.edu.vn/htql/sinhvien/dang_nhap.php",                  # Trang đăng nhập
    "https://qldt.ctu.edu.vn/htql/sinhvien/hindex.php",                     # Trang chủ
    "https://qldt.ctu.edu.vn/htql/sinhvien/qldiem/codes/index.php",         # Trang kqht
    "https://qldt.ctu.edu.vn/htql/sinhvien/qldiem/codes/index.php?mID=201"  # Xem bảng điểm
]

#access to link
with requests.Session() as s:
    # Login
    r = s.post(urls[0], data=login_data, headers=headers)
    # Navigate to main page
    r = s.get(urls[1], headers=headers)
    time.sleep(0.5)
    # Navigate to kqht page
    r = s.get(urls[2], data=kqht_data, headers=headers)
    time.sleep(0.5)
    # Get kqht table
    r = s.get(urls[3], headers=headers)
    time.sleep(0.5)
    # Get kqht table
    r = s.post(urls[3], data=query_data, headers=headers)
    time.sleep(1.5)
    if r.status_code != 200:
        print('---------Get data failed--------------')
    # soup = BeautifulSoup(r.content)

#read html and process raw data 
dfs = pd.read_html(r.content)
tables = [df.drop(0, axis='rows') for df in dfs[5::3]]
rawData = pd.concat(tables)

#set the column name
name_columns = dfs[5].loc[0, :]
rawData.columns = name_columns

#remove the first column and set the order number for rows
rawData.drop(labels=['Stt'],axis=1,inplace=True)
rawData.index = np.arange(1,rawData.shape[0]+1,1)

#remove data about SHCVHT and set the order number for rows
Data = rawData[rawData['Mã HP']!='SHCVHT']
Data.index = np.arange(1,Data.shape[0]+1,1)

#find duplicated rows 
same1 = Data.loc[Data.duplicated(subset=['Mã HP'], keep='first'),:]
same2 = Data.loc[Data.duplicated(subset=['Mã HP'], keep='last'),:]

#save information of subjects more than 1 time
item1 = [list(same1.index),list(same1['Điểm số'])]
item2 = [list(same2.index),list(same2['Điểm số'])]
Idx_get=[]
Idx_rem=[]

#select rows where that have greater score data
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

#save re_learn data as excel file
RE.to_excel("Re_LearnDATA.xlsx", index = False)

#remove duplicated rows that have smaller score data and set the order number for rows
Data =Data.drop(Data.index[[[remIdx]]])
Data.index = np.arange(1,Data.shape[0]+1,1)

#save full data as excel file
Data.to_excel("FullDATA.xlsx", index = True)

#remove the courses that do not have accumulated points
Accum = Data[Data['Tích lũy'] == '*']

#get items data to accumulate GPA
credits = list(Accum['Tín chỉ'])
scores = list(Accum['Điểm chữ'])
    #convert letter score to score
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

#insert Exchane column into Accum and set the order number for rows
Accum.insert(loc=6, column='Exchane_scores', value=Exchane)
Accum.index = np.arange(1,Accum.shape[0]+1,1)

#save accumulated data as csv file
Accum.to_excel("AccumScoreDATA.xlsx", index = True)

#caculate GPA
numerator = 0
denominator = 0
for i in range(len(credits)):
    numerator += int(credits[i])*Exchane[i]
    denominator += int(credits[i])

GPA = numerator/denominator
print(denominator)
print(GPA)




