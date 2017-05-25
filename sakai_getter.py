__author__ = 'Boris'
# encode = utf-8
# this code is written and designed by Boris, 2017.3.28.
# without permission, this code cannot be modified or copied
# for any other uses.
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

time__ = 0

class Site(object):

    def __init__(self, name, url, session):
        self.name = name
        self.url = url + '/'
        self.session = session
        self.db = self.get_db(url)
        

    def get_db(self, url):
        pattern = re.compile('/site/(.*?)$')
        return re.findall(pattern, url)[0]

    def __str__(self):
        return ('name: {}, url: {} , session: {}'.format(self.name,
                + self.url, + self.session))


class Sakai(object):
    """
    docstring for Sakai,
    this code is to get Sakai page for SUSTC students, they can get necessary
    information such as course slices or assignments from this modual
    """

    def __init__(self, username, password, path):
        """
        to init Sakai, username and password is in need
        """
        super(Sakai, self).__init__()
        self.path = path
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
        self.url = 'https://cas.sustc.edu.cn/cas/login?service=http%3A%2F%2Fsakai.sustc.edu.cn%2Fportal%2Flogin'
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
        pattern = re.compile('"loggedIn": (.*?),')
        self.loggedIn = 'true' in re.findall(pattern, text)
        return self.loggedIn

    def _check_logged(self):
        if not self.loggedIn:
            print('not logged in, permission denied')
        return self.loggedIn

    def _get_home_page(self):
        r = self.s.get('http://sakai.sustc.edu.cn/portal')
        text = r.content.decode('utf-8')
        txt = unescape(text)
        return txt

    def get_home_page(self):
        if not self._check_logged():
            return

        return self._get_home_page()

    def get_sites(self):
        if not self._check_logged():
            return
        soup = BeautifulSoup(self.get_home_page(), 'lxml')
        header = soup.find(id='linkNav')
        topnav = header.find(id='topnav')
        topnav_items = topnav.find_all('a')
        for item in topnav_items[1:-1]:
            name = item.get_text()
            url = item.get('href')
            session = 'top'
            site = Site(name, url, session)
            self.topped_sites[name] = site
            self.sites[name] = site
        others = soup.find(id='otherSitesCategorWrap')
        if others:
            for item in others:
                if item.name == 'h4':
                    session = item.get_text()
                if item.name == 'ul':
                    for li in item.find_all('li'):
                        name = li.find('span').get_text()
                        url = li.find('a').get('href')
                        site = Site(name, url, session)
                        self.other_sites[name] = site
                        self.sites[name] = site
        return list(self.sites.keys())

    def _get_tree(self, url):
        base_url = url
        r = self.s.get(base_url)
        soup = BeautifulSoup(r.content, 'lxml')
        html_folders = soup.find_all(class_='folder')
        html_files = soup.find_all(class_='file')
        folders = {}
        files = {}
        if html_folders:
            for item in html_folders:
                folders[item.get_text().strip()] = self._get_tree(base_url + item.a.get('href'))

        for item in html_files:
            name = item.get_text().strip()
            url = base_url + item.a.get('href')
            files[name] = url
        return [folders, files]

    def _print_tree(self, tree, current, d = 0):
        print(' ' * (d - 1) + "|" + '-'* d + '%s' % current)
        folders = tree[0]
        files = tree[1]
        for folder in folders.keys():
            self._print_tree(folders[folder], folder, d + 2)
        for file in files:
            print('  ' * d + '|-%s' % file)

    def _download(self, tree, cur_dir):
        global time__
        cur_dir = os.path.expanduser(cur_dir)
        if not os.path.isdir(cur_dir):
            os.mkdir(cur_dir)
        files = tree[1]
        folders = tree[0]
        for folder in folders.keys():
            self._download(folders[folder], cur_dir + '/{}'.format(folder))

        for file in files.keys():
            time__ += 1
            url = files[file]
            try:
                r = self.s.get(url, stream=True, timeout = 2)
                chunk_size = 1000
                timer = 0
                if 'Content-Length' in r.headers.keys():
                    length = int(r.headers['Content-Length'])
                else:
                    length = 1
                print('downloading {}'.format(file))
                dir = cur_dir + '/' + file.strip().replace(':', '_')
                sys.path.append(dir)
                if os.path.isfile(dir):
                    print('  file already exist, skipped')
                    continue
                with open(dir, 'wb') as f:
                    for chunk in r.iter_content(chunk_size):
                        timer += chunk_size
                        percent = round(timer/length, 4) * 100
                        print('\r {:4f}'.format((percent)), end = '')
                        f.write(chunk)
                print('\r  finished    ')
                time.sleep(0.01)
            except requests.exceptions.ReadTimeout:
                print('read time out, trying to redownload')
                self._download_error(r.url, dir)
            except requests.exceptions.ConnectionError:
                print('ConnectionError, trying to redownload')
                self._download_error(r.url, dir)
            except UnboundLocalError:
                print('Unkonwn error')

    def _download_error(self, url, dir):

        try:
            r = self.s.get(url, stream=True, timeout = 10)
            chunk_size = 1000
            timer = 0
            length = int(r.headers['Content-Length'])
            # print('downloading {}'.format(file))
            with open(dir, 'wb') as f:
                for chunk in r.iter_content(chunk_size):
                    timer += chunk_size
                    percent = round(timer/length, 2) * 100
                    print('\r {:4f}'.format((percent)), end = '')
                    f.write(chunk)
            print('successfully redownload')
        except requests.exceptions.ReadTimeout:
            if platform.system() == 'Windows':
                windows_command_line.printRed('You may need to download this file yourself, sorry\n')
                windows_command_line.printRed(r.url + '\n')
            else:
                print('You may need to download this file yourself, sorry')
                print(r.url)
        except requests.exceptions.ConnectionError:
                if platform.system() == 'Windows':
                    windows_command_line.printRed('You may need to download this file yourself, sorry\n')
                else:
                    print('You may need to download this file yourself, sorry')
                    print(r.url)

    def get_tree(self, site, ensure = True):
        site = self.sites[site]
        base_url = 'http://sakai.sustc.edu.cn/access/content/group/' + site.db + "/"
        tree = self._get_tree(base_url)
        r = self.s.get(base_url)
        #print tree
        print('this is the current files in the root: ')
        self._print_tree(tree, site.name)
        #check whether to download
        while ensure:
            a = input('are you going to download them?[y/n]')
            # a = 'y'
            if a == 'y' or a == 'Y':
                break
            elif a == 'n' or a == 'n':
                return
            else:
                print('please enter y or n')

        self._download(tree, self.path + '/' + site.name)

        # for name in sorted(files.keys()):
        #     url = files[name]
        #     r = self.s.get(base_url + url, stream=True)
        #     chunk_size = 2000
        #     timer = 0
        #     total = len(r.content)
        #     print('downloading {}'.format(name))


        #     with open('./{}/{}'.format(site.name, name), 'wb') as fd:
        #         for chunk in r.iter_content(chunk_size):
        #             timer = timer + chunk_size
        #             print('{}'.format(round(timer / total * 100), + 2), end='\r')
        #             fd.write(chunk)
        #         fd.close()
        print('done')


if __name__ == '__main__':
    if 'Windows' in platform.system():
        formula = '(.*)\\\\.*?.exe'
        pattern = re.compile(formula)
        path = re.findall(pattern, sys.argv[0])[0]
        import windows_command_line
        windows_command_line.printPink('Welcome to use sakai getter. This application is developed by Boris, hope you will enjoy it.\n')
        windows_command_line.printPink('If you have any problem when using it, please email me by 11510237@mail.sustc.edu.cn, thank you very much\n')
    else:
        import Cocoa
        print('\033[0;33;38mWelcome to use sakai getter. This application is developed by Boris, hope you will enjoy it.')
        print('If you have any problem when using it, please email me by 11510237@mail.sustc.edu.cn, thank you very much')
        print('\033[0m')
        path = Cocoa.NSBundle.mainBundle().bundlePath()
        if 'Python.app' in path:
            path = os.getcwd()
        sys.path.append(path)
        # formula = 'Users/Boris'
        # pattern = re.compile(formula)
        # path = (re.sub(pattern, '~', path))
    while True:
        username = 11510237  # input('Please enter your username:')
        password = 310034  # getpass.getpass('please enter you password:')
        sakai = Sakai(username, password, path)
        if sakai.login():
            print('successfully logged in')
            break
        else:
            print('wrong password, you can print Ctrl-C to exit.')
            continue

    sites = sorted(sakai.get_sites())
    print("You've registered these sites:")
    for i in range(1, len(sites) + 1):
        print(i, sites[i - 1])
    num = (input('enter the number of the site that you want to download:')).strip().split()

    for num_ in map(lambda x: int(x) - 1, num):
        site = sites[num_]
        print('you have choosed {}'.format(site))
        sakai.get_tree(site, False)
    
    sakai.get_tree(site)
    input('Thank you for using\nenter any key to exit')