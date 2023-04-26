"""
@File: open_box.py
@Brief: 盒武器，需要使用自己的账号登录系统，可以通过姓名或一卡通号查询人员信息
@Author: Gol3vka
@Last Modified: 2023-04-26
"""

import js2py
import json
import requests
from bs4 import BeautifulSoup

# 关闭https警告
requests.packages.urllib3.disable_warnings()


class OpenBox:
    def __init__(self, debug=False):
        # 读取配置文件
        config_path = './config{}.json'.format('_local' if debug else '')
        with open(config_path) as file:
            config = json.load(file)
        self.id_ = config['id']
        self.password_ = config['password']
        self.headers_ = config['headers']
        self.login_urls_ = config['login_urls']
        self.query_urls_ = config['query_urls']

        # 登录
        self.session_obj = self._login()

    @staticmethod
    def _encrypt_AES(plain_text: str, salt: str) -> str:
        """AES加密，需要调用encrypt.js"""
        with open('./encrypt.js') as file:
            js_content = file.read()
        js_obj = js2py.EvalJs()
        js_obj.execute(js_content)
        cipher = js_obj.encryptAES(plain_text, salt)
        return cipher

    def _login(self) -> requests.Session:
        """通过统一身份认证登录

        Returns:
            requests.Session: 成功登录后的session对象
        """
        # 定义session对象
        session_obj = requests.Session()
        session_obj.verify = False
        session_obj.allow_redirects = True
        session_obj.headers.update(self.headers_)

        # 获取登录页面表单，解析隐藏输入框信息
        try:
            response = session_obj.get(self.login_urls_[0])
        except requests.exceptions.ConnectionError:
            raise ConnectionError('无法连接到统一身份认证平台，请检查网络连接和DNS设置')
        soup = BeautifulSoup(response.text, 'html.parser')
        hidden_inputs = soup.select('[tabid="01"] input[type="hidden"]')

        # 构建登录信息
        login_data = {'username': self.id_}
        for element in hidden_inputs:
            if element.has_attr('name'):
                login_data[element['name']] = element['value']
            elif element.has_attr('id'):
                login_data[element['id']] = element['value']
        login_data['password'] = self._encrypt_AES(self.password_, login_data['pwdDefaultEncryptSalt'])

        # 提交登录信息（频繁登录存在验证码，无法解决）
        response = session_obj.post(self.login_urls_[1], data=login_data)
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', id='casLoginForm')
        if form is not None:
            msg = form.find('span', id='msg').text.strip()
            raise ConnectionError(f'登录失败，{msg}')

        # 涉及到vpn和多个跳转
        session_obj.get(self.login_urls_[2])
        response = session_obj.get(self.login_urls_[3])
        soup = BeautifulSoup(response.text, 'html.parser')
        i = soup.find('i', class_='layui-icon layui-icon-username')
        if i is None:
            raise ConnectionError('登录失败')
        username = i.parent.text.strip()
        if username == '游客':
            raise ConnectionError('登录失败')
        print('登录成功')

        # 登录成功，可以使用该session进行查询
        return session_obj

    def _query(self, keyword: str, is_student: bool = True) -> str:
        """查询一卡通号或姓名对应的信息

        Args:
            keyword(str): 查询关键字，一卡通号或姓名
            is_student(bool): 是否为学生，否则为教职工

        Returns:
            str: 得到的响应，json字符串
        """
        # 学生和教职工的查询接口不同
        query_url = self.query_urls_[0] if is_student else self.query_urls_[1]
        response = self.session_obj.get(query_url.format(keyword))
        return response.text

    @staticmethod
    def _parse_response(response: str, is_student: bool = True) -> list:
        """从响应中解析详细信息

        Args:
            response(str): 待解析的响应，json字符串
            is_student(bool): 是否为学生，否则为教职工

        Returns:
            list: 列表项数等于查询结果数，每一项为包含详细信息的字典，学生与教职工有区别
        """
        response_json = json.loads(response)
        num = len(response_json['data'])
        print(f'共找到{num}条记录')
        info = [dict() for _ in range(num)]
        for i in range(num):
            data = response_json['data'][i]
            if is_student:
                info[i] = {'姓名': data['xm'],
                           '性别': data['xb']['mc'] if data['xb'] else None,
                           '政治面貌': data['zzmm']['mc'] if data['zzmm'] else None,
                           '入学年份': data['rxnf'],
                           '学制': data['xz'] + '年',
                           '学院': '[{}]{}-{}'.format(data['xy']['px'], data['xy']['mc'], data['xy']['ywmc']),
                           '学号-分流前': data['id'],
                           '学号-分流后': data['ykth'],
                           '一卡通号': data['xh']}
            else:
                info[i] = {'姓名': data['xm'],
                           '性别': data['xb'],
                           '出生日期': data['csrq'],
                           '政治面貌': data['zzmm']['mc'] if data['zzmm'] else None,
                           '学院': '[{}]{}-{}'.format(data['xy']['px'], data['xy']['mc'], data['xy']['ywmc']),
                           '工号': data['gh'],
                           '联系电话': data['lxdh'],
                           '邮箱': data['dzxx']}
        return info

    def id2name(self, query_id: str, is_student: bool = True) -> str:
        """一卡通号 -> 姓名

        Args:
            query_id(str): 待查询一卡通号
            is_student(bool): 是否为学生，否则为教职工

        Returns:
            str: 姓名，不存在时返回'null'
        """
        response = self._query(query_id, is_student)
        response_json = json.loads(response)
        return response_json['data'][0]['xm'] if response_json['data'] else 'null'

    def id2info(self, query_id: str, is_student: bool = True) -> dict:
        """一卡通号 -> 详细信息

        Args:
            query_id(str): 待查询一卡通号
            is_student(bool): 是否为学生，否则为教职工

        Returns:
            dict: 包含详细信息的字典（默认一个一卡通号只能查询到一个结果）
        """
        response = self._query(query_id, is_student)
        info = self._parse_response(response, is_student)
        return info[0]

    def name2info(self, query_name: str, is_student: bool = True) -> list:
        """姓名 -> 详细信息

        Args:
            query_name(str): 待查询姓名
            is_student(bool): 是否为学生，否则为教职工

        Returns:
            list: 列表项数等于查询结果数，每一项为包含详细信息的字典，学生与教职工有区别
        """
        response = self._query(query_name, is_student)
        info = self._parse_response(response, is_student)
        return info


if __name__ == '__main__':
    # 涉及隐私，不提供测试数据
    ob = OpenBox(True)
    print(ob.id2name('xx', True))
    print(ob.id2name('xx', False))
    print(ob.id2info('xx', True))
    print(ob.id2info('xx', False))
    print(ob.name2info('xx', True))
    print(ob.name2info('xx', False))
