# ![1f5c2](./README.assets/1f5c2.gif) SEU-Open-Box

同学你好，我是学校领导，你写的小作文针砭时弊、振聋发聩，我们深感惭愧。为了奖勋你，请把你的学号和姓名告诉我，给你加创新学分 :hugs::hugs::hugs:

## 目录

- [ SEU-Open-Box](#-seu-open-box)
  - [目录](#目录)
  - [免责声明](#免责声明)
  - [隐私声明](#隐私声明)
  - [目录结构](#目录结构)
  - [使用说明](#使用说明)
    - [1. 创建虚拟环境【可选】](#1-创建虚拟环境可选)
    - [2. 安装依赖](#2-安装依赖)
    - [3. 配置文件](#3-配置文件)
    - [4. 调用 OpenBox 类](#4-调用-openbox-类)
    - [5. 使用示例](#5-使用示例)
  - [许可证](#许可证)

## 免责声明

1. 本项目所使用到的查询接口合法合规，属于学校系统提供的正常可见服务，在校学生均可通过浏览器正常访问查询。

2. 用户在使用本项目时应遵守相关法律法规，不得利用本项目从事任何违法违规行为。用户应自行对使用风险进行全面评估，对行为负责。

3. 查询结果用途取决于用户行为，若因用户个人行为违法导致的法律纠纷或其他后果，作者不承担任何责任。

4. 本项目仅供参考，对于获取信息不准确、不完整或错误，作者不承担任何责任。

使用本项目即视为接受本免责声明的所有条款。拥护网络安全，自觉遵守法律法规，是每个公民应尽的义务。

## 隐私声明

用户登录信息（包括一卡通和密码）只在本地存储，仅用于登录统一身份认证平台。

本项目不会收集和上传用户登录信息、查询结果到学校系统以外的服务器。

## 目录结构

```c
SEU-Open-Box
    ├── open_box.py         // OpenBox 类
    ├── demo.py             // 使用示例
    ├── config.json         // 配置文件
    ├── encrypt.js          // 加密脚本
    ├── requirements.txt    // 依赖
    ├── README.md           // 说明文档
    └── LICENSE             // 许可证
```

## 使用说明

### 1. 创建虚拟环境【可选】

- venv

    ```bash
    cd /...path to.../SEU-Open-Box
    python -m venv open-box
    ./open-box/Scripts/activate
    ```

- conda

    ```bash
    conda create -n open-box
    conda activate open-box
    ```

- 略

### 2. 安装依赖

```bash
cd /...path to.../SEU-Open-Box
pip install -r ./requirements.txt
```

### 3. 配置文件

打开 [`config.json`](./config.json) 文件，在 `id` 和 `password` 字段分别填写您的一卡通号和登录密码，例如：

```json
{
  "id": "12345678",
  "password": "P455w0rd",
  "...": "..."
}
```

:warning: **请勿修改 `password` 字段之后的内容！**

如果您有上传到代码仓库的需求，为避免登录信息泄露，建议您复制 [`config.json`](./config.json) 文件并重命名为 `config_local.json` 来配置一卡通号和密码，并在接下来类实例化时传入参数 `debug=True`：

```python
ob = OpenBox(debug=True)
```

debug 模式下会使用 `config_local.json` 作为配置文件，该文件包含在了 [`.gitignore`](./.gitignore) 中，不会被上传到代码仓库。

### 4. 调用 OpenBox 类

```python
##### 导入 OpenBox 类 #####
from open_box import OpenBox


##### 创建 OpenBox 类实例 #####
# 在 __init__() 方法中会完成登录
# 成功会打印“登录成功”
# 失败会抛出异常，注意查看异常信息，可能出错的情况有：
#   1. 配置文件中的账号密码错误
#   2. 频繁登录触发验证，手动从浏览器登录一次大概能解决
#   3. DNS 问题，找不到 vpn.seu.edu.cn 的地址
ob = OpenBox()
# ob = OpenBox(debug=True)  # debug 模式，使用 config_local.json 作为配置文件，详见上一部分内容


##### 调用类方法 #####
# 以下方法中的第二个参数含义相同，均为：查询对象是否为学生，默认为True
# 通过一卡通号查询姓名，返回 str 或 None
print(ob.id2name('【一卡通号】', True))
print(ob.id2name('【一卡通号】', False))

# 通过一卡通号查询详细信息，返回 dict 或 None
print(ob.id2info('【一卡通号】', True))
print(ob.id2info('【一卡通号】', False))

# 通过姓名查询详细信息，查询结果可能不唯一，返回包含多个 dict 的 list 或 [None]
print(ob.name2info('【姓名】', True))
print(ob.name2info('【姓名】', False))
```

### 5. 使用示例

[`demo.py`](./demo.py) 是一个使用示例：读取 excel 文件 `in.xls` 中特定区域的一卡通号，使用 OpenBox 类多线程查询姓名，将结果按照对应的顺序写入文件 `out.csv` 中。

```python
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
```

涉及隐私信息，不提供测试文件和输出结果，仅供参考。

## 许可证

[GNU LESSER GENERAL PUBLIC LICENSE v2.1 © Gol3vka.](./LICENSE)
