#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import urllib.error
import re
import ssl
import io
import os
import time
import gzip
import random
import socket

import m3u8
import json
import requests
import subprocess
import mysql.connector
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from mysql.connector import pooling
from requests.exceptions import RequestException

socket.setdefaulttimeout(5.0)

class Tools (object) :

    def __init__ (self) :
        pass
    
    # 校验是否为ip地址
    def check_ip(self, ip):
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(pattern, ip))
            
    # 检查URL的有效性
    def check_url(self, url, timeout):
        try:
            response = requests.get(url, stream=True, timeout=timeout)
            return response.status_code == 200
        except RequestException:
            return False

    # 检查IPTV的有效性
    def check_iptv(self, url, delay):
        try:
            startTime = int(round(time.time() * 1000))
            response = urllib.request.urlopen(url, timeout=delay)
            code = response.getcode()
            if code == 200 :
                endTime = int(round(time.time() * 1000))
                useTime = endTime - startTime
                # 延迟超过3秒，视为卡顿无效
                if int(useTime) > 0 and int(useTime) < 3 * 1000:
                    return True
                else:
                    return False
            else:
                return False
        except:
            return False
    
    # 解析IPTV分辨率等信息
    def get_ffprobe_info(self, url):
        command = ['ffprobe', '-print_format', 'json', '-show_format', '-show_streams', '-v', 'quiet', url]
        
        try:
            # 设置超时时间为10秒
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            output = result.stdout
            data = json.loads(output)
            # 获取视频流信息
            video_streams = data['streams']
            width = 0.00
            height = 0
            frame = 0.00
            
            if len(video_streams) > 0:
                stream = video_streams[0]
                # 提取宽度和高度
                width = stream.get('width')
                if width is None:
                    frame = 0
                height = stream.get('height')
                if height is None:
                    height = 0
                # 提取帧速率
                frame = stream.get('r_frame_rate')
                if frame != '0/0' and frame != '':
                    frame = eval(frame)
                else:
                    frame = 0.0
            if width == 0 or height == 0 or frame == 0.0:
                return []
            return [width, height, frame]
        except KeyError:
            # print('无法提取视频流信息：找不到 streams 键')
            return []
        except json.JSONDecodeError:
            # print('无法解析 ffprobe 输出为 JSON 格式')
            return []
        except subprocess.CalledProcessError as e:
            # print("Error: 视频信息无效，解析失败")
            return []
        except subprocess.TimeoutExpired:
            # print("Error: 执行超时")
            return []

    # 获取IPTV播放速度信息
    def get_speed(self, url, fornum):
        try:
            speeds = []
            average_speed = 0
            
            for _ in range(fornum):
                start_time = time.time()
                response = requests.get(url, stream=True, timeout=10)
                total_bytes = 0
                
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        total_bytes += len(chunk)
                
                response.close()
                
                current_time = time.time()
                elapsed_time = current_time - start_time
                speed = total_bytes / elapsed_time / 1024  # 计算网速，单位为 Kbps
                speeds.append(speed)
                # print(f"当前网速：{speed:.2f} Kbps")
                
                time.sleep(2)  # 等待2秒
            
            average_speed = sum(speeds) / len(speeds)
            # 格式化平均网速为两位小数
            average_speed = f"{average_speed:.2f}"
            # print(f"平均网速：{average_speed} Kbps")
            return average_speed
        except requests.Timeout:
            # print("请求超时")
            return 0.00
        except requests.RequestException as e:
            # print("请求发生异常:", str(e))
            return 0.00