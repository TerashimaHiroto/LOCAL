import flet as ft
import requests

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.DARK

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
    area_list = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)

    # データ読み込み
    area_data = load_area_data()
    centers = area_data["centers"]
    offices = area_data["offices"]
    class10s = area_data["class10s"]  # 地域詳細データ

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

    def handle_center_click(e):
        for item in region_list.controls:
            item.bgcolor = None
        e.control.bgcolor = ft.colors.PURPLE_700

        center_code = e.control.data
        prefecture_list.controls.clear()
        area_list.controls.clear()

        for office_code, office_data in offices.items():
            if office_data.get("parent") == center_code:
                item = create_list_item(office_data["name"], office_code)
                item.on_click = handle_prefecture_click
                prefecture_list.controls.append(item)

        page.update()

    def handle_prefecture_click(e):
        for item in prefecture_list.controls:
            item.bgcolor = None
        e.control.bgcolor = ft.colors.PURPLE_700

        office_code = e.control.data
        office_data = offices.get(office_code, {})
        area_list.controls.clear()

        if "children" in office_data:
            for child_code in office_data["children"]:
                # 地域名を取得
                area_name = class10s.get(child_code, {}).get("name", "不明")
                item = create_list_item(area_name, child_code)
                item.on_click = handle_area_click
                area_list.controls.append(item)

        page.update()

    def handle_area_click(e):
        for item in area_list.controls:
            item.bgcolor = None
        e.control.bgcolor = ft.colors.PURPLE_700
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
            ft.Divider(height=1, color=ft.colors.WHITE24),
            ft.Container(
                content=ft.Text("地域", weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                padding=10
            ),
            ft.Container(
                content=area_list,
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
                    content=ft.Column([
                        ft.Text("天気予報が表示されます", color=ft.colors.WHITE),
                    ]),
                    expand=True,
                    padding=20,
                ),
            ],
            expand=True,
        ),
    )

ft.app(target=main)