# -*- coding: utf-8 -*-
"""
国内月热度榜单数据获取模块
数据来源：QQ音乐(网页抓取) + 网易云音乐(API) + 酷狗音乐(网页抓取)
每日缓存，避免频繁请求
"""

import requests
import json
import os
import time
import re

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chart_cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'hot_chart.json')
CACHE_DURATION = 24 * 60 * 60

WEB_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

NETEASE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://music.163.com/',
    'Accept': 'application/json',
}


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _is_cache_valid():
    if not os.path.exists(CACHE_FILE):
        return False
    mtime = os.path.getmtime(CACHE_FILE)
    return (time.time() - mtime) < CACHE_DURATION


def _load_cache():
    if _is_cache_valid():
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def _save_cache(data):
    _ensure_cache_dir()
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_qq_toplist():
    """获取QQ音乐巅峰榜·热歌榜（网页抓取方式）"""
    songs = []
    try:
        url = "https://y.qq.com/n/ryqq/toplist/26"
        resp = requests.get(url, headers=WEB_HEADERS, timeout=15)
        match = re.search(r'window\.__INITIAL_DATA__\s*=\s*({.*?})\s*</script>', resp.text, re.DOTALL)
        if not match:
            return songs
        data_str = match.group(1)
        data_str = re.sub(r'\bundefined\b', 'null', data_str)
        data_str = re.sub(r'new Date\([^)]*\)', 'null', data_str)
        data = json.loads(data_str)
        song_list = data.get('songInfoList', [])
        for i, song in enumerate(song_list[:30]):
            singer_names = '/'.join([s.get('name', '') for s in song.get('singer', [])])
            songs.append({
                'rank': i + 1,
                'song': song.get('name', ''),
                'singer': singer_names,
                'genre': '流行',
                'platform': 'QQ音乐',
                'heat': 0
            })
    except Exception as e:
        print(f"QQ音乐榜单获取失败: {e}")
    return songs


def fetch_netease_hot():
    """获取网易云音乐热歌榜 Top30"""
    songs = []
    try:
        url = "https://music.163.com/api/playlist/detail?id=3778678"
        resp = requests.get(url, headers=NETEASE_HEADERS, timeout=10)
        data = resp.json()
        track_list = data.get('result', {}).get('tracks', [])
        for i, track in enumerate(track_list[:30]):
            singer_names = '/'.join([s.get('name', '') for s in track.get('artists', [])])
            genre = ''
            if track.get('artists'):
                genre = track['artists'][0].get('name', '')
            songs.append({
                'rank': i + 1,
                'song': track.get('name', ''),
                'singer': singer_names,
                'genre': genre or '流行',
                'platform': '网易云',
                'heat': track.get('popularity', 0)
            })
    except Exception as e:
        print(f"网易云音乐榜单获取失败: {e}")
    return songs


def fetch_kugou_hot():
    """获取酷狗音乐TOP500榜单（网页抓取方式）"""
    songs = []
    try:
        url = "https://www.kugou.com/yy/rank/home/1-8888.html"
        resp = requests.get(url, headers=WEB_HEADERS, timeout=15)
        match = re.search(r'global\.features\s*=\s*(\[.*?\]);', resp.text, re.DOTALL)
        if not match:
            return songs
        features = json.loads(match.group(1))
        for i, item in enumerate(features[:30]):
            filename = item.get('FileName', '')
            author = item.get('author_name', '')
            song_name = filename
            if ' - ' in filename:
                parts = filename.split(' - ', 1)
                song_name = parts[1].strip()
                if not author:
                    author = parts[0].strip()
            song_name = song_name.replace('&amp;', '&')
            author = author.replace('&amp;', '&')
            songs.append({
                'rank': i + 1,
                'song': song_name,
                'singer': author,
                'genre': '流行',
                'platform': '酷狗',
                'heat': item.get('privilege', 0)
            })
    except Exception as e:
        print(f"酷狗音乐榜单获取失败: {e}")
    return songs


def get_hot_chart():
    """获取国内月热度榜单（带每日缓存）"""
    cached = _load_cache()
    if cached:
        return cached

    qq_hot = fetch_qq_toplist()
    netease_hot = fetch_netease_hot()
    kugou_hot = fetch_kugou_hot()

    combined = _merge_charts(qq_hot, netease_hot, kugou_hot)

    result = {
        'update_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'combined': combined,
        'qq_hot': qq_hot,
        'netease_hot': netease_hot,
        'kugou_hot': kugou_hot
    }

    _save_cache(result)
    return result


def _merge_charts(qq_list, netease_list, kugou_list):
    """合并三个平台的榜单，按综合热度排序"""
    song_map = {}

    for item in qq_list:
        key = item['song'] + '|' + item['singer']
        if key not in song_map:
            song_map[key] = {
                'song': item['song'],
                'singer': item['singer'],
                'genre': item['genre'],
                'qq_rank': item['rank'],
                'netease_rank': 0,
                'kugou_rank': 0,
                'platforms': ['QQ音乐']
            }
        else:
            song_map[key]['qq_rank'] = item['rank']
            if 'QQ音乐' not in song_map[key]['platforms']:
                song_map[key]['platforms'].append('QQ音乐')

    for item in netease_list:
        key = item['song'] + '|' + item['singer']
        if key not in song_map:
            song_map[key] = {
                'song': item['song'],
                'singer': item['singer'],
                'genre': item['genre'],
                'qq_rank': 0,
                'netease_rank': item['rank'],
                'kugou_rank': 0,
                'platforms': ['网易云']
            }
        else:
            song_map[key]['netease_rank'] = item['rank']
            if '网易云' not in song_map[key]['platforms']:
                song_map[key]['platforms'].append('网易云')

    for item in kugou_list:
        key = item['song'] + '|' + item['singer']
        if key not in song_map:
            song_map[key] = {
                'song': item['song'],
                'singer': item['singer'],
                'genre': item['genre'],
                'qq_rank': 0,
                'netease_rank': 0,
                'kugou_rank': item['rank'],
                'platforms': ['酷狗']
            }
        else:
            song_map[key]['kugou_rank'] = item['rank']
            if '酷狗' not in song_map[key]['platforms']:
                song_map[key]['platforms'].append('酷狗')

    merged = list(song_map.values())
    for item in merged:
        qq_score = max(0, 31 - item['qq_rank']) * 3 if item['qq_rank'] > 0 else 0
        netease_score = max(0, 31 - item['netease_rank']) * 3 if item['netease_rank'] > 0 else 0
        kugou_score = max(0, 31 - item['kugou_rank']) * 3 if item['kugou_rank'] > 0 else 0
        platform_count = sum(1 for r in [item['qq_rank'], item['netease_rank'], item['kugou_rank']] if r > 0)
        cross_bonus = (platform_count - 1) * 15 if platform_count > 1 else 0
        item['score'] = qq_score + netease_score + kugou_score + cross_bonus

    merged.sort(key=lambda x: x['score'], reverse=True)

    result = []
    for i, item in enumerate(merged[:30]):
        result.append({
            'rank': i + 1,
            'song': item['song'],
            'singer': item['singer'],
            'genre': item['genre'],
            'platforms': '、'.join(item['platforms']),
            'qq_rank': item['qq_rank'],
            'netease_rank': item['netease_rank'],
            'kugou_rank': item['kugou_rank'],
            'score': item['score']
        })

    return result


if __name__ == '__main__':
    chart = get_hot_chart()
    print(f"更新时间: {chart['update_time']}")
    print(f"\n综合热度榜 Top 10:")
    for item in chart['combined'][:10]:
        print(f"  {item['rank']}. {item['song']} - {item['singer']} [{item['genre']}] 平台:{item['platforms']} 分数:{item['score']}")
