import re
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QStandardItem
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
from PyQt5 import uic
from PyQt5 import sip
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
import pymysql
import sqlalchemy
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

font_path = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
font_name = font_manager.FontProperties(fname=font_path).get_name()
matplotlib.rc('font', family=font_name)


form_class = uic.loadUiType("school_app.ui")[0]

class schoolApp(QMainWindow, form_class):
    BORDER_LINES = [
        [(3, 2), (5, 2), (5, 3), (9, 3), (9, 1)],  # 인천
        [(2, 5), (3, 5), (3, 4), (8, 4), (8, 7), (7, 7), (7, 9), (4, 9), (4, 7), (1, 7)],  # 서울
        [(1, 6), (1, 9), (3, 9), (3, 10), (8, 10), (8, 9),
         (9, 9), (9, 8), (10, 8), (10, 5), (9, 5), (9, 3)],  # 경기도
        [(9, 12), (9, 10), (8, 10)],  # 강원도
        [(10, 5), (11, 5), (11, 4), (12, 4), (12, 5), (13, 5),
         (13, 4), (14, 4), (14, 2)],  # 충청남도
        [(11, 5), (12, 5), (12, 6), (15, 6), (15, 7), (13, 7),
         (13, 8), (11, 8), (11, 9), (10, 9), (10, 8)],  # 충청북도
        [(14, 4), (15, 4), (15, 6)],  # 대전시
        [(14, 7), (14, 9), (13, 9), (13, 11), (13, 13)],  # 경상북도
        [(14, 8), (16, 8), (16, 10), (15, 10),
         (15, 11), (14, 11), (14, 12), (13, 12)],  # 대구시
        [(15, 11), (16, 11), (16, 13)],  # 울산시
        [(17, 1), (17, 3), (18, 3), (18, 6), (15, 6)],  # 전라북도
        [(19, 2), (19, 4), (21, 4), (21, 3), (22, 3), (22, 2), (19, 2)],  # 광주시
        [(18, 5), (20, 5), (20, 6)],  # 전라남도
        [(16, 9), (18, 9), (18, 8), (19, 8), (19, 9), (20, 9), (20, 10)],  # 부산시
    ]

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()
        self.fill_combobox_2()

        self.df_all = pd.read_csv('school_data.csv', encoding='utf-8')
        self.conn = pymysql.connect(host='localhost',
                               port=3306,
                               user='root',
                               password='160813',
                               db='school_map')
        self.cur = self.conn.cursor()

        self.write_table_mysql(self.df_all)
        self.df_elem, self.df_junior, self.df_high = self.split_data(self.df_all)
        self.draw_map = self.make_map_data()

        self.pushButton.clicked.connect(self.search)

    def search(self):
        school = self.comboBox.currentText()
        area = self.comboBox_2.currentText()
        if area == '전국':
            area = ''
        if school == '초등학교':
            data = self.merge_data(self.draw_map, self.df_elem)
            final_data = self.searched_data(data, area)
            self.draw_blockMap(final_data, 'count', area + ' ' + school + ' 수', 'Blues')
        elif school == '중학교':
            data = self.merge_data(self.draw_map, self.df_junior)
            final_data = self.searched_data(data, area)
            self.draw_blockMap(final_data, 'count', area + ' ' + school + ' 수', 'Blues')
        elif school == '고등학교':
            data = self.merge_data(self.draw_map, self.df_high)
            final_data = self.searched_data(data, area)
            self.draw_blockMap(final_data, 'count', area + ' ' + school + ' 수', 'Blues')

        pix_map = QPixmap('./data_result/' + 'blockMap_' + 'count' + '.png')
        self.label.setPixmap(pix_map)
        self.label.setScaledContents(True)

    def fill_combobox_2(self):
        names = ['강원도', '경기도', '경상남도', '경상북도', '광주광역시', '대구광역시', '대전광역시', '부산광역시',
       '서울특별시', '세종특별자치시', '울산광역시', '인천광역시', '전라남도', '전라북도', '제주특별자치도',
       '충청남도', '충청북도']
        self.comboBox_2.addItem('전국')
        for name in names:
            self.comboBox_2.addItem(name)

    def split_data(self, df_all):
        df_all = df_all[['학제', '학교 세부 유형', '시도', '교육지원청', '도로명주소']]
        df_all['시도'].unique()
        change_value = {'서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시', '인천': '인천광역시',
                        '광주': '광주광역시', '대전': '대전광역시', '울산': '울산광역시', '세종': '세종특별자치시',
                        '경기': '경기도', '강원': '강원도', '충북': '충청북도', '충남': '충청남도',
                        '전북': '전라북도', '전남': '전라남도', '경북': '경상북도', '경남': '경상남도', '제주': '제주특별자체도'}
        df_all.replace(change_value, inplace=True)
        df_elem = pd.DataFrame(df_all[df_all['학제'] == '초등학교'])
        df_elem = df_elem.reset_index(drop=True)
        df_elem['count'] = 1
        new_df_elem = df_elem.groupby(by=['시도', '교육지원청'], as_index=False).sum()
        new_df_elem['시도군구'] = new_df_elem.apply(lambda r: r['시도'] + ' ' + r['교육지원청'], axis=1)
        new_df_elem = new_df_elem.set_index("시도군구")

        df_junior = pd.DataFrame(df_all[df_all['학제'] == '중학교'])
        df_high = pd.DataFrame(df_all[df_all['학제'] == '고등학교'])
        df_junior = df_junior.reset_index(drop=True)
        df_junior['count'] = 1
        df_high = df_high.reset_index(drop=True)
        df_high['count'] = 1

        new_df_junior = df_junior.groupby(by=['시도', '교육지원청'], as_index=False).sum()
        new_df_high = df_high.groupby(by=['시도', '교육지원청'], as_index=False).sum()

        new_df_junior['시도군구'] = new_df_junior.apply(lambda r: r['시도'] + ' ' + r['교육지원청'], axis=1)
        new_df_junior = new_df_junior.set_index("시도군구")

        new_df_high['시도군구'] = new_df_high.apply(lambda r: r['시도'] + ' ' + r['교육지원청'], axis=1)
        new_df_high = new_df_high.set_index("시도군구")

        return new_df_elem, new_df_junior, new_df_high

    def make_map_data(self):
        path = os.getcwd()
        data_draw_korea = pd.read_csv(path + '/data_draw_korea.csv', index_col=0, encoding='UTF-8', engine='python')
        data_draw_korea['시도군구'] = data_draw_korea.apply(lambda r: r['광역시도'] + ' ' + r['행정구역'], axis=1)
        data_draw_korea = data_draw_korea.set_index("시도군구")

        return data_draw_korea

    def merge_data(self, df1, df2):
        merged_data = pd.merge(df1, df2, how='outer', left_index=True, right_index=True)
        merged_data.dropna(axis=0, inplace=True)
        return merged_data

    def searched_data(self, merged_data, search_word):
        sel_merged_data = merged_data.copy()
        if search_word:
            new_count = merged_data['count'].where(merged_data['광역시도'] == search_word, other=0)
            sel_merged_data['count'] = new_count
        return sel_merged_data

    def draw_blockMap(self, blockedMap, targetData, title, color):
        whitelabelmin = (max(blockedMap[targetData]) - min(blockedMap[targetData])) * 0.25 + min(blockedMap[targetData])
        datalabel = targetData
        vmin = min(blockedMap[targetData])
        vmax = max(blockedMap[targetData])
        mapdata = blockedMap.pivot(index='y', columns='x', values=targetData)
        masked_mapdata = np.ma.masked_where(np.isnan(mapdata), mapdata)
        plt.figure(figsize=(8, 13))
        plt.title(title)
        plt.pcolor(masked_mapdata, vmin=vmin, vmax=vmax, cmap=color, edgecolor='#aaaaaa', linewidth=0.5)
        for idx, row in blockedMap.iterrows():
            annocolor = 'white' if row[targetData] > whitelabelmin else 'black'
            if row['광역시도'].endswith('시') and not row['광역시도'].startswith('세종'):
                dispname = '{}\n{}'.format(row['광역시도'][:2], row['행정구역'][:-1])
                if len(row['행정구역']) <= 2:
                    dispname += row['행정구역'][-1]
            else:
                dispname = row['행정구역'][:-1]

            dispname += "\n" + str(int(row['count']))

            if len(dispname.splitlines()[-1]) >= 3:
                fontsize, linespacing = 8.5, 1.3
            else:
                fontsize, linespacing = 8.5, 1.3

            plt.annotate(dispname, (row['x'] + 0.5, row['y'] + 0.5), weight='bold',
                         fontsize=fontsize, ha='center', va='center', color=annocolor,
                         linespacing=linespacing)
        for path in self.BORDER_LINES:
            ys, xs = zip(*path)
            plt.plot(xs, ys, c='black', lw=4)

        plt.gca().invert_yaxis()
        # plt.gca().set_aspect(1)
        plt.axis('off')
        cb = plt.colorbar(shrink=.1, aspect=10)
        cb.set_label(datalabel)
        plt.tight_layout()
        plt.savefig('./data_result/' + 'blockMap_' + targetData + '.png')


    def write_table_mysql(self, df):
        try:
            # {user}:{pw}@localhost/{db}
            engine = sqlalchemy.create_engine("mysql+pymysql://root:160813@localhost/school_map")
            df.to_sql('school_data', engine)
        except ValueError:
            print("Table already exists.")


    def initUI(self):
        self.setWindowTitle('전국 초중고 찾기')
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = schoolApp()
    form.show()
    sys.exit(app.exec_())