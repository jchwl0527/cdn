import os
import time
import requests
from lxml import etree
import certifi
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry  # type: ignore
# 创建目录
if not os.path.exists('16k'):
    os.mkdir('16k')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43',
}


def get_page(ids):
    url = f'https://16k.club/post.php?id={ids}'

    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    http = requests.Session()
    http.mount('https://', adapter)

    resp = http.get(url, headers=headers)

    # resp = requests.get(url, headers=headers, verify=certifi.where())
    html = resp.text

    # 解析HTML,提取数据
    tree = etree.HTML(html)
    try:
        # 提取标题
        title = tree.xpath('/html/body/div[1]/div[1]/h1/text()')[0]
    except IndexError:
        print(f'{ids}为空。')
        return

    # 先检查本地是否有这个文件
    if os.path.exists(f'16k/{ids}-{title}.mp4') or os.path.exists(f'16k/{ids}-{title}.webp'):
        print(f'跳过{ids}-{title},本地已经有该文件!')
        return

    # 先检查是否有视频源地址,如果有则下载视频
    video_src = tree.xpath('/html/body/div[1]/div[1]/div/div/div/video/source/@src')
    if video_src:
        video_src = video_src[0]
        # video_url = 'https:' + video_src
        video_resp = requests.get(video_src, stream=True)

        with open(f'16k/{ids}-{title}.mp4', 'wb') as f:
            for chunk in video_resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                print('\r下载视频进度:{}%'.format(int(f.tell() / int(video_resp.headers['Content-Length']) * 100)),
                      end='')

    else:
        # 如果没有视频,则下载图片
        img_src = tree.xpath('/html/body/div[1]/div[1]/div/div/div/img/@src')[0]
        # img_url = 'https:' + img_src
        img_resp = requests.get(img_src, stream=True)

        with open(f'16k/{ids}-{title}.webp', 'wb') as f:
            for chunk in img_resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                print('\r下载图片进度:{}%'.format(int(f.tell() / int(img_resp.headers['Content-Length']) * 100)),
                      end='')


if __name__ == '__main__':
    # 创建线程池,最大线程数16
    pool = ThreadPoolExecutor(max_workers=64)

    for ids in range(1, 9999, 64):  # 每次采集16个
        # 创建新的线程池
        pool = ThreadPoolExecutor(max_workers=64)
        # 将任务提交给线程池
        results = list(pool.map(get_page, range(ids, ids + 64)))
        # 等待所有线程完成
    pool.shutdown()
