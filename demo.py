"""
@File: demo.py
@Brief: 一个小例子：读取成绩单中的一卡通号，查询对应姓名，输出到csv文件
@Author: Gol3vka
@Last Modified: 2023-04-27
"""

from multiprocessing.dummy import Pool
from time import time

import pandas as pd

from open_box import OpenBox


# 线程入口
def query(item):
    global ob, name_df, cnt
    index, row = item
    name = ob.id2name(row[0])
    name_df.loc[index] = [name]
    cnt += 1
    print(f'{cnt}/149')


# 计时开始
start = time()

# 初始化变量
ob = OpenBox(True)
name_df = pd.DataFrame(columns=['姓名'], index=range(149))
cnt = 0

# 从xls文件特定区域读取一卡通号
id_df = pd.read_excel('./in.xls', usecols=[1], skiprows=3, nrows=149, dtype=str)

# 多线程查询
pool = Pool(10)
pool.map(query, id_df.iterrows())

# 计时结束
end = time()
print(f'查询耗时：{end - start}s')

# 输出到csv文件
name_df.to_csv('./out.csv', index=False)
