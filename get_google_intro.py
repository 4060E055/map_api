import json
import time
from urllib.parse import quote
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from liontk.proxy.proxy_client import ProxyClient
import math
"""
call google search to get place introduction
只能在server用隨機proxy
"""
#fixme 待整理與優化
class GoogleSearch:
    def __init__(self, contry):
        self.client = ProxyClient.get_client(minute_threshold=5, refresh_per_req_counts=1000)
        self.contry = contry
        self.__user_agent = UserAgent()

    def google_request(self, place):

        url_encoded_text = quote(place)
        url = f"https://www.google.com/search?q={url_encoded_text}"

        # 創建隨機的 User-Agent
        headers = {"User-Agent": self.__user_agent.random}

        proxy_ip = self.client.get_avail_proxy().get_ip_with_proxy_port()  # 獲取代理IP
        response = requests.get(url, headers=headers, proxies={'http': f'{proxy_ip}', 'https': f'{proxy_ip}'})
        if response.status_code == 200:
            result = BeautifulSoup(response.text, "html.parser")
            return result
        else:
            print("Request Filed：　", response.status_code, response.text)
            return None

    def get_place_intro(self, place: str, city: str = "", sleep=1) -> str:
        # keywords = ["介紹", "簡介", "Introduction", "Summary"]
        keywords = ["介紹", "簡介", "資訊", "相關訊息", "情報", "名稱"]

        for keyword in keywords:  # 試關鍵字直到有找到
            search_text = f"{city} {place} {keyword}"

            print(f"查詢：{search_text}")
            result = self.google_request(search_text)
            if result != None:  # request成功
                place_content = self.get_tag_text(result)
                if place_content != None:  # 找到tag內容
                    return (search_text, place_content)
            time.sleep(sleep)  # 休息一秒再試

        if city != self.contry:
            for keyword in keywords:  # 試關鍵字直到有找到
                search_text = f"{self.contry} {place} {keyword}"

                print(f"查詢：{search_text}")
                result = self.google_request(search_text)
                if result != None:  # request成功
                    place_content = self.get_tag_text(result)
                    if place_content != None:  # 找到tag內容
                        return (search_text, place_content)
                time.sleep(sleep)  # 休息一秒再試

        return (None, None)

    def get_tag_text(self, result):

        target_element = result.select('span.hgKElc')
        text_content = ""
        # 检查目標元素是否存在
        if target_element:
            # 提取目标元素的文本内容
            for element in target_element:
                text_content += element.get_text(strip=True)
            return text_content
        else:
            return None


def write_to_json(output_data, output_json_path):
    try:
        with open(output_json_path, "r", encoding='utf-8') as file:
            json_data = json.load(file)
    except json.JSONDecodeError:  # 如果json檔案是空的
        json_data = []
    finally:
        json_data.extend(output_data)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            output_json = json.dumps(json_data, ensure_ascii=False, indent=4)
            f.write(output_json)
    with open('data.json', 'w') as json_file:
        json.dump(output_data, json_file)


if __name__ == "__main__":

    def csv_to_json():
        input_csv_path = 'input_data/merge_4_0307.csv'
        places_df = pd.read_csv(input_csv_path)
        places_df_nodup = places_df.drop_duplicates(subset='ATTRACTION')
        tokyo_df = places_df_nodup[places_df_nodup['G_CITY'] == '東京都']
        output_json_path = 'output_data/places_intro_0310.json'
        # tokyo_df_nodup = tokyo_df.drop_duplicates(subset='ATTRACTION', keep='last')
        # print(f"總共 東京都 資料筆數:{tokyo_df.shape[0]}")
        print(f"總共 東京都 資料筆數:{tokyo_df.shape[0]}")
        n = 0
        for idx, row in tokyo_df.iterrows():
            n += 1
            print(f"查詢第{n}筆資料:{row['ATTRACTION']}")
            search_text, place_intro = gsearch.get_place_intro(row['ATTRACTION'], row['G_CITY'][:2])
            if place_intro != None:
                write_to_json([{
                    'place': row['ATTRACTION'],
                    # 'city': row['G_CITY'],
                    'search_text': search_text,
                    'introduction': place_intro
                }], output_json_path)
            else:
                write_to_json([{
                    'place': row['ATTRACTION'],
                    # 'city': row['G_CITY'],
                    'search_text': None,
                    'introduction': None
                }], output_json_path)

            #
            # if idx>=10:
            #     break


    def jsonPOI_to_json():
        input_json_path = 'input_data/real_tokyo_article.json'
        input_csv_path = 'input_data/jp_poi_0308.csv'
        output_json_path = 'output_data/real_tokyo_article_0311.json'

        with open(output_json_path, 'w', encoding='utf-8') as f:
            f.write('[]')

        with open(input_json_path, "r", encoding='utf-8') as file:
            json_data = json.load(file)

        # input csv
        places_df = pd.read_csv(input_csv_path)

        POI_data = []
        for data in json_data:
            POI_data += data['POI']

        POI_data = list(set(POI_data))

        print(f"總共資料筆數:{len(POI_data)}")
        for idx, poi in enumerate(POI_data):
            print(f"查詢第{idx}筆資料:{[poi]}")

            poi_df = places_df[places_df['ATTRACTION'] == poi]
            if poi_df.empty:
                city = '日本'
            else:
                city = poi_df['G_CITY'].tolist()[0]
                if (type(city)==float and math.isnan(city)) or city=="":
                    city = '日本'

            search_text, place_intro = gsearch.get_place_intro(poi, city)
            if place_intro != None:
                write_to_json([{
                    'place': poi,
                    'search_text': search_text,
                    'introduction': place_intro
                }], output_json_path)
            else:
                write_to_json([{
                    'place': poi,
                    'search_text': None,
                    'introduction': None
                }], output_json_path)


    gsearch = GoogleSearch("日本")
    # ex2:利用json檔案中的東京都查詢google
    jsonPOI_to_json()

    # ex1:利用csv檔中的東京都查詢google
    # csv_to_json()

    # single test
    # gsearch.get_place_intro('29テラス', '東京都')
    gsearch.client.close()
