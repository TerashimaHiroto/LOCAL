import flet as ft
import requests
from datetime import datetime
import json

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.DARK

    # 天気予報表示用のコンテナ
    weather_display = ft.Column(
        spacing=20,
        scroll=ft.ScrollMode.AUTO,
    )

    def load_area_data():
        try:
            response = requests.get("http://www.jma.go.jp/bosai/common/const/area.json")
            return response.json()
        except:
            with open('area.json', 'r', encoding='utf-8') as f:
                return json.load(f)

    # スクロール可能なコンテナを作成
    region_list = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)
    prefecture_list = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)

    # データ読み込み
    area_data = load_area_data()
    centers = area_data["centers"]
    offices = area_data["offices"]

    # 都道府県コードのマッピング作成
    prefecture_codes = {}
    for office_code, office_data in offices.items():
        if "parent" in office_data:
            prefecture_codes[office_code] = f"{int(office_code):06d}"

    def get_weather_icon(code):
        # 気象庁の天気コードに基づいてアイコンを返す
        code = str(code)
        if code.startswith('1'): # 100番台は晴れ
            return ft.icons.SUNNY
        elif code.startswith('2'): # 200番台は曇り
            return ft.icons.CLOUD
        elif code.startswith('3'): # 300番台は雨
            return ft.icons.WATER_DROP
        elif code.startswith('4'): # 400番台は雪
            return ft.icons.AC_UNIT
        else:
            return ft.icons.QUESTION_MARK
        

    def create_weather_card(date, weather_code, temp_min, temp_max):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        date.strftime("%Y-%m-%d"),
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE,
                    ),
                    ft.Icon(
                        get_weather_icon(weather_code),
                        size=40,
                        color=ft.colors.YELLOW if str(weather_code).startswith('1') else ft.colors.WHITE,
                    ),
                    ft.Text(str(weather_code), color=ft.colors.WHITE),
                    ft.Row([
                        ft.Text(f" {temp_min}℃" if temp_min else "-", color=ft.colors.BLUE),
                        ft.Text(" / ", color=ft.colors.WHITE),
                        ft.Text(f" {temp_max}℃" if temp_max else "-", color=ft.colors.RED),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                ),
                padding=20,
                width=150,
            )
        )

    def create_list_item(text, code, is_selected=False):
        return ft.Container(
            content=ft.Column([
                ft.Text(text, size=16, color=ft.colors.WHITE),
                ft.Text(code, size=12, color=ft.colors.WHITE70),
            ]),
            bgcolor=ft.colors.PURPLE_700 if is_selected else None,
            padding=10,
            border_radius=10,
            data=code,
            width=250
        )
    def fetch_weather_forecast(area_code):
        try:
            base_url = "https://www.jma.go.jp/bosai/forecast/data/forecast"
            url = f"{base_url}/{area_code}.json"
            print(f"API URL: {url}")  # デバッグ用のURL表示
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API呼び出しエラー: {e}")
            return None

    def handle_center_click(e):
        for item in region_list.controls:
            item.bgcolor = None
        e.control.bgcolor = ft.colors.PURPLE_700

        center_code = e.control.data
        prefecture_list.controls.clear()
        weather_display.controls.clear()
        weather_display.controls.append(ft.Text("都道府県を選択してください", color=ft.colors.WHITE))

        for office_code, office_data in offices.items():
            if (office_data.get("parent") == center_code and 
                "parent" in office_data):
                item = create_list_item(office_data["name"], office_code)
                item.on_click = handle_prefecture_click
                prefecture_list.controls.append(item)

        page.update()

    def handle_prefecture_click(e):
        for item in prefecture_list.controls:
            item.bgcolor = None
        e.control.bgcolor = ft.colors.PURPLE_700

        office_code = e.control.data
        if office_code not in prefecture_codes:
            weather_display.controls.clear()
            weather_display.controls.append(
                ft.Text("この地域の天気予報は取得できません", color=ft.colors.RED)
            )
            page.update()
            return

        prefecture_code = prefecture_codes[office_code]
        
        weather_display.controls.clear()
        weather_display.controls.append(ft.ProgressRing())
        page.update()

        forecast_data = fetch_weather_forecast(prefecture_code)
        weather_display.controls.clear()

        if forecast_data:
            try:
                prefecture_name = offices[office_code]["name"]
                weather_display.controls.append(
                    ft.Text(
                        f"{prefecture_name}の天気予報",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE,
                    )
                )

                areas = forecast_data[0]["timeSeries"][0]["areas"]
                temps_data = forecast_data[0]["timeSeries"][2]["areas"]  # 気温データ
                
                for area_index, area in enumerate(areas):
                    area_name = area["area"]["name"]
                    weather_codes = area["weatherCodes"]
                    
                    weather_display.controls.append(
                        ft.Text(
                            f"\n{area_name}",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.WHITE,
                        )
                    )

                    weather_row = ft.Row(
                        scroll=ft.ScrollMode.AUTO,
                        spacing=10,
                    )

                    timeDefines = forecast_data[0]["timeSeries"][0]["timeDefines"]
                    
                    for i, time in enumerate(timeDefines):
                        date = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S+09:00")
                        weather_code = weather_codes[i]
                        
                        # 気温データの取得
                        temp_min = temps_data[area_index]["temps"][i*2] if i < len(temps_data[area_index]["temps"])//2 else None
                        temp_max = temps_data[area_index]["temps"][i*2+1] if i < len(temps_data[area_index]["temps"])//2 else None
                        
                        weather_row.controls.append(
                            create_weather_card(date, weather_code, temp_min, temp_max)
                        )

                    weather_display.controls.append(weather_row)

            except Exception as e:
                weather_display.controls.append(
                    ft.Text(f"データの解析中にエラーが発生しました: {e}", color=ft.colors.RED)
                )
        else:
            weather_display.controls.append(
                ft.Text("天気予報データの取得に失敗しました", color=ft.colors.RED)
            )

        page.update()

    # 初期の地方リストを作成
    for center_code, center_data in centers.items():
        item = create_list_item(center_data["name"], center_code)
        item.on_click = handle_center_click
        region_list.controls.append(item)

    # スクロール可能なコンテナを作成
    scrollable_column = ft.Column(
        [
            ft.Container(
                content=ft.Text("地方選択", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                padding=10
            ),
            ft.Container(
                content=region_list,
                height=300,
                padding=10
            ),
            ft.Divider(height=1, color=ft.colors.WHITE24),
            ft.Container(
                content=ft.Text("都道府県", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                padding=10
            ),
            ft.Container(
                content=prefecture_list,
                height=300,
                padding=10
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
    )

    # レイアウト
    page.add(
        ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.SUNNY, color=ft.colors.WHITE),
                    ft.Text("天気予報", size=20, weight=ft.FontWeight.BOLD),
                ],
            ),
            padding=15,
            bgcolor=ft.colors.PURPLE_700,
        ),
        ft.Row(
            [
                ft.Container(
                    content=scrollable_column,
                    width=300,
                    bgcolor="#78909C",
                ),
                ft.VerticalDivider(width=1, color=ft.colors.WHITE24),
                ft.Container(
                    content=weather_display,
                    expand=True,
                    padding=20,
                ),
            ],
            expand=True,
        ),
    )

ft.app(target=main)