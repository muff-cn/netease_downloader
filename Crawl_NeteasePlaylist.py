import asyncio
import json
import os
import sys

import aiofiles
import aiohttp
import mutagen
import requests
from DecryptLogin import login
from DecryptLogin.modules.core.music163 import Cracker
from aiohttp.client_exceptions import ClientError
from mutagen.mp3 import MP3

"""
BUG: 请求失败后应重新登录 | 已解决 2024/1/6
"""

__author__ = 'Jerry Liao'
__date__ = 'Jun 6, 2024'


class DownloadPlaylist:
    def __init__(self, save_folder, username='', psw=''):
        self.username = username
        self.psw = psw
        self.path = save_folder
        login_call = self.login()
        infos_return = login_call[0]
        self.session: requests.Session = login_call[1]
        self.cookie_str = "; ".join([f"{name}={value}" for name, value in self.session.cookies.items()])
        self.csrf = infos_return['csrf']
        self.playlist_id = ['2298360318', '2020864493']
        self.cracker = Cracker()
        self.selenium = False
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
        }
        self.error_list = []
        self.top_playlist = {'飙升榜': '19723756', '新歌榜': '3779629', '原创榜': '2884035', '热歌榜': '3778678',
                             '云音乐说唱榜': '991319590', '云音乐古典榜': '71384707', '云音乐电音榜': '1978921795',
                             '黑胶VIP爱听榜': '5453912201', '云音乐ACG榜': '71385702', '云音乐韩语榜': '745956260',
                             '云音乐国电榜': '10520166', 'UK排行榜周榜': '180106', '美国Billboard榜': '60198',
                             'Beatport全球电子舞曲榜': '3812895', 'KTV唛榜': '21845217', '日本Oricon榜': '60131',
                             '云音乐欧美热歌榜': '2809513713', '云音乐欧美新歌榜': '2809577409',
                             '法国 NRJ Vos Hits 周榜': '27135204', '云音乐ACG动画榜': '3001835560',
                             '云音乐ACG游戏榜': '3001795926', '云音乐ACG VOCALOID榜': '3001890046',
                             }

    def run(self):
        def get_playlist_id_with_timeout(
                prompt="请输入要下载的歌单id (输入\033[93m quit \033[0m退出, 输入\033[93m help \033[0m获取帮助): ",
        ):
            return input(prompt)

        async def main(id_list):
            # def main():
            task_list = []
            for per_song in id_list.keys():
                # print(per_song, music_ids.get(per_song))
                t = asyncio.create_task(
                    self.download_songs(id_list.get(per_song),
                                        f'{self.path}/{playlist_name}',
                                        per_song)
                )
                task_list.append(t)

            await asyncio.wait(task_list)

        while True:
            self.error_list = []
            music_ids = dict()

            playlist_id = get_playlist_id_with_timeout()

            if not playlist_id:
                playlist_id = self.playlist_id[1]
            elif playlist_id == 'quit':
                break
            elif playlist_id == 'help':
                info = (
                    '---------------------\n'
                    '输入0 \t返回\n'
                    '输入1 \t获取网易云榜单id\n'
                    '---------------------\n'
                )
                print(info)
                cmd = input()
                if cmd == '1':
                    print('---------------------')
                    for key in self.top_playlist.keys():
                        print(f'{key:<30}', '\t', self.top_playlist.get(key))
                    print('---------------------')
                continue
            playlist_info = self.get_playlist(playlist_id)
            # print(playlist_info)
            playlist_name = playlist_info['playlist']['name']
            for per_id in zip(playlist_info['playlist']['trackIds'], playlist_info['playlist']['tracks']):
                music_ids[f"{per_id[1]['ar'][0]['name']} - {per_id[1]['name']}"] = per_id[0]['id']
            print(f'歌单名: \033[32m{playlist_name}\033[0m (共 \033[92m{len(music_ids)}\033[0m 首音乐)')
            confirm = input(f'确认要下载歌单 \033[32m{playlist_name}\033[0m 吗? (\033[93my/n\033[0m)  ')
            # break
            if confirm in ('yes', 'y'):

                # print(music_ids)

                asyncio.run(main(music_ids))
                for file in self.error_list:
                    os.remove(file)
                print(
                    f"[INFO] 歌单 \033[32m{playlist_name}\033[0m "
                    f"下载成功 \033[92m{len(music_ids) - len(self.error_list)} \033[0m首, "
                    f"失败 \033[92m{len(self.error_list)} \033[0m首"
                )
            else:
                continue

    # TODO: 下载音乐
    async def download_songs(self, music_id, folder_name, music_name):

        os.makedirs(folder_name, exist_ok=True)
        url = f'https://music.163.com/song/media/outer/url?id={music_id}.mp3'
        # cookie = requests.utils.dict_from_cookiejar(requests_session.cookies)
        async with aiohttp.ClientSession() as session:
            head = self.headers
            head['Cookie'] = self.cookie_str
            # print(self.cookie_str)
            while True:
                async with session.get(url, headers=head) as resp:
                    try:
                        cont = await resp.content.read()
                        need_removed_strs = ['<', '>', '\\', '/', '?', ':', '"', '：', '|', '？', '*']
                        # 创建转换表
                        remove_table = str.maketrans('', '', ''.join(need_removed_strs))

                        # 应用转换表并删除指定字符
                        song_name = music_name.translate(remove_table)
                        async with aiofiles.open(f'{folder_name}/{song_name}.mp3', 'wb') as f:
                            await f.write(cont)
                            try:
                                audio = MP3(f'{folder_name}/{song_name}.mp3')
                                print(f'下载成功 -> \033[36m{song_name}\033[0m')
                                if not audio:
                                    ...
                            except mutagen.mp3.HeaderNotFoundError:
                                print(f'下载失败 -> \033[31m{song_name}\033[0m', '(VIP)')
                                self.error_list.append(f"{folder_name}/{song_name}.mp3")
                            break
                    except (aiohttp.client_exceptions.ClientPayloadError or
                            aiohttp.client_exceptions.ServerDisconnectedError or
                            aiohttp.client_exceptions.ClientConnectorError or
                            aiohttp.client_exceptions.ServerDisconnectedError):
                        continue

    # TODO: 模拟登录
    @staticmethod
    def login():
        client = login.Client()
        music163 = client.music163(reload_history=True)
        # music163 = client.music163(reload_history=False)
        try:
            # raise RuntimeError
            infos_return, session = music163.login('', '', 'scanqr')
            print(infos_return)
        except RuntimeError:
            lg = login.Login()
            username = input("请输入账号: ")  # 13479499712
            password = input("请输入密码: ")  # lyf686955
            infos_return, session = lg.music163(username, password, 'pc')
            # print(infos_return)

        # print(infos_return)
        return infos_return, session

    # TODO: 获取歌单信息
    def get_playlist(self, playlist_id) -> dict:
        detail_url = 'https://music.163.com/weapi/v6/playlist/detail?csrf_token='
        offset = 0
        data = {
            'id': playlist_id,
            'offset': offset,
            'total': True,
            'limit': 1000,
            'n': 1000,
            'csrf_token': self.csrf
        }

        def req():
            resp = self.session.post(detail_url + self.csrf, headers=self.headers, data=self.cracker.get(text=data))
            text = json.loads(resp.text)
            resp.close()
            return text

        # chance = 0
        # while chance <= 5:
        #     chance += 1
        res = req()
        if res.get('code') == 404:
            new = input("请求失败! 重新登录吗? (\033[93my/n\033[0m) ")
            if new in ('y', 'yes'):
                self.login()
                return self.get_playlist(playlist_id)
            else:
                sys.exit()
        else:
            return res


if __name__ == '__main__':
    os.makedirs('Playlists', exist_ok=True)
    downloader = DownloadPlaylist('Playlists')
    downloader.run()
