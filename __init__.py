from msilib import Directory
from nonebot import on_command, on_regex
from nonebot.rule import to_me
from nonebot.params import CommandArg, EventMessage
from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import Message, MessageSegment

import multiprocessing
from spleeter.separator import Separator

import re
import os
import requests
import time
import json

proxies = {
  'http': 'http://127.0.0.1:7895',
  'https': 'http://127.0.0.1:7895',
}
file_dir = os.path.dirname(os.path.realpath(__file__))



song = on_regex(r"恋恋唱\s*(.+?)")

@song.handle()
async def _(event: Event, message: Message = EventMessage()):
    regex = "恋恋唱\s*(.+?)"
    await song.send("正在推理，少女祈祷中...（生成时间可能较长，一般为三分钟左右的时间，请耐心等待）")
    match = re.match(regex, str(message))
    groups = match.groups()
    song_name = groups[0]
    # 搜索歌曲的ID
    print('find id')
    search_url = f'https://netease-cloud-music-api-eight-zeta-83.vercel.app/search/suggest?keywords={song_name}'
    search_response = requests.get(search_url,proxies=proxies)
    search_data = search_response.json()
    print('id found')

    # 遍历搜索结果中的所有歌曲
    i = 0
    while i < len(search_data['result']['songs']):
        song_id = search_data['result']['songs'][i]['id']
        download_url = f'https://netease-cloud-music-api-eight-zeta-83.vercel.app/song/download/url?id={song_id}&br=320000'
        download_response = requests.get(download_url,proxies=proxies)
        download_data = download_response.json()

        # 检查是否可以下载歌曲
        if download_data['data']['code'] == 200:
            # 下载音乐文件并保存为raw.mp3
            music_url = download_data['data']['url']
            music_response = requests.get(music_url)
            music_response.raise_for_status() 
            print('music OK')
            with open('src/plugins/nonebot_plugin_SoVitsSvc/raw.mp3', 'wb') as file:
                file.write(music_response.content)
            print('file OK')
            break
        else:
            i += 1

    if i == len(search_data['result']['songs']):
        print('No available songs found')

    #分离人声
    current_directory = os.path.dirname(os.path.realpath(__file__))
    multiprocessing.freeze_support()
    
    separator = Separator('spleeter:2stems-16kHz')

    # 使用分离器处理音频，音频文件位于当前目录
    audio_descriptor = os.path.join(current_directory, 'raw.mp3')
    output_directory = os.path.join(current_directory, 'so-vits-svc')

    result = separator.separate_to_file(audio_descriptor, output_directory)
    if result:
        print('audio OK')
    #调用svc
    cmd = 'python src/plugins/nonebot_plugin_SoVitsSvc/so-vits-svc/inference_main.py -m "src/plugins/nonebot_plugin_SoVitsSvc/so-vits-svc/logs/44k/G_30000.pth" -c "src/plugins/nonebot_plugin_SoVitsSvc/so-vits-svc/configs/config.json" -n "vocals.wav" -t 0 -s "nahida"'
    os.system(cmd)
    print('svc is running')
    #发送
    audio_file = os.path.join(file_dir, 'so-vits-svc','results','vocals.wav_0key_nahida_sovits_pm.flac')
    print('svc OK')
    await song.send(MessageSegment.record(f'file:///{audio_file}'))