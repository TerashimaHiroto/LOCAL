import flet as ft
import requests
from datetime import datetime
import json
import sqlite3
from datetime import datetime, timedelta

# データベース初期化
def init_db():
    conn = sqlite3.connect('weather_forecast.db')
    c = conn.cursor()
    
    # エリア情報テーブル
    c.execute('''CREATE TABLE IF NOT EXISTS areas
                 (area_code TEXT PRIMARY KEY,
                  area_name TEXT,
                  parent_code TEXT)''')
    
    # 天気予報テーブル
    c.execute('''CREATE TABLE IF NOT EXISTS weather_forecasts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  area_code TEXT,
                  area_name TEXT,
                  forecast_date TEXT,
                  weather_code INTEGER,
                  temp_min REAL,
                  temp_max REAL,
                  created_at TEXT,
                  UNIQUE(area_code, area_name, forecast_date))''')
    
    conn.commit()
    conn.close()

# エリア情報をDBに保存
def save_area_data(areas_data):
    conn = sqlite3.connect('weather_forecast.db')
    c = conn.cursor()
    
    for code, data in areas_data.items():
        name = data.get("name")
        parent = data.get("parent", "")
        c.execute("INSERT OR REPLACE INTO areas VALUES (?, ?, ?)",
                 (code, name, parent))
    
    conn.commit()
    conn.close()

# 天気予報データをDBに保存
def save_weather_forecast(area_code, area_name, forecasts):
    conn = sqlite3.connect('weather_forecast.db')
    c = conn.cursor()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for forecast in forecasts:
        c.execute("""INSERT OR REPLACE INTO weather_forecasts
                    (area_code, area_name, forecast_date, weather_code,
                     temp_min, temp_max, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                 (area_code, area_name, forecast['date'],
                  forecast['weather_code'], forecast['temp_min'],
                  forecast['temp_max'], current_time))
    
    conn.commit()
    conn.close()

def get_weather_icon(code):
    code = str(code)
    if code.startswith('1'):
        return ft.icons.SUNNY
    elif code.startswith('2'):
        return ft.icons.CLOUD
    elif code.startswith('3'):
        return ft.icons.WATER_DROP
    elif code.startswith('4'):
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
                    ft.Text(f"{temp_min}℃" if temp_min else "-", color=ft.colors.BLUE),
                    ft.Text(" / ", color=ft.colors.WHITE),
                    ft.Text(f"{temp_max}℃" if temp_max else "-", color=ft.colors.RED),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            ),
            padding=20,
            width=150,
        )
    )

def load_area_data():
    try:
        response = requests.get("https://www.jma.go.jp/bosai/common/const/area.json")
        return response.json()
    except:
        with open('area.json', 'r', encoding='utf-8') as f:
            return json.load(f)

def create_list_item(text, code, is_selected=False):
    return ft.Container(
        content=ft.Column([
            ft.Text(
                text,
                size=16,
                color=ft.colors.WHITE,
                overflow=ft.TextOverflow.ELLIPSIS  # はみ出し防止
            ),
            ft.Text(
                code,
                size=12,
                color=ft.colors.WHITE70,
                overflow=ft.TextOverflow.ELLIPSIS  # はみ出し防止
            ),
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
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API呼び出しエラー: {e}")
        return None

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.DARK
    
    # データベース初期化
    init_db()

    # 天気予報表示用のコンテナ
    weather_display = ft.Column(
        spacing=20,
        scroll=ft.ScrollMode.AUTO,
    )

    # スクロール可能なコンテナを作成
    region_list = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)
    prefecture_list = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)

    # エリアデータの読み込み
    area_data = load_area_data()
    centers = area_data["centers"]
    offices = area_data["offices"]

    # 都道府県コードのマッピング作成
    prefecture_codes = {}
    for office_code, office_data in offices.items():
        if "parent" in office_data:
            prefecture_codes[office_code] = f"{int(office_code):06d}"

    # 今日から3日分の日付を取得
    def get_default_dates():
        dates = []
        today = datetime.now()
        for i in range(3):
            date = today + timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        return dates

    # 日付選択用のドロップダウン
    date_dropdown = ft.Dropdown(
        width=200,
        label="日付選択",
        color=ft.colors.WHITE,
    )

    def update_date_dropdown():
        conn = sqlite3.connect('weather_forecast.db')
        c = conn.cursor()
        # 過去のデータも含めて全ての日付を取得
        c.execute("SELECT DISTINCT forecast_date FROM weather_forecasts ORDER BY forecast_date")
        dates = c.fetchall()
        conn.close()

        # デフォルトの日付を設定
        default_dates = get_default_dates()
        
        date_dropdown.options = [
            ft.dropdown.Option(
                text=date[0],
                key=date[0],
            )
            for date in dates
        ]
        
        # デフォルトで今日の日付を選択
        if default_dates[0] in [opt.key for opt in date_dropdown.options]:
            date_dropdown.value = default_dates[0]
        
        page.update()

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
    # 選択した都道府県のハイライト表示
        for item in prefecture_list.controls:
            item.bgcolor = None
        e.control.bgcolor = ft.colors.PURPLE_700

        office_code = e.control.data
        prefecture_code = prefecture_codes[office_code]

        # 表示をクリアして読み込み中を表示
        weather_display.controls.clear()
        weather_display.controls.append(ft.ProgressRing())
        page.update()

        forecast_data = fetch_weather_forecast(prefecture_code)
        weather_display.controls.clear()

        if forecast_data:
            try:
                prefecture_name = offices[office_code]["name"]
                areas = forecast_data[0]["timeSeries"][0]["areas"]
                temps_data = forecast_data[0]["timeSeries"][2]["areas"]
                timeDefines = forecast_data[0]["timeSeries"][0]["timeDefines"]

                # 選択した都道府県の天気予報のみを表示
                weather_display.controls.append(
                    ft.Text(
                        f"{prefecture_name}の天気予報",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE,
                    )
                )

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

    def on_date_change(e):
        selected_date = date_dropdown.value
        if not selected_date:
            return

        weather_display.controls.clear()
        
        # 選択された日付から3日分のデータを取得
        dates = []
        start_date = datetime.strptime(selected_date, "%Y-%m-%d")
        for i in range(3):
            dates.append((start_date + timedelta(days=i)).strftime("%Y-%m-%d"))

        weather_display.controls.append(
            ft.Text(
                f"{dates[0]}から3日間の天気予報",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            )
        )

        # 各日付のデータを取得して表示
        for forecast_date in dates:
            conn = sqlite3.connect('weather_forecast.db')
            c = conn.cursor()
            c.execute("""SELECT area_name, weather_code, temp_min, temp_max
                        FROM weather_forecasts
                        WHERE forecast_date = ?
                        ORDER BY area_name""", (forecast_date,))
            forecasts = c.fetchall()
            conn.close()

            if forecasts:
                weather_display.controls.append(
                    ft.Text(
                        f"\n{forecast_date}",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE,
                    )
                )

                current_area = None
                weather_row = None

                for forecast in forecasts:
                    area_name, weather_code, temp_min, temp_max = forecast
                    
                    if area_name != current_area:
                        if weather_row:
                            weather_display.controls.append(weather_row)
                        
                        current_area = area_name
                        weather_display.controls.append(
                            ft.Text(
                                f"\n{area_name}",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.WHITE,
                            )
                        )
                        weather_row = ft.Row(
                            scroll=ft.ScrollMode.AUTO,
                            spacing=10,
                        )

                    weather_row.controls.append(
                        create_weather_card(
                            datetime.strptime(forecast_date, "%Y-%m-%d"),
                            weather_code,
                            temp_min,
                            temp_max
                        )
                    )

                if weather_row:
                    weather_display.controls.append(weather_row)

        page.update()

    date_dropdown.on_change = on_date_change

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
                    date_dropdown,
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

    # エリアデータの保存
    save_area_data(area_data["centers"])
    save_area_data(area_data["offices"])

    # 初期の地方リストを作成
    for center_code, center_data in centers.items():
        item = create_list_item(center_data["name"], center_code)
        item.on_click = handle_center_click
        region_list.controls.append(item)

    page.update()

ft.app(target=main)