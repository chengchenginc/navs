#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import csv, json
import requests
from bs4 import BeautifulSoup
import re,html

headers = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'}

TOOLS_PATH = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
DATA_PATH = os.path.dirname(TOOLS_PATH) + os.path.sep + "data" + os.path.sep
LOGO_PATH = os.path.dirname(TOOLS_PATH) + os.path.sep + "static" + os.path.sep + "images" + os.path.sep + "logos" + os.path.sep


theme = "default"
split_size = 4  # 按4个分一组


tag_regex = r'<[^>]+>'
tag_rc = re.compile(tag_regex, re.S)


def filter_tags(htm):
    htm = html.unescape(htm)
    text = tag_rc.sub('', htm)
    return text


def read_navs_from_csv():
    navs = []
    with open(DATA_PATH + theme + os.path.sep + "navs.csv", newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        index = 0
        headers = []
        for row in csv_reader:
            index += 1
            if index == 1:
                headers = row
            else:
                item = {}
                for i in range(0, len(headers)):
                    header = headers[i]
                    item[header] = row[i]
                navs.append(item)
    content = json.dumps(navs, ensure_ascii=False)
    with open(DATA_PATH + theme + os.path.sep + "navs.json", mode="w", encoding="utf-8") as f1:
        f1.write(content)
    print("read csv finish")


def merge_navs_menus():
    navs_file = DATA_PATH + theme + os.path.sep + "navs.json"
    menus_file = DATA_PATH + theme + os.path.sep + "menus.json"
    if os.path.exists(navs_file) is False:
        print("navs.json不存在")
        exit(0)
    with open(navs_file, encoding='utf-8') as f_navs:
        navs = f_navs.read()
        navs = json.loads(navs)

    format_menus, format_navs = get_format_navs_menus(navs)

    generator_menus = False
    if os.path.exists(menus_file) is False or generator_menus is True:
        print("使用默认构建菜单")
        menus = format_menus
        if os.path.exists(menus_file) is False:  # 存档
            with open(DATA_PATH + theme + os.path.sep + "menus.json", mode="w", encoding="utf-8") as fm:
                content = json.dumps(menus, ensure_ascii=False)
                fm.write(content)
    else:
        with open(menus_file, encoding='utf-8') as f_menus:
            menus = f_menus.read()
            menus = json.loads(menus)
    with open(DATA_PATH + theme + os.path.sep + "navs_menus.json", mode="w", encoding="utf-8") as fnm:
        content = json.dumps({"navs": format_navs, "menus": menus}, ensure_ascii=False)
        fnm.write(content)
    print("merge finish")


def get_format_navs_menus(navs):
    menus = {}
    new_navs = {}
    for nav in navs:
        tags = nav['tags']
        menu = menus.get(tags, None)
        new_nav = new_navs.get(tags, None)
        if menu is None:
            menus[tags] = {"name": tags, "items": [], "link": "#" + tags, "icon": ""}
        if new_nav is None:
            new_navs[tags] = {"name": tags, "items": []}

        del nav['tags']
        new_navs[tags]["items"].append(nav)
    list_menus = [i for i in menus.values()]

    list_navs = []
    for tags in new_navs:
        new_nav = new_navs[tags]
        items = new_nav.get("items", [])
        new_nav["items"] = list_split(items, split_size)
        list_navs.append(new_nav)
    # print(json.dumps(list_menus, ensure_ascii=False))
    # print(json.dumps(list_navs, ensure_ascii=False))
    return (list_menus, list_navs)

def list_split(items, n):
    return [items[i:i + n] for i in range(0, len(items), n)]


def gather_navs():
    url = "http://tools.mazileon.com/"
    response = requests.get(url, headers=headers)
    # print(response.text)
    soup = BeautifulSoup(response.text, "lxml")

    row = soup.select(".content>.row")
    row_items = row[0].find_all("div")
    tags = ""
    items = []
    for row_item in row_items:
        if "col-12" in row_item.get("class"):
            section_title = row_item.select(".section-title")
            if section_title is not None and len(section_title) > 0:
                tags = section_title[0].contents[2].strip()
                tags = tags.replace("-","").replace(".","")
                print(tags)
            pass
        if "col-xl-3" in row_item.get("class"):
            data = row_item.select('a.card')
            for item in data:
                name = item.select('.card-title')[0].get_text().strip()
                explain = item.select('.card-desc')[0].get_text().strip()
                href = item.get('href')
                logo = item.select('img')[0].get("src")

                domains = href.replace("com.cn", "com").split(".")
                en_name = domains[1]
                if len(domains) == 2:
                    en_name = domains[0]
                en_name = en_name.replace("http://", "").replace("https://", "").replace("/", "")
                #[{"name": "36Kr", "en_name": "36Kr", "explain": "创业资讯、科技新闻", "link": "https://36kr.com/", "logo": "36kr.png", "tags": "社区咨询"}]

                filename = os.path.basename(logo)
                filename, file_extension = os.path.splitext(filename)

                new_logo = en_name+file_extension
                download_file(logo, LOGO_PATH + new_logo)
                _item = {
                    'name': name,
                    'en_name': en_name,
                    'explain': explain,
                    'link': href,
                    'logo': new_logo,
                    'tags': tags
                }
                items.append(_item)
    print(json.dumps(items, ensure_ascii=False))


def download_file(url, save_path):
    if os.path.exists(save_path) is False:
        r = requests.get(url)
        with open(save_path, "wb") as fcopy:
            fcopy.write(r.content)
        print("保存成功:"+save_path)


if __name__ == '__main__':
    merge_navs_menus()
    # gather_navs()
