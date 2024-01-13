import requests
import m3u8
import time
import json
import subprocess
import tools
import mysql.connector
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from mysql.connector import pooling
from requests.exceptions import RequestException

engine_url = "http://tonkiang.us/"

# 爬取CCTV频道资源
def spider_source():
    # 获取工具类
    T = tools.Tools()
    
    # 爬取直播源引擎
    groups = ["CCTV6", "CCTV10"]
    for group_addr in groups:
        # 获取当前时间
        current_time = datetime.now()
    
        page = 1
        number = 0
        page_count = 1
        counts = 1
        timeout_cnt = 0
        # 初始化集合数据
        data_list = []

        # 生成数据格式
        while page <= page_count and number < counts:
            url = engine_url + "?page=" + str(page) + "&s=" + group_addr
            # 发起HTTP请求获取网页内容
            try:
                response = requests.get(url, timeout=15)
                # 处理响应
                response.raise_for_status()
                # 检查请求是否成功
                html_content = response.text
                
                print(f"{current_time} 搜索频道直播源：{url}")

                # 使用BeautifulSoup解析网页内容
                soup = BeautifulSoup(html_content, "html.parser")

                # 查找所有class为"result"的<div>标签
                result_divs = soup.find_all("div", class_="result")

                # 循环处理每个结果<div>标签
                for result_div in result_divs:
                    m3u8_name = ""
                    m3u8_link = ""
                    # 获取m3u8名称
                    channel_div = result_div.find("div", class_="channel")
                    if channel_div is not None:
                        name_div = channel_div.find("div", style="float: left;")
                        if name_div is not None:
                            m3u8_name = name_div.text.strip()
                        else: 
                            counts_text = channel_div.text.strip()
                            # 提取数字部分
                            counts = int(''.join(filter(str.isdigit, counts_text)))
                            print(f"{current_time} 总记录数：{counts}")
                            page_count = int(counts) // 30
                            if counts/30 > page_count:
                                page_count += 1
                            print(f"{current_time} 总页码数：{page_count}")

                        # 获取m3u8链接
                        m3u8_div = result_div.find("div", class_="m3u8")
                        if m3u8_div is not None:
                            m3u8_link = m3u8_div.find("td", style="padding-left: 6px;").text.strip()
                            if m3u8_link.endswith('?'):
                                m3u8_link = m3u8_link[:-1]
                                    
                        if "http" not in m3u8_link:
                            # 继续下一次循环迭代
                            continue
                        
                        # 获取频道分类
                        if T.check_iptv(m3u8_link, 5):
                            speed = T.get_speed(m3u8_link, 3)
                            video_info = T.get_ffprobe_info(m3u8_link)
                            data_info = (m3u8_name, m3u8_link)
                            if float(speed) > 0 and len(video_info) > 0 and not any(info[:2] == data_info[:2] for info in data_list):
                                # 提取宽度和高度
                                width = video_info[0]
                                height = video_info[1]
                                # 提取帧速率
                                frame = video_info[2]
                                # 将数据添加到列表
                                print(f"{current_time} 第{number+1}条数据，频道名称：{m3u8_name}，分辨率：{width}*{height}，帧速率：{frame}, 播放速度：{speed} Kbps，有效地址: {m3u8_link}")
                                number += 1
                            else:
                                print(f"{current_time} 频道分辨率和播放速度获取失败：频道名称：{m3u8_name}，无效地址: {m3u8_link}")
                        else: 
                            print(f"{current_time} 频道地址校验失败：频道名称：{m3u8_name}，无效地址: {m3u8_link}")
            except (requests.Timeout, requests.RequestException) as e:
                timeout_cnt += 1
                print(f"{current_time} 请求发生超时，异常次数：{timeout_cnt}")
                if timeout_cnt <= 10:
                    # 继续下一次循环迭代
                    continue
                else:
                    print(f"{current_time} 超时次数过多：{timeout_cnt} 次，请检查网络是否正常")
            page += 1

# 执行主程序函数
spider_source()
