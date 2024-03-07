import os
import traceback
from datetime import datetime
import pytz
import requests

"""
Google Map Directions API Introduction：
https://developers.google.com/maps/documentation/directions/get-directions?hl=zh-tw#maps_http_directions_boston_concord_waypoints_now-txt
"""


class NotFutureTime(Exception):
    def __init__(self, current_time, input_time):
        self.current_time = current_time
        self.input_time = input_time
        super().__init__()

    def __str__(self):
        return (f'Current time：{self.current_time}\n'
                f'Input time：{self.input_time}\n'
                f'Error message：The input time is earlier than the current time. Please enter a future time.')


class SearchDirectionsFailed(Exception):
    def __init__(self, status_code, error_message):
        self.code = status_code
        self.message = error_message
        super().__init__()

    def __str__(self):
        return (f'Directions API Status code：{self.code}\n'
                f'Error message：{self.message}')


class Transportation:
    DRIVING = 'driving'  # 開車
    WALKING = 'walking'  # 步行
    BICYCLING = 'bicycling'  # 騎腳踏車
    TRANSIT = 'transit'  # 大眾運輸


class TransitMode:
    """
    大眾運輸模式
    warning: 這個模式只有在交通方式是大眾運輸(Transportation.TRANSIT)時才有用
    """
    BUS = 'bus'  # 公車
    SUBWAY = 'subway'  # 地鐵
    TRAIN = 'train'  # 火車
    TRAM = 'tram'  # 有軌電車
    RAIL = 'rail'  # 輕軌
    FERRY = 'ferry'  # 渡輪


class GoogleMapApi:
    def __init__(self, key):
        self.key = key

    def directions(self, origin: str, destination: str, time_param: dict, mode=Transportation.DRIVING,
                   transit_mode=TransitMode.BUS) -> dict:
        """
        用 google map directions api 取得兩點路線相關資訊
        如果找不到路線則回傳空dict
        output dict keys:
            - 'summary': 交通簡介
            - 'distance': 距離
            - 'duration': 交通順暢狀況下的時間
            - 'duration_in_traffic': 交通狀況下預估的時間
            - 'steps': 路線步驟
            - 'start_location': 起點經緯
            - 'end_location': 終點經緯
            - 'start_address': 起點地址
            - 'end_address': 終點地址

        :param origin: 起點
        :param destination: 終點
        :param mode: 交通方式
        :param time_param: 出發時間，格式為dict[is_now,year, month, day, hour, minute]
        :param transit_mode: 大眾運輸模式，使用Transportation.TRANSIT時才有作用
        :return: dict
        """
        if time_param['is_now'] == False:
            taiwan_timezone = pytz.timezone('Asia/Taipei')  # 設定時區
            taiwan_time_point = datetime(time_param['year'], time_param['month'], time_param['day'], time_param['hour'],
                                         time_param['minute'], tzinfo=taiwan_timezone)
            current_time = datetime.now(taiwan_timezone)
            if taiwan_time_point < current_time:  # 如果輸入的時間比現在時間還早 就raise error
                raise NotFutureTime(current_time, taiwan_time_point)

            departure_time = int(taiwan_time_point.timestamp())
        else:
            departure_time = 'now'

        url = (f'https://maps.googleapis.com/maps/api/directions/json')
        params = {
            'origin': origin,
            'destination': destination,
            'key': self.key,
            'departure_time': departure_time,
            'mode': mode,
            # 'alternatives': str(alternatives).lower(), # 是否要多條路線
            'language': 'zh-TW',
            'region': 'JP',
        }

        if mode == Transportation.TRANSIT:  # 如果是大眾運輸模式，就加入大眾運輸模式參數
            params['transit_mode'] = transit_mode

        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 'ZERO_RESULTS':
                return {}
            elif result['status'] == 'OK':
                routes = result['routes'][0]
                output_dict = {
                    'summary': routes['summary'],  # 交通簡介
                    'distance': routes['legs'][0]['distance']['text'],  # 距離
                    'duration': routes['legs'][0]['duration']['text'],  # 交通順暢狀況下的時間
                    'duration_in_traffic': routes['legs'][0]['duration_in_traffic'][  # 交通狀況下預估的時間
                        'text'] if 'duration_in_traffic' in routes['legs'][0] else None,
                    'steps': routes['legs'][0]['steps'],  # 路線步驟
                    'start_location': routes['legs'][0]['start_location'],  # 起點經緯
                    'end_location': routes['legs'][0]['end_location'],  # 終點經緯
                    'start_address': routes['legs'][0]['start_address'],  # 起點地址
                    'end_address': routes['legs'][0]['end_address'],  # 終點地址

                }
                return output_dict

            elif result['status'] == 'NOT_FOUND':  # 如果找不到景點，就raise error
                not_found_place = []
                if result['geocoded_waypoints'][0]['geocoder_status'] == 'ZERO_RESULTS':
                    not_found_place.append(origin)
                if result['geocoded_waypoints'][1]['geocoder_status'] == 'ZERO_RESULTS':
                    not_found_place.append(destination)

                raise SearchDirectionsFailed(response.status_code,
                                            f'{not_found_place} not found. Please check the input.')
            else:  # 如果status不是OK或ZERO_RESULTS，就raise error
                raise SearchDirectionsFailed(response.status_code, 'status = ' + result['status'])

        else:  # 如果response.status_code不是200，就raise error
            raise SearchDirectionsFailed(response.status_code, response.text)


if __name__ == '__main__':
    origin = '難波JR站'
    destination = '大阪城'

    gmap = GoogleMapApi(key=os.getenv("MAP_KEY"))
    try:
        time_setting = {
            'is_now': False,
            'year': 2024,
            'month': 3,
            'day': 28,
            'hour': 20,
            'minute': 45
        }

        time_setting2 = {
            'is_now': True,
        }

        output_dict = gmap.directions(origin, destination, time_setting, Transportation.WALKING)
        output_dict = gmap.directions(origin, destination, time_setting, Transportation.DRIVING)
        output_dict = gmap.directions(origin, destination, time_setting2, Transportation.BICYCLING)
        output_dict = gmap.directions(origin=origin, destination=destination, time_param=time_setting2,
                                      mode=Transportation.TRANSIT, transit_mode=TransitMode.BUS)  # 大眾運輸模式 找不到會回傳空dict
    except SearchDirectionsFailed as e:
        print(e)
    except NotFutureTime as e:  # 如果輸入的時間比現在時間還早 就raise error
        print(e)
    except Exception as e:
        traceback.print_exc()
