import requests
import html
import time
import getpass
import os
import re
import sys
import platform
from lxml.html.soupparser import unescape
from bs4 import BeautifulSoup

class Sakai(object):
    """
    docstring for Sakai,
    this code is to get Sakai page for SUSTC students, they can get necessary
    information such as course slices or assignments from this modual
    """

    def __init__(self, username, password):
        """
        to init Sakai, username and password is in need
        """
        super(Sakai, self).__init__()
        self.headers = {
            "User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3)' +
                          ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/' +
                          '56.0.2924.87 Safari/537.36'}
        self.data = {
            'username': str(username),
            'password': str(password),
            #     'lt': lt,
            #     'excusion': execution,
            '_eventId': 'submit',
            'submit': 'LOGIN',
        }
        self.url = 'https://cas.sustc.edu.cn/cas/login?service=http%3A%2F%2Fjwxt.sustc.edu.cn%2Fjsxsd%2F'
        self.s = requests.session()
        # 第一次访问，用来获取lt和execution属性（每次登陆sakai都会变化，是一个防止爬虫的设置）
        r = self.s.get(self.url, headers = self.headers)
        content = r.content.decode('utf-8')
        # print(r.headers)
        # 得到lt和excution属性
        self.data['execution'] = self._get_execution(content)
        self.data['lt'] = self._get_lt(content)
        self.loggedIn = False
        self.topped_sites = {}
        self.other_sites = {}
        self.sites = {}

    def _get_execution(self, content):
        formula = '<input.*?name="execution".*?value="(.*?)" />'
        pattern = re.compile(formula)
        return re.findall(pattern, content)[0]

    def _get_lt(self, content):
        formula = '<input.*?name="lt".*?value="(.*?)" />'
        pattern = re.compile(formula)
        return re.findall(pattern, content)[0]

    def login(self):
        self.s.post(self.url, self.data)
        text = self._get_home_page()

        self.loggedIn = "学生个人中心" in text
        if self.loggedIn:
            self.soup = BeautifulSoup(text, 'lxml')
        print(text)
        return self.loggedIn

    def _check_logged(self):
        if not self.loggedIn:
            print('not logged in, permission denied')
        return self.loggedIn

    def _get_home_page(self):
        self.s.get('http://jwxt.sustc.edu.cn/jsxsd/xsxk/xsxk_index?jx0502zbid=054B5FA7E55F44E0BB3D24DB3BC561')
        r = self.s.get('http://jwxt.sustc.edu.cn/jsxsd')
        text = r.content.decode('utf-8')
        txt = unescape(text)
        return txt

    def get_main_page(self, url):
        r = self.s.get(url)
        print(r.text)


if __name__ == '__main__':
    sakai = Sakai(11510237, 310034)
    if not sakai.login():
        raise Exception('Failed to login, please check your password or network') 
    sakai.get_main_page('http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/comeInFawxk')
