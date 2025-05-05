import flet as ft
import os
import requests
import base64
from PIL import Image
from io import BytesIO
import tempfile

# endpoint da api
API_URL = "http://127.0.0.1:8000/analyze"

# Cores que vamos usar
PRIMARY_COLOR = "#6200EE"
SECONDARY_COLOR = "#03DAC6"
BACKGROUND_COLOR = "#FAFAFA"
CARD_COLOR = "#FFFFFF"
SUCCESS_COLOR = "#4CAF50"
ERROR_COLOR = "#F44336"
NEUTRAL_COLOR = "#9E9E9E"


class NotifiCheckApp:
    def __init__(self):
        self.selected_file_path = None
        self.is_analyzing = False
        self.reference_dir = r"C:\proj_notific_fake\data\real"

    def main(self, page: ft.Page):
        page.title = "NotifiCheck - Verificador de Notificações"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.bgcolor = BACKGROUND_COLOR
        page.window_width = 1000
        page.window_height = 800
        page.window_min_width = 400
        page.scroll = ft.ScrollMode.AUTO

        # Tirulo do app
        title = ft.Text(
            "NotifiCheck",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=PRIMARY_COLOR,
        )

        subtitle = ft.Text(
            "Verificamos se uma notificação é verdadeira",
            size=16,
            color=NEUTRAL_COLOR,
            italic=True,
        )

        # arquivos para selecionar a imagem
        def on_file_picked(e: ft.FilePickerResultEvent):
            if e.files and len(e.files) > 0:
                self.selected_file_path = e.files[0].path
                selected_file.value = f"Arquivo selecionado: {os.path.basename(self.selected_file_path)}"

                # Exibir a imagem
                with open(self.selected_file_path, "rb") as f:
                    image_bytes = f.read()
                    img = Image.open(BytesIO(image_bytes))

                    max_width = 300
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((max_width, new_height))

                    # Salvar em arquivo temporário
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp:
                        img.save(temp.name)
                        temp_path = temp.name

                selected_image.src = temp_path
                selected_image.visible = True

                analyze_btn.disabled = False

                page.update()

        file_picker = ft.FilePicker(on_result=on_file_picked)
        page.overlay.append(file_picker)

        pick_files_btn = ft.ElevatedButton(
            "Selecionar imagem",
            icon=ft.icons.UPLOAD_FILE,
            on_click=lambda _: file_picker.pick_files(
                allowed_extensions=["png", "jpg", "jpeg"],
                allow_multiple=False
            ),
            style=ft.ButtonStyle(
                bgcolor=PRIMARY_COLOR,
                color=ft.colors.WHITE,
            ),
            height=50,
        )

        selected_file = ft.Text("Nenhum arquivo selecionado", size=14)

        # preview da imagem
        selected_image = ft.Image(
            visible=False,
            fit=ft.ImageFit.CONTAIN,
            border_radius=10,
        )

        # Indicador de carregamento
        progress_ring = ft.ProgressRing(
            width=40,
            height=40,
            stroke_width=4,
            color=PRIMARY_COLOR,
            visible=False
        )

        # Resultados dentro do container
        result_section = ft.Container(
            visible=False,
            padding=20,
            bgcolor=CARD_COLOR,
            border_radius=10,
            content=ft.Column(
                spacing=20,
                controls=[
                    ft.Text("Resultado da análise", size=20,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(height=0),
                ],
            ),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
            )
        )

        # analisnado a iamgem
        def analyze_image(e):
            if not self.selected_file_path:
                return

            progress_ring.visible = True
            analyze_btn.disabled = True
            result_section.visible = False
            page.update()

            try:
                with open(self.selected_file_path, "rb") as file:
                    files = {"file": (os.path.basename(
                        self.selected_file_path), file, "image/jpeg")}
                    data = {"reference_dir": self.reference_dir}

                    response = requests.post(API_URL, files=files, data=data)

                    if response.status_code == 200:
                        result = response.json()

                        result_color = SUCCESS_COLOR if result["is_authentic"] else ERROR_COLOR

                        result_content = ft.Column(
                            spacing=20,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(
                                            ft.icons.CHECK_CIRCLE if result["is_authentic"] else ft.icons.ERROR,
                                            size=50,
                                            color=result_color
                                        ),
                                        ft.Text(
                                            "Notificação Autêntica" if result["is_authentic"] else "Notificação Suspeita",
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                            color=result_color
                                        )
                                    ]
                                ),
                                ft.Container(
                                    padding=10,
                                    bgcolor=ft.colors.with_opacity(
                                        0.1, result_color),
                                    border_radius=10,
                                    content=ft.Column(
                                        spacing=10,
                                        controls=[
                                            ft.Text(
                                                f"Confiança: {result['confidence']:.2f}%", size=16),
                                            ft.Image(
                                                src_base64=result["confidence_chart"],
                                                width=400,
                                                fit=ft.ImageFit.CONTAIN,
                                            ),
                                        ]
                                    )
                                ),
                                ft.Divider(),
                                ft.Text("Detalhes da análise",
                                        weight=ft.FontWeight.BOLD, size=18),
                                ft.DataTable(
                                    columns=[
                                        ft.DataColumn(ft.Text("Métrica")),
                                        ft.DataColumn(ft.Text("Valor")),
                                    ],
                                    rows=[
                                        ft.DataRow(
                                            cells=[
                                                ft.DataCell(
                                                    ft.Text("Pontuação combinada")),
                                                ft.DataCell(
                                                    ft.Text(f"{result['combined_score']:.4f}")),
                                            ]
                                        ),
                                        ft.DataRow(
                                            cells=[
                                                ft.DataCell(
                                                    ft.Text("Similaridade visual ")),
                                                ft.DataCell(
                                                    ft.Text(f"{result['visual_similarity']:.4f}")),
                                            ]
                                        ),
                                        ft.DataRow(
                                            cells=[
                                                ft.DataCell(
                                                    ft.Text("Similaridade semântica")),
                                                ft.DataCell(
                                                    ft.Text(f"{result['semantic_similarity']:.4f}")),
                                            ]
                                        ),
                                    ],
                                ),
                            ]
                        )

                        # Update the result section
                        result_section.content.controls.pop()  # Remove placeholder
                        result_section.content.controls.append(result_content)
                        result_section.visible = True

                    else:
                        # Display error
                        error_content = ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(ft.icons.ERROR, size=50,
                                                color=ERROR_COLOR),
                                        ft.Text(
                                            "Erro na análise", size=24, weight=ft.FontWeight.BOLD, color=ERROR_COLOR)
                                    ]
                                ),
                                ft.Text(
                                    f"Erro: {response.status_code}"),
                                ft.Text(response.text),
                            ]
                        )
                        result_section.content.controls.pop()
                        result_section.content.controls.append(error_content)
                        result_section.visible = True

            except Exception as e:

                error_content = ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.icons.ERROR, size=50,
                                        color=ERROR_COLOR),
                                ft.Text("Erro de conexão", size=24,
                                        weight=ft.FontWeight.BOLD, color=ERROR_COLOR)
                            ]
                        ),
                        ft.Text(f"Não foi possível conectar à API: {str(e)}"),
                        ft.Text(
                            "Verifique se o servidor está em execução."),
                    ]
                )
                result_section.content.controls.pop()
                result_section.content.controls.append(error_content)
                result_section.visible = True

            finally:

                progress_ring.visible = False
                analyze_btn.disabled = False
                page.update()

        # Bora de analisar
        analyze_btn = ft.ElevatedButton(
            "Analisar ",
            icon=ft.icons.SEARCH,
            on_click=analyze_image,
            style=ft.ButtonStyle(
                bgcolor=SECONDARY_COLOR,
                color=ft.colors.BLACK,
            ),
            disabled=True,
            height=50,
        )

        # rodapé
        footer = ft.Text(
            "© 2025 NotifiCheck - Daniel Pereira da Silva",
            size=12,
            color=NEUTRAL_COLOR,
            text_align=ft.TextAlign.CENTER,
        )

        # Layout
        page.add(
            ft.Container(
                content=ft.Column(
                    spacing=20,
                    controls=[
                        # Header
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    title,
                                    subtitle,
                                ],
                                spacing=5,
                            ),
                            margin=ft.margin.only(bottom=10),
                        ),


                        ft.ResponsiveRow(
                            controls=[

                                ft.Column(
                                    col={"sm": 12, "md": 5, "lg": 4},
                                    spacing=20,
                                    controls=[
                                        ft.Container(
                                            padding=20,
                                            bgcolor=CARD_COLOR,
                                            border_radius=10,
                                            content=ft.Column(
                                                spacing=20,
                                                controls=[
                                                    ft.Text(
                                                        "Selecione uma imagem", size=18, weight=ft.FontWeight.BOLD),
                                                    pick_files_btn,
                                                    selected_file,
                                                    ft.Divider(),
                                                    ft.Container(
                                                        content=selected_image,
                                                        alignment=ft.alignment.center,
                                                        margin=10,
                                                    ),
                                                    ft.Row(
                                                        controls=[
                                                            analyze_btn, progress_ring],
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                    ),
                                                ],
                                            ),
                                            shadow=ft.BoxShadow(
                                                spread_radius=1,
                                                blur_radius=10,
                                                color=ft.colors.with_opacity(
                                                    0.1, ft.colors.BLACK),
                                            )
                                        ),
                                    ],
                                ),

                                #
                                ft.Column(
                                    col={"sm": 12, "md": 7, "lg": 8},
                                    spacing=20,
                                    controls=[
                                        result_section,
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                padding=20,
            ),


            ft.Container(
                content=footer,
                padding=20,
                alignment=ft.alignment.center,
            ),
        )


if __name__ == "__main__":
    app = NotifiCheckApp()
    ft.app(target=app.main)
