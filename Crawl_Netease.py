import requests


HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.43'
}


def info_get(music_id):
    resp = requests.get(
        f'https://music.163.com/api/song/detail/?id={music_id}&ids=%5B{music_id}%5D'
    )
    info_dict = resp.json()
    name = info_dict['songs'][0]['name']
    artists = info_dict['songs'][0]['artists'][0]['name']
    return artists, name


def download_song(song_id):
    song = requests.get(url=f'https://music.163.com/song/media/outer/url?id={song_id}.mp3', headers=HEADER)
    song_name = ' - '.join(info_get(song_id))
    with open(f"{song_name}.mp3", 'wb') as f:
        f.write(song.content)
        print(f'下载成功 -> {song_name}')


if __name__ == '__main__':
    audio_id = input("请输入要下载音乐的id: ")
    if not audio_id:
        audio_id = '2089730107'
    download_song(audio_id)
