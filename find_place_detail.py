import json
import os
import random
import time
import traceback

import pandas as pd
import requests
"""
call google map api to get place detail
"""
#fixme 待整理與優化
def g_search_text(search_place='Spicy Vegetarian Food in Sydney, Australia'):
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': os.getenv("MAP2_KEY"),
        'X-Goog-FieldMask': '*',
    }

    data = {
        'textQuery': search_place,
        'regionCode': 'JP',
        'languageCode': 'zh-TW'
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        if result == {}:
            print(f'No result for ：{search_place}')
            return None
        else:
            return result['places'][0]
    else:
        print(f'Text Search Error:{response.status_code}\n{response.text}')
        return None


# fixme 未使用未完成 ，使用place id 的查找方式
def get_place_detail(place_id='ChIJkSkRxxPnAGARW6j0O5pSiPw'):
    # 设置请求头和请求体数据
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': os.getenv("MAP_KEY"),
        'X-Goog-FieldMask': '*'
    }
    url = f'https://places.googleapis.com/v1/places/{place_id}'
    # 发送 POST 请求
    response = requests.get(url, headers=headers)
    # 处理响应
    if response.status_code == 200:
        result = response.json()
        # 处理返回的结果
        print(result)
    else:
        print(f'Error:{response.status_code}\n{response.text}')


def write_to_json(output_file_path, place, place_detail):
    # 讀取現有json，進行階段性寫入，避免中斷後重頭開始
    try:
        with open(output_file_path, "r", encoding='utf-8') as file:
            json_data = json.load(file)
    except json.JSONDecodeError:  # 如果json檔案是空的
        json_data = []


    finally:
        json_data.extend([{
            'place_text': place.get('ATTRACTION', ''),
            'funliday_data': place,
            'google_map_data': place_detail
        }])

        # 寫入json
        with open(output_file_path, 'w', encoding='utf-8') as f:
            output_json = json.dumps(json_data, ensure_ascii=False, indent=4)
            f.write(output_json)


def get_opening_time(place_detail):
    if 'currentOpeningHours' in place_detail:
        return place_detail['currentOpeningHours'].get('weekdayDescriptions', '')
    else:
        return ""


def split_compound(compound_text):
    specified_keywords = ["都", "道", "縣", "府"]

    #todo 指定位置開始尋找指定keywords
    for keyword in specified_keywords:
        keyword_idx=compound_text[2:3].find(keyword)
        if keyword_idx != -1:
            compound_text = compound_text[:keyword_idx+3] + '_' + compound_text[keyword_idx+3:]
            break

        # compound_text = compound_text.repleace(keyword, keyword + '_')
        # if '_' in compound_text:
        #     break
    try:
        result = compound_text.split('_')
        return result[0], result[1]
    except:
        return "", ""





if __name__ == '__main__':
    def Icsv_Ojson():
        # place_detail = g_search_text('PARCO 百貨 寶可夢公仔')
        output_file_path = 'data/JP_POI_detail_2.json'
        input_file = 'input_data/merge4.csv'
        #
        # places_df = pd.read_excel(input_file)
        # places_data = places_df.to_dict(orient='records')
        #
        places_df = pd.read_csv(input_file)
        # 将 DataFrame 转换为字典
        places_data = places_df.to_dict(orient='records')
        seconds_min = 5  # 每次查詢間隔秒數
        seconds_max = 8  # 每次查詢間隔秒數
        start_num = 0  # 起始筆數
        end_num = 207  # 結束筆數
        print(f"總共有{len(places_data)}筆資料")
        for idx, place in enumerate(places_data[start_num:end_num]):
            print(f'查詢第{idx + start_num}筆資料:{place.get("ATTRACTION", "")}')
            place_detail = g_search_text(place.get('ATTRACTION', ''))

            write_to_json(output_file_path, place, place_detail)
            time.sleep(random.randint(seconds_min, seconds_max))


    def Icsv_Ocsv_Ojson():
        input_file = 'input_data/merge4.csv'
        output_json_path = 'data/JP_POI_detail_0305.json'
        output_csv_path = 'output_data/merge_0305.csv'
        # 使用 Pandas 读取 CSV 文件
        places_df = pd.read_csv(input_file)
        # 将 DataFrame 转换为字典
        places_data = places_df.to_dict(orient='records')
        seconds_min = 5  # 每次查詢間隔秒數
        seconds_max = 8  # 每次查詢間隔秒數
        start_num = 0  # 起始筆數
        end_num = 207  # 結束筆數
        print(f"總共有{len(places_data[start_num:end_num])}筆資料")
        for idx, place in enumerate(places_data[start_num:end_num]):
            try:
                print(f'查詢第{idx + start_num}筆資料:{place.get("ATTRACTION", "")}')
                place_detail = g_search_text(place.get('ATTRACTION', ''))

                if place_detail is not None:
                    if 'plusCode' in place_detail:
                        compound_text = place_detail['plusCode']['compoundCode'].split(' ')[1]
                        # pattern = '|'.join(map(re.escape, specified_keywords))
                        city, area = split_compound(compound_text)

                    else:
                        city = ""
                        area = ""

                    # 使用正則表達式進行拆分

                    places_data[idx]['PLACE_ID'] = place_detail.get('id', '')
                    places_data[idx]['G_CITY'] = city
                    places_data[idx]['G_AREA'] = area
                    places_data[idx]['REVIEW'] = place_detail.get('reviews', '')
                    places_data[idx]['OPENING_TIME'] = get_opening_time(place_detail)
                    places_data[idx]['TYPES'] = place_detail.get('types', '')
                    places_data[idx]['SUMMARY'] = place_detail['editorialSummary'].get('text', '')
                    places_data[idx]['LONG'] = place_detail['location'].get('longitude', '')
                    places_data[idx]['LAT'] = place_detail['location'].get('latitude', '')
            except:
                traceback.print_exc()
            # write_to_json(output_file_path, place, place_detail)
            time.sleep(random.randint(seconds_min, seconds_max))
        try:
            df = pd.DataFrame(places_data)
            df.to_csv(output_csv_path, index=False, encoding='utf-8')
            print(f"已儲存至{output_csv_path}")
        except:
            traceback.print_exc()

    #notice 執行不同測試程式

    # Icsv_Ojson()

    # Icsv_Ocsv_Ojson()
