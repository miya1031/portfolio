# 用途
# ボートレース競争成績取得.pyにより取得した競走データに「性別」「シリーズ」の項目を追加する。

# ディレクトリ「./各場データ/」にボートレース競争成績取得.pyにより取得した
# 各場の競走データが「（開催場）+'BOATRACE競争データ.csv'」が格納されていることを前提とする。

# ファイルの前準備
#  同ディレクトリに"性別データ"と"シリーズデータ"と"各場データ_性別シリーズ追加"というフォルダを作成

##################################################
#
# 1. 性別データ
#
##################################################

# 関数 OutputSex を用いると
# 指定した日・開催場の性別データを出力できる。
# 例
# 宮島ボートレースの2022年5月29日の性別データを取得し、保存したい
# ↓
# OutputSex(2022,5,29,'宮島',True)

# クラス AttachSexData() を用いると
# 指定した開催場のディレクトリ「./各場データ/」に格納されているデータ期間の
# 性別データをディレクトリ「./性別データ/」に「'【性別データ】'+（開催場）+'BOATRACE競争データ.csv'」
# として保存できる
# 例
# 宮島ボートレースについて競走データを取得している期間の性別データを取得し、保存したい
# ↓
# Data = AttachSexData('宮島','宮島BOATRACE競争データ.csv')
# Data.search_file()

import pandas as pd
import os 
import requests
from bs4 import BeautifulSoup

def OutputSex(year,month,day,place,flag=False):
    '''
    年月日と開催場を入力すると、指定日の指定開催場でのレース毎の枠と名前と性別を格納したDataFrameを出力

    (input)
    year(int):年
    month(int):月
    day(int):日
    place(str):開催場
    flag(bool):ファイルに保存するかの判定

    参照するURL例
    2022年5月29日 宮島
    https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=17&hd=20220529
    '''
    place_labels = ['桐生','戸田','江戸川','平和島','多摩川','浜名湖','蒲郡','常滑','津','三国','びわこ','住之江','尼崎','鳴門','丸亀','児島','宮島','徳山','下関','若松','芦屋','福岡','唐津','大村']
    p_num = str(place_labels.index(place)+1).zfill(2)
    raceindex_url = 'https://www.boatrace.jp/owpc/pc/race/raceindex?jcd='+p_num+'&hd='+str(year)+str(month).zfill(2)+str(day).zfill(2)
    r = requests.get(raceindex_url)
    soup = BeautifulSoup(r.content,'html.parser')
    table = soup.find_all('td')
    sex_list = []
    name_list = []
    race_num = [[i,i,i,i,i,i] for i in range(1,13)]
    race_num = [x for row in race_num for x in row]
    waku_num = [[1,2,3,4,5,6] for i in range(12)]
    waku_num = [x for row in waku_num for x in row]
    for t in table:
        if not t.find('div',class_='is-empty') is None:
            sex_list += ['男']
            name_list += [t.find('a').string]
        elif not t.find('div',class_='is-lady') is None:
            sex_list += ['女']
            name_list += [t.find('a').string]
    if (len(sex_list)!=72)|(len(name_list)!=72):#ある開催場で1日に出走する選手数は72人（重複あり）
        print(raceindex_url)
    df = pd.DataFrame(list(zip(race_num,waku_num,name_list,sex_list)), columns = ['レース番号','枠','名前','性別'])
    df['年'] = year
    df['月'] = month
    df['日'] = day
    df['開催場'] = place
    if flag:
        df = df.reindex(columns=['年', '月', '日', '開催場', 'レース番号', '枠', '名前', '性別'])
        df.to_csv('./'+str(year)+str(month).zfill(2)+str(day).zfill(2)+place+'性別データ.csv',encoding='utf_8_sig', index=False)
    return df

class AttachSexData():
    def __init__(self,place,file_name):
        self.place = place
        self.file_name = file_name
        place_labels = ['桐生','戸田','江戸川','平和島','多摩川','浜名湖','蒲郡','常滑','津','三国','びわこ','住之江','尼崎','鳴門','丸亀','児島','宮島','徳山','下関','若松','芦屋','福岡','唐津','大村']
        self.p_num = str(place_labels.index(place)+1).zfill(2)
        self.df_seiseki = pd.read_csv('./各場データ/'+file_name,encoding='utf_8_sig')
        self.df_seiseki['開催日'] = pd.to_datetime(self.df_seiseki['開催日'])
        #self.df_seiseki['締切時刻(datetime)'] = pd.to_datetime(self.df_seiseki['締切時刻(datetime)'])
        attach_path = './性別データ/【性別データ】'+file_name
        if os.path.exists(attach_path):#既に性別データファイルがある場合、結合できるようにするため場合分け
            self.df_attach = pd.read_csv(attach_path,encoding='utf_8_sig')
            self.df_attach['開催日'] = pd.to_datetime(self.df_attach['開催日'])
            #self.df_attach['締切時刻(datetime)'] = pd.to_datetime(self.df_attach['締切時刻(datetime)'])
        else:
            self.df_attach = None
    
    def search_file(self):
        '''
        既に取得したデータを重複して取得しないように注意
        '''
        
        if self.df_attach is None:
            self.df_seiseki = self.df_seiseki.drop_duplicates(subset='開催日')
            #print(self.df_seiseki.head())
        else:
            time_list = self.df_seiseki['開催日'].unique()
            time_list_ = self.df_attach['開催日'].unique()
            time_list = list(set(time_list)^set(time_list_))
            self.df_seiseki = self.df_seiseki[self.df_seiseki['開催日'].isin(time_list)]
            #print(self.df_seiseki.head())
            self.df_seiseki = self.df_seiseki.drop_duplicates(subset='開催日')
        
        self.df_seiseki = self.df_seiseki.reset_index(drop=True)#index降りなおし 
        
        if len(self.df_seiseki) == 0:
            return None
        
        for i in range(len(self.df_seiseki)):
            try :
                df = OutputSex(self.df_seiseki.loc[i,'年'],self.df_seiseki.loc[i,'月'],self.df_seiseki.loc[i,'日'],self.place)
            except URLError as e:
                break
            else:
                df['開催日'] = self.df_seiseki.loc[i,'開催日']
                #print(df.head())
                if i == 0:
                    df_sex = df
                else:
                    df_sex = pd.concat([df_sex,df])
        df_sex = df_sex.reindex(columns=['年', '月', '日', '開催日', '開催場', 'レース番号', '枠', '名前', '性別'])
        if self.df_attach is None:
            df_sex.to_csv('./性別データ/【性別データ】'+self.file_name,encoding='utf_8_sig', index=False)
        else:
            df_sex = pd.concat([self.df_attach,df_sex])
            df_sex.to_csv('./性別データ/【性別データ】'+self.file_name,encoding='utf_8_sig', index=False)
        
        return df_sex


##################################################
#
# 2. シリーズデータ
#
##################################################

#　問題点
#　同じ月に違う場で同じ冠のレース名が存在する場合がある。
#　例：2022年5月にマクール杯が多摩川と三国で開催される。
#　よって、シリーズファイルに　年：2022　月：5　シリーズ：マクール杯　のデータが2つ出力されてしまう。
#　→どうにか開催場を特定できないか
#　→重複するレース名はおそらく全部「一般」であるので、重複削除してしまえばよいか

# 関数 OutputSeries を用いると
# 指定した年月のシリーズデータを出力できる。
# 例
# 2022年5月のシリーズデータを取得し、保存したい
# ↓
# OutputSeries(2022,5,True)

# クラス AttachSeriesData() を用いると
# ディレクトリ「./各場データ/」に格納されている全場のデータのデータ期間（開催場は指定できない）の
# シリーズデータをディレクトリ「./シリーズデータ/」に「'【シリーズデータ】全場.csv'」
# として保存できる
# 例
# 競走データを取得している期間のシリーズデータを取得し、保存したい
# ↓
# Data = AttachSeriesData()
# Data.search_file()

def OutputSeries(year,month,flag=False):
    raceindex_url = 'https://www.boatrace.jp/owpc/pc/race/monthlyschedule?ym='+str(year)+str(month).zfill(2)
    r = requests.get(raceindex_url)
    soup = BeautifulSoup(r.content,'html.parser')
    str_list = ['Ippan','G3','G2','G1','SG','Lady','Venus','Rookie','Takumi']
    str_list = ["is-gradeColor"+i for i in str_list]
    class_list = ['一般','G3','G2','G1','SG','オールレディース','ヴィーナスシリーズ','ルーキーシリーズ','マスターズリーグ']
    r_name = []
    r_grade = []
    for str_,grade_ in zip(str_list,class_list):
        l = soup.find_all('td', class_=str_)
        for el in l:
            if not el.string is None:
                r_name += [el.string]
                r_grade += [grade_]
    df = pd.DataFrame(list(zip(r_name,r_grade)), columns = ['レース名','シリーズ'])
    df['年'] = year
    df['月'] = month
    df = df.drop_duplicates()#重複削除・上記の問題点を解決するため
    if flag:
        df = df.reindex(columns=['年', '月', 'レース名', 'シリーズ'])
        df.to_csv('./シリーズデータ/'+str(year)+str(month).zfill(2)+'シリーズデータ.csv',encoding='utf_8_sig', index=False)
    return df

def get_unique_list(seq):
    '''
    2次元配列の重複削除
    '''
    seen = []
    return [x for x in seq if x not in seen and not seen.append(x)]

def sub_list(a,b):
    '''
    2次元配列の引き算
    b⊆aでないと作動しない
    '''
    return [x for x in a if x not in b]

class AttachSeriesData():
    def __init__(self):
        '''
        【シリーズデータ】ファイルの最近の年月を取得
        全場のデータの最新の年月を取得
        年月の重複削除を行←どちらもこの方法で
        '''
        self.list_seiseki = []#['年','月']を格納するリスト
        for place in ['桐生','戸田','江戸川','平和島','多摩川','浜名湖','蒲郡','常滑','津','三国','びわこ','住之江','尼崎','鳴門','丸亀','児島','宮島','徳山','下関','若松','芦屋','福岡','唐津','大村']:
            df_seiseki = pd.read_csv('./各場データ/'+place+'BOATRACE競争データ.csv',encoding='utf_8_sig')
            df_seiseki = df_seiseki.drop_duplicates(subset=['年','月'])
            df_seiseki = df_seiseki.reset_index(drop=True)#index降りなおし
            for i in range(len(df_seiseki)):
                self.list_seiseki += [[df_seiseki.loc[i,'年'],df_seiseki.loc[i,'月']]]
            self.list_seiseki = get_unique_list(self.list_seiseki)
        attach_path = './シリーズデータ/【シリーズデータ】全場.csv'
        if os.path.exists(attach_path):#既に観測データファイルがある場合、結合できるようにするため場合分け
            l = []
            self.df_attach = pd.read_csv(attach_path,encoding='utf_8_sig')
            df_attach = pd.read_csv(attach_path,encoding='utf_8_sig')
            df_attach = df_attach.drop_duplicates(subset=['年','月'])
            df_attach = df_attach.reset_index(drop=True)#index振り直し
            for i in range(len(df_attach)):
                l += [[df_attach.loc[i,'年'],df_attach.loc[i,'月']]]
            l = get_unique_list(l)
            self.list_seiseki = sub_list(self.list_seiseki,l)
        else:
            self.df_attach = None
            
    
    def search_file(self):        
        if len(self.list_seiseki) == 0:
            return None
        
        for pair in self.list_seiseki:
            try :
                df = OutputSeries(pair[0],pair[1])
            except URLError as e:
                break
            else:
                if pair == self.list_seiseki[0]:
                    df_series = df
                else:
                    df_series = pd.concat([df_series,df])
        df_series = df_series.reindex(columns=['年', '月', 'レース名', 'シリーズ'])
        if self.df_attach is None:
            df_series.to_csv('./シリーズデータ/【シリーズデータ】全場.csv',encoding='utf_8_sig', index=False)
        else:
            df_series = pd.concat([self.df_attach,df_series])
            df_series.to_csv('./シリーズデータ/【シリーズデータ】全場.csv',encoding='utf_8_sig', index=False)
        
        return df_series

##################################################
#
# 3. 性別・シリーズデータを競走データに結合
#
##################################################

# 1,2 で紹介した関数・クラスを用いて、性別・シリーズデータを競走データに結合する

# 関数 AttachSexSeries を用いると、指定した開催場の競走データ（ディレクトリ「./各場データ/」に保存されているデータ）に
# 性別・シリーズデータを結合し、ディレクトリ「./各場データ_性別シリーズ追加/」に「（開催場）+'BOATRACE競争データ_ver2.csv'」
# として保存できる
# 例
# 宮島ボートレースの競争データに性別・シリーズデータを結合し、保存したい
# ↓
# AttachSexSeries('宮島')

# 関数 AttachSexSeriesAll を用いると全24場に対し、関数 AttachSexSeries を実行できる

def AttachSexSeries(place):
    sex = AttachSexData(place,place+'BOATRACE競争データ.csv')
    sex.search_file()
    df_seiseki = pd.read_csv('./各場データ/'+place+'BOATRACE競争データ.csv',encoding='utf_8_sig')
    df_sex = pd.read_csv('./性別データ/【性別データ】'+place+'BOATRACE競争データ.csv',encoding='utf_8_sig')
    df_sex = df_sex.drop(columns=['開催日', '開催場', '名前'])
    df_series = pd.read_csv('./シリーズデータ/【シリーズデータ】全場.csv',encoding='utf_8_sig')
    df_seiseki = pd.merge(df_seiseki,df_sex,on=['年','月','日','レース番号','枠'])
    df_seiseki = pd.merge(df_seiseki,df_series,on=['年','月','レース名'])
    df_seiseki.to_csv('./各場データ_性別シリーズ追加/'+place+'BOATRACE競争データ_ver2.csv',encoding='utf_8_sig',index=False)

def AttachSexSeriesAll():
    series = AttachSeriesData()
    series.search_file()
    for place in ['桐生','戸田','江戸川','平和島','多摩川','浜名湖','蒲郡','常滑','津','三国','びわこ','住之江','尼崎','鳴門','丸亀','児島','宮島','徳山','下関','若松','芦屋','福岡','唐津','大村']:
    #for i in ['多摩川','浜名湖','常滑','宮島','下関','若松','唐津','大村']:
        AttachSexSeries(place)