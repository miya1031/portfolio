#インポート

import pandas as pd
import csv
from datetime import datetime
from datetime import timedelta
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
import numpy as np
import re
import codecs
import math
import time

class OutputURL():
    def __init__(self,year,month,day,place):
        '''
        year:(int) 年
        month:(int) 月
        day:(int) 日
        place:(str) 開催場
        '''
        self.year = year
        self.month = month
        self.day = day
        self.place = place
        place_labels = ['桐生','戸田','江戸川','平和島','多摩川','浜名湖','蒲郡','常滑','津','三国','びわこ','住之江','尼崎','鳴門','丸亀','児島','宮島','徳山','下関','若松','芦屋','福岡','唐津','大村']
        self.p_num = str(place_labels.index(place)+1).zfill(2)
        self.result_url = None
        self.racelist_url = None
        self.beforeinfo_url = None
    def OutputResultURL(self,r_num):
        '''
        (self.year)年(self.month)月(self.day)日の(self.place)ボートレース場の(r_num)の
        競争成績のURLを出力する
        r_num:(int) レース番号
        '''
        self.result_url = 'https://www.boatrace.jp/owpc/pc/race/raceresult?rno='+str(r_num)+'&jcd='+self.p_num+'&hd='+str(self.year)+str(self.month).zfill(2)+str(self.day).zfill(2)
        return self.result_url
    
    def OutputRacelistURL(self,r_num):
        '''
        (self.year)年(self.month)月(self.day)日の(self.place)ボートレース場の(r_num)の
        競走表のURLを出力する
        r_num:(int) レース番号
        '''
        self.racelist_url = 'https://www.boatrace.jp/owpc/pc/race/racelist?rno='+str(r_num)+'&jcd='+self.p_num+'&hd='+str(self.year)+str(self.month).zfill(2)+str(self.day).zfill(2)
        return self.racelist_url
    
    def OutputBeforeInfoURL(self,r_num):
        '''
        (self.year)年(self.month)月(self.day)日の(self.place)ボートレース場の(r_num)の
        直前情報のURLを出力する
        r_num:(int) レース番号
        '''
        self.beforeinfo_url = 'https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno='+str(r_num)+'&jcd='+self.p_num+'&hd='+str(self.year)+str(self.month).zfill(2)+str(self.day).zfill(2)
        return self.beforeinfo_url

def OutputWindDirection(soup):
    '''
    soup:htmlデータ
    
    ボートレース結果URLのhtmlを読み解くと風向を表す画像は番号で管理されている。
    # その管理方法は1番が北、2番が北北東、16番が北北西だと思われる。
    その管理方法は1番が南、2番が南南西、16番が南南東だと思われる。
    この法則だとしたとき、htmlデータから風速を出力する関数。

    出力
    w_d:(str) 風向
    w_t:(str) ""or"追い風"or"向い風"
    '''
    # direction = ['北','北北東','北東','東北東','東','東南東','南東','南南東','南','南南西','南西','西南西','西','西北西','北西','北北西']
    direction = ['南','南南西','南西','西南西','西','西北西','北西','北北西','北','北北東','北東','東北東','東','東南東','南東','南南東']
    north_num = None
    wind_num = None
    dif_num = None
    result_num = None
    w_d = None
    w_t = None
    
    for i in range(len(direction)):
        info = 'weather1_bodyUnitImage is-direction'+str(i+1)+' is-type1__3rdadd'
        if soup.find('p',class_=info) != None:
            north_num = i+1
    for i in range(len(direction)):
        info = "weather1_bodyUnitImage is-wind"+str(i+1)
        if soup.find('p',class_=info) != None:
            wind_num = i+1
    if wind_num == None:
        return w_d,w_t
    else:
        dif_num = north_num-1
        result_num = wind_num - dif_num
        w_d = direction[result_num-1]
        if wind_num in [11,12,13,14,15]:
            w_t = '向い風'
        elif wind_num in [3,4,5,6,7]:
            w_t = '追い風'
        return w_d,w_t

def OutputRaceClass(soup):
    '''
    soup:htmlデータ
    
    ボートレース結果URLのhtmlを読み解くとレースクラス画像は文字列で管理されている。
    htmlデータからレースクラスを出力する関数。
    '''
    str_list = ['ippan','G3b','G2b','G1b','G1a','SGa']
    class_list = ['一般','G3','G2','G1','PG1','SG']
    for i in range(len(str_list)):
        info = "heading2_title is-"+str_list[i]
        if soup.find('div',class_=info) != None:
            return class_list[i]


def OutputOthers(soup):
    '''
    soup:htmlデータ
    
    出力
    
    r_name:(str) レース名
    r_type:(str) レース種別
    dist:(str) 距離
    stable_boad(str):安定版
    temp:気温
    climate:天候
    wind_power:風速
    w_temp:水温
    wave_height:波高
    
    htmlデータから
    その他情報を取得する関数
    '''
    r_name = soup.find('h2',class_ = 'heading2_titleName').string
    stable_boad = ''
    try:
        stable_boad += soup.find('span',class_ = 'label2 is-type1').text
    except AttributeError:
        stable_boad += ''
    try:
        stable_boad += soup.find('span',class_ = 'label2 is-type2__add2020').text
    except AttributeError:
        stable_boad += ''
    text_ = soup.find('h3',class_ = 'title16_titleDetail__add2020').text#string→textにすることで距離短縮の赤字距離に対応
    text_ = text_.split()
    r_type, dist = text_[0], text_[1]
    #r_type = soup.find('span',class_ = 'heading2_titleDetail is-type1').string[:soup.find('span',class_ = 'heading2_titleDetail is-type1').string.index('\u3000')]
    #dist = soup.find('span',class_ = 'heading2_titleDetail is-type1').string.replace(r_type,'').replace('\u3000','').replace('\r','').replace('\n','').replace('\t','').replace('m','')
    temp = soup.find_all('span',class_ = 'weather1_bodyUnitLabelData')[0].string.replace('\r','').replace('\n','').replace(' ','').replace('℃','')
    climate = soup.find_all('span',class_ = 'weather1_bodyUnitLabelTitle')[1].string.replace('\r','').replace('\n','').replace(' ','')
    wind_power = soup.find_all('span',class_ = 'weather1_bodyUnitLabelData')[1].string.replace('\r','').replace('\n','').replace(' ','').replace('m','')
    w_temp = soup.find_all('span',class_ = 'weather1_bodyUnitLabelData')[2].string.replace('\r','').replace('\n','').replace(' ','').replace('℃','')
    wave_height = soup.find_all('span',class_ = 'weather1_bodyUnitLabelData')[3].string.replace('\r','').replace('\n','').replace(' ','').replace('cm','')
    
    return r_name,r_type,dist,stable_boad,temp,climate,wind_power,w_temp,wave_height

def OutputRefund(bet_type,df):
    '''
    入力
    bet_type:(str) 賭式
    df:(df)払戻金が含まれるデータフレーム
    出力
    組番・払戻金の文字列
    '''
    result = ''
    match_df = df[df['勝式']==bet_type]
    match_df = match_df.dropna(subset=['組番'])
    match_df = match_df.reset_index(drop=True)#インデックスの振りなおし
    for i in range(len(match_df)):
        result += match_df.at[i,'組番']
        if type(match_df.at[i,'払戻金'])==str:#複勝の配当金が記載されていないことがある。
            result += ' '
            result += match_df.at[i,'払戻金']
        if i != (len(match_df)-1):
            result += ' / '
    return result

def OutputCause(df):#１着同着は２艇まで考える。おそらく３艇同着はない
    '''
    決まり手のデータフレームから、決まり手をリストで出力（１着同着２艇まで考慮）
    '''
    cause_list = ['逃げ','差し','まくり','まくり差し','抜き','恵まれ']
    if df.at[0,'決まり手'] in cause_list:
        return [df.at[0,'決まり手']]
    else:
        for i in cause_list:
            for j in cause_list:
                if i+j == df.at[0,'決まり手']:
                    return [i,j]

class OrganizeDfs():
    def __init__(self):
        self.df = None
    def OutputDfs(self,dframe):
        dfs = dframe
        cause_ = OutputCause(dfs[5])
        if len(cause_) ==1:
            cause = cause_[0]#1着同着の場合はどうなるか要確認
            cause_2 = ''
        else:#１着同着は２艇まで考える。おそらく３艇同着はない
            cause = cause_[0]
            cause_2 = cause_[1]
        split_player_num = lambda x: x[:x.index(' ')]
        split_name = lambda x: x[x.index(' ')+1:]
        to_second = lambda x: float(x[0])*60+float(x[2:4])+float(x[5])*0.1 if x != 0 else None
        dfs[1]['レースタイム']=dfs[1]['レースタイム'].fillna(0)
        dfs[1]['登録番号'] = dfs[1]['ボートレーサー'].map(split_player_num).astype(int)
        dfs[1]['名前'] = dfs[1]['ボートレーサー'].map(split_name)
        dfs[1]['レースタイム（秒）'] = dfs[1]['レースタイム'].map(to_second)
        dfs[1]=dfs[1].drop('ボートレーサー',axis=1)
        dfs[1]['決まり手']=[cause,cause_2,'','','','']
        dfs[1] = dfs[1].astype(str)
        split_boat_num = lambda x: str(x)[0]
        split_s_time = lambda x : str(x)[1:].replace(cause,'').replace(cause_2,'').replace('F','').replace('L','')
        #欠場選手が一人いた場合、スタート情報は５艇分しかないのでエラーが出る。
        dfs[2]['枠'] = dfs[2]['スタート情報'].map(split_boat_num)
        dfs[2]['スタート情報'] = dfs[2]['スタート情報'].map(split_s_time)
        dfs[2]['スタート情報'] = pd.to_numeric(dfs[2]['スタート情報'],errors='coerce')
        in_course = [1,2,3,4,5,6]
        in_course = in_course[:len(dfs[2])]
        dfs[2]['進入コース'] = in_course
        waku1 = ['1','2','3','4','5','6']
        #欠場選手の情報をNoneで補完。例）20211031浜名湖3R,出遅れの時もスタート情報がない場合がある。例）20211007浜名湖5R
        for waku1_ in waku1:
            if waku1_ not in dfs[2]['枠'].tolist():
                dfs[2].loc[len(dfs[2])]=[None,waku1_,None]
        self.df = pd.merge(dfs[1], dfs[2], on='枠')
        return self.df
    def AddRefund(self,dframe):
        dfs = dframe
        for betting in ['3連単','3連複','2連単','2連複','拡連複','単勝','複勝']:
            self.df[betting] = OutputRefund(betting,dfs[3])
        return self.df

class ResultScraping():
    def __init__(self,url):
        self.url = url
        self.dfs = pd.read_html(self.url)#締切時刻のスクレイピングに外で使う
        self.result_df = None
    
    def OutputResult(self):
        ResultDf = OrganizeDfs()
        ResultDf.OutputDfs(self.dfs)
        self.result_df = ResultDf.AddRefund(self.dfs)
        return self.result_df       
        
    def OutputOtherInfo(self):
        r = requests.get(self.url)
        soup = BeautifulSoup(r.content,'html.parser')
        self.result_df['レース名'],self.result_df['レース種'],self.result_df['距離'],self.result_df['安定版/進入固定'],self.result_df['気温'],self.result_df['天候'],self.result_df['風速'],self.result_df['水温'],self.result_df['波高'] = OutputOthers(soup)
        self.result_df['風向'],self.result_df['風種'] = OutputWindDirection(soup)
        self.result_df['レースグレード'] = OutputRaceClass(soup)
        return self.result_df       


def index_multi(l,x):
    '''
    入力
    l:(str) 調べたい文字列
    x:(str) indexを調べたい文字列
    出力
    (list) xのインデックス（複数）
    '''
    return [i for i,_x in enumerate(l) if _x == x]

def Output_class_place_age_weight(x):
    '''
    入力
    x:(str) 級別・支部・出身地が含まれる文字列
    出力
    class_result:(str) 級別
    home_result:(str) 支部
    birth_result:(str) 出身地
    age_result:(str) 年齢
    weught_result:(str) 体重
    '''
    place_list = ['北海道',
    '青森',
    '岩手',
    '宮城',
    '秋田',
    '山形',
    '福島',
    '茨城',
    '栃木',
    '群馬',
    '埼玉',
    '千葉',
    '東京',
    '神奈川',
    '新潟',
    '富山',
    '石川',
    '福井',
    '山梨',
    '長野',
    '岐阜',
    '静岡',
    '愛知',
    '三重',
    '滋賀',
    '京都',
    '大阪',
    '兵庫',
    '奈良',
    '和歌山',
    '鳥取',
    '島根',
    '岡山',
    '広島',
    '山口',
    '徳島',
    '香川',
    '愛媛',
    '高知',
    '福岡',
    '佐賀',
    '長崎',
    '熊本',
    '大分',
    '宮崎',
    '鹿児島',
    '沖縄']
    class_list = ['A1','A2','B1','B2']
    class_result = None
    place_result = []
    home_result = None
    birth_result = None
    age_result = None
    weight_result = None
    for class_ in class_list:
        if class_ in x:
            class_result = class_
    index_x = index_multi(x,'/')
    age_result = x[index_x[-1]-3:index_x[-1]].replace('歳','')
    weight_result = x[index_x[-1]+1:].replace('kg','')
    
    #都道府県名が入っている名前をカウントしないように（例：山形）文字列を短縮
    x = x[index_multi(x,' ')[-3]:]
    for place_ in place_list:
        if place_ in x:
            place_result += [place_]
    if len(place_result) == 1:#支部 = 出身地の場合
        home_result = place_result[0]
        birth_result = place_result[0]
    elif len(place_result) == 2:#支部 != 出身地の場合
        if x.index(place_result[0]) < x.index(place_result[1]):
            home_result = place_result[0]
            birth_result = place_result[1]
        else:
            home_result = place_result[1]
            birth_result = place_result[0]
    return class_result,home_result,birth_result,age_result,weight_result

def OutputMotorOrBoat(y):
    '''
    モーター（ボート）番号・モーター（ボート）２連対率・モーター（ボート）３連対率を出力する
    ※全国・当地選手成績やFL数・平均スタートタイムもこの関数で出力できる。
    '''
    result_num = None
    result_within2 = None
    result_within3 = None
    index_y = index_multi(y,' ')
    result_num = y[:index_y[0]]
    result_within2 = y[index_y[0]+1:index_y[-1]].replace(' ','')
    result_within3 = y[index_y[-1]+1:]
    return result_num,result_within2,result_within3

def RacelistScraping(url):
    '''
    入力
    url:(str) 出走表のurl
    出力
    df:(df) 枠・モーター情報（番号・２連対立・３連対率）・ボート情報（番号・２連対立・３連対率）・級別・支部・出身地・年齢・体重が含まれるデータフレーム
    '''
    dfs = pd.read_html(url)
    waku = ['1','2','3','4','5','6']#枠は文字列で統一。そうしないとdfをmergeできない。
    p_F = []
    p_L = []
    p_ST = []
    p_all_within1 = []
    p_all_within2 = []
    p_all_within3 = []
    p_at_within1 = []
    p_at_within2 = []
    p_at_within3 = []
    motor_num = []
    motor_within2 = []
    motor_within3 = []
    boat_num = []
    boat_within2 = []
    boat_within3 = []
    p_class = []
    p_home = []
    p_birth = []
    p_age = []
    p_weight = []
    for i in range(0,24,4):
        p_F_,p_L_,p_ST_ = OutputMotorOrBoat(dfs[1].loc[i,('ボートレーサー','F数L数平均ST')][0])
        p_F_ = p_F_.replace('F','')
        p_L_ = p_L_.replace('L','')
        p_F += [p_F_]
        p_L += [p_L_]
        p_ST += [p_ST_]
        p_all_within1_,p_all_within2_,p_all_within3_ = OutputMotorOrBoat(dfs[1].loc[i,('全国','勝率2連率3連率')][0])
        p_all_within1 += [p_all_within1_]
        p_all_within2 += [p_all_within2_]
        p_all_within3 += [p_all_within3_]
        p_at_within1_,p_at_within2_,p_at_within3_ = OutputMotorOrBoat(dfs[1].loc[i,('当地','勝率2連率3連率')][0])
        p_at_within1 += [p_at_within1_]
        p_at_within2 += [p_at_within2_]
        p_at_within3 += [p_at_within3_]
        motor_num_,motor_within2_,motor_within3_ = OutputMotorOrBoat(dfs[1].loc[i,('モーター','No2連率3連率')][0])
        motor_num += [motor_num_]
        motor_within2 += [motor_within2_]
        motor_within3 += [motor_within3_]
        boat_num_,boat_within2_,boat_within3_ = OutputMotorOrBoat(dfs[1].loc[i,('ボート','No2連率3連率')][0])
        boat_num += [boat_num_]
        boat_within2 += [boat_within2_]
        boat_within3 += [boat_within3_]
        p_class_,p_home_,p_birth_,p_age_,p_weight_= Output_class_place_age_weight(dfs[1].loc[i,('ボートレーサー','登録番号/級別氏名支部/出身地年齢/体重')][0])
        p_class += [p_class_]
        p_home += [p_home_]
        p_birth += [p_birth_]
        p_age += [p_age_]
        p_weight += [p_weight_]
    df = pd.DataFrame(data={'枠': waku, 
                            'F数': p_F, 
                            'L数': p_L,
                            '平均スタートタイム': p_ST, 
                            '全国勝率': p_all_within1, 
                            '全国2連対率': p_all_within2, 
                            '全国3連対率': p_all_within3,
                            '当地勝率': p_at_within1, 
                            '当地2連対率': p_at_within2,
                            '当地3連対率': p_at_within3, 
                            'モーター番号': motor_num, 
                            'モーター2連対率': motor_within2, 
                            'モーター3連対率': motor_within3,
                            'ボート番号': boat_num, 
                            'ボート2連対率': boat_within2, 
                            'ボート3連対率': boat_within3,
                            '級別': p_class,
                            '支部': p_home,
                            '出身地': p_birth,
                            '年齢': p_age,
                            '体重': p_weight}, 
                      columns=['枠', 
                               'F数', 
                               'L数', 
                               '平均スタートタイム', 
                               '全国勝率', 
                               '全国2連対率', 
                               '全国3連対率', 
                               '当地勝率', 
                               '当地2連対率', 
                               '当地3連対率', 
                               'モーター番号', 
                               'モーター2連対率', 
                               'モーター3連対率', 
                               'ボート番号', 
                               'ボート2連対率', 
                               'ボート3連対率', 
                               '級別', 
                               '支部', 
                               '出身地', 
                               '年齢', 
                               '体重'])
    return df

def JustInfoScraping(url):
    dfs_ = pd.read_html(url)
    waku = ['1','2','3','4','5','6']#枠は文字列で統一。そうしないとdfをmergeできない。
    tenji_time = []
    tilt = []
    propeller = []
    change_parts = []
    adjust_weight = []
    tenji_course = [1,2,3,4,5,6]
    tenji_waku = []
    tenji_st = []
    
    for i in range(0,24,4):
        tenji_time += [dfs_[1].loc[i,('展示タイム','展示タイム')]]
        tilt += [dfs_[1].loc[i,('チルト','チルト')]]
        propeller += [dfs_[1].loc[i,('プロペラ','プロペラ')]]
        change_parts += [dfs_[1].loc[i,('部品交換','部品交換')]]
        adjust_weight += [dfs_[1].loc[i+2,('体重','調整重量')]]
    #print(dfs_[2])
    #print(dfs_[2].loc[5,('スタート展示','コース')])
    for j in range(6):
        if type(dfs_[2].loc[j,('スタート展示','コース')]) == str:
            tenji_waku += [dfs_[2].loc[j,('スタート展示','コース')][0]]
            tenji_st += [dfs_[2].loc[j,('スタート展示','コース')][3:]]
    #欠場の展示タイムをNone補完
    tenji_course = tenji_course[:len(tenji_waku)]
    for waku_ in waku:
        if waku_ not in tenji_waku:
            tenji_waku += [waku_]
            tenji_course += [None]
            tenji_st += [None]
    d_ = pd.DataFrame(data={'枠': waku, 
                            '展示タイム': tenji_time, 
                            'チルト': tilt, 
                            'プロペラ': propeller, 
                            '部品交換': change_parts, 
                            '調整重量': adjust_weight}, 
                      columns=['枠', 
                               '展示タイム', 
                               'チルト', 
                               'プロペラ', 
                               '部品交換', 
                               '調整重量'])
    df_tenji = pd.DataFrame(data={'枠': tenji_waku, 
                                  '展示進入コース': tenji_course, 
                                  '展示スタートタイム': tenji_st}, 
                            columns=['枠', 
                                     '展示進入コース',
                                     '展示スタートタイム'])
    return pd.merge(d_,df_tenji,on='枠')

class OutputOneday():
    def __init__(self,year,month,day,place):
        '''
        year:(int)
        month:(int)
        day:(int)
        place:(str)
        '''
        self.year = year
        self.month = month
        self.day = day
        self.place = place
        self.DF = None
        self.count_change = 0#変更回数をカウント。12Rすべて取得できたら最終的に12になる。
    def OutputALLDFS(self):
        MakeURL = OutputURL(self.year,self.month,self.day,self.place)
        for i in range(1,13):#1日12レース
            result_url_ = MakeURL.OutputResultURL(i)
            try:#URLが開けない場合（例：中止）はスキップ
                html = urlopen(result_url_)#ここは意味ないかも。webサイト自体は存在するから
            except HTTPError as e:
                print(result_url_)
            except URLError as e:
                print(result_url_)
            else:
                try:
                    ResultWeb = ResultScraping(result_url_)
                except IndexError as e:
                    print(result_url_)
                except ValueError as e:
                    print(result_url_)
                else:
                    racetime = None
                    SingleDf = None
                    try:
                        SingleDf = ResultWeb.OutputResult()
                    except IndexError as e:
                        print(result_url_)
                    except ValueError as e:
                        print(result_url_)
                    else:                     
                        SingleDf = ResultWeb.OutputOtherInfo()
                        racelist_url = MakeURL.OutputRacelistURL(i)#結果のURLが開けるなら出走表のURLの開けると仮定
                        SingleDf = pd.merge(SingleDf,RacelistScraping(racelist_url), on='枠')
                        beforeinfo_url_ = MakeURL.OutputBeforeInfoURL(i)#結果のURLが開けるなら直前情報のURLの開けると仮定
                        SingleDf = pd.merge(SingleDf,JustInfoScraping(beforeinfo_url_), on='枠')
                        SingleDf['年'] = self.year
                        SingleDf['月'] = self.month
                        SingleDf['日'] = self.day
                        SingleDf['開催日'] = datetime(self.year,self.month,self.day)
                        SingleDf['開催場'] = self.place
                        SingleDf['レース番号'] = str(i)
                        racetime = ResultWeb.dfs[0].loc[0,str(i)+'R']
                        SingleDf['締切時刻'] = racetime
                        SingleDf['締切時刻(datetime)'] = datetime(self.year,self.month,self.day,int(racetime[:racetime.index(':')]),int(racetime[racetime.index(':')+1:]))
                        if i == 1:
                            self.DF = SingleDf
                        else:
                            self.DF = pd.concat([self.DF,SingleDf])
                        self.count_change += 1
            time.sleep(1)
        if self.count_change ==0:
            return None
        else:
            self.DF = self.DF.reindex(columns=['年',
                                               '月',
                                               '日',
                                               '開催日',
                                               '開催場',
                                               'レース番号',
                                               'レース名',
                                               'レースグレード',
                                               'レース種',
                                               '締切時刻',
                                               '締切時刻(datetime)',
                                               '距離',
                                               '安定版/進入固定',
                                               '着',
                                               '決まり手',
                                               '枠',
                                               '進入コース',
                                               '名前',
                                               '登録番号',
                                               '級別',
                                               '支部',
                                               '出身地',
                                               '年齢',
                                               '体重', 
                                               '調整重量', 
                                               'レースタイム',
                                               'レースタイム（秒）',
                                               'スタート情報', 
                                               '展示タイム', 
                                               '展示進入コース', 
                                               '展示スタートタイム', 
                                               'チルト', 
                                               'プロペラ', 
                                               '部品交換', 
                                               'F数', 
                                               'L数', 
                                               '平均スタートタイム', 
                                               '全国勝率', 
                                               '全国2連対率', 
                                               '全国3連対率', 
                                               '当地勝率', 
                                               '当地2連対率', 
                                               '当地3連対率', 
                                               'モーター番号', 
                                               'モーター2連対率', 
                                               'モーター3連対率', 
                                               'ボート番号', 
                                               'ボート2連対率', 
                                               'ボート3連対率', 
                                               '天候',
                                               '気温',
                                               '風速',
                                               '風向',
                                               '風種',
                                               '水温',
                                               '波高',
                                               '3連単',
                                               '3連複',
                                               '2連単',
                                               '2連複',
                                               '拡連複',
                                               '単勝',
                                               '複勝'])
            source_path = './各場データ/'+self.place+'BOATRACE競争データ.csv'#./はカレントディレクトリを表す。
            df_output = pd.read_csv(source_path,encoding='utf_8_sig')
            df_output = pd.concat([df_output,self.DF])
            df_output.to_csv('./各場データ/'+self.place+'BOATRACE競争データ.csv',encoding='utf_8_sig', index=False)
            # all_source_path = './全場BOATRACE競争データ.csv'#./はカレントディレクトリを表す。
            # df_all_output = pd.read_csv(all_source_path,encoding='utf_8_sig')
            # df_all_output = pd.concat([df_all_output,self.DF])
            # df_all_output.to_csv('./全場BOATRACE競争データ.csv',encoding='utf_8_sig', index=False)
            return self.DF

def daterange(_start, _end):
    day_list = []
    for n in range((_end - _start).days):
        day_list+= [_start + timedelta(n)]
    day_list += [_end]
    for i in range(len(day_list)):
        day_list[i] = [str(day_list[i].year),str(day_list[i].month),str(day_list[i].day)]
    return day_list


def date_list_output(start_day,finish_day):
    return daterange(datetime.strptime(start_day,'%Y-%m-%d'),datetime.strptime(finish_day,'%Y-%m-%d'))

class PeriodOutput():
    '''
    1日毎にファイルを更新していくので、途中でエラーが出ても、続きから集計を行える。
    '''
    def __init__(self,start_day,finish_day,place):
        '''
        start_day:(str) yyyy-mm-dd
        finish_day:(str) yyyy-mm-dd
        '''
        self.day_list = date_list_output(start_day,finish_day)
        self.place = place
        #self.place_list = ['桐生','戸田','江戸川','平和島','多摩川','浜名湖','蒲郡','常滑','津','三国','びわこ','住之江','尼崎','鳴門','丸亀','児島','宮島','徳山','下関','若松','芦屋','福岡','唐津','大村']
        #self.allplace_df = None#全場のデータフレーム
    def AllPlaceOutput(self):
        for i in range(len(self.day_list)):
            MakeOneDayResult = OutputOneday(int(self.day_list[i][0]),int(self.day_list[i][1]),int(self.day_list[i][2]),self.place)
            MakeOneDayResult.OutputALLDFS()

# ファイルの前準備
# 1. 同ディレクトリに"各場データ"というフォルダを作成
# 2. 同ディレクトリの"初期化.py"を実行
# 例
# 多摩川ボートレース場の2021年1月1日から2021年12月31日の全レースの競争成績を取得したい場合
# ↓
# a = PeriodOutput('2021-01-01','2021-12-31','多摩川')
# a.AllPlaceOutput()
