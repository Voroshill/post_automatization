import xlsxwriter
from io import BytesIO
from typing import List
from app.domain.entities.user import User, UserStatus
from app.core.logging.logger import export_logger


class ExportService:
    def __init__(self):
        export_logger.info("ExportService инициализирован")

    def export_users_to_xlsx(self, users: List[User], status_filter: str = None) -> bytes:
        """
        Экспорт пользователей в XLSX файл
        """
        try:
            export_logger.info(f"Начало экспорта {len(users)} пользователей в XLSX")
            output = BytesIO()

            workbook = xlsxwriter.Workbook(output)
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4F81BD',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            cell_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })
            status_formats = {
                UserStatus.PENDING: workbook.add_format({
                    'border': 1,
                    'bg_color': '#FFF2CC',
                    'align': 'center'
                }),
                UserStatus.CREATING: workbook.add_format({
                    'border': 1,
                    'bg_color': '#B7D7FF',
                    'align': 'center'
                }),
                UserStatus.APPROVED: workbook.add_format({
                    'border': 1,
                    'bg_color': '#D5E8D4',
                    'align': 'center'
                }),
                UserStatus.REJECTED: workbook.add_format({
                    'border': 1,
                    'bg_color': '#F8CECC',
                    'align': 'center'
                }),
                UserStatus.DISMISSED: workbook.add_format({
                    'border': 1,
                    'bg_color': '#E1D5E7',
                    'align': 'center'
                })
            }
            worksheet = workbook.add_worksheet('Пользователи')
            headers = [
                'ID', 'Уникальный ID', 'Фамилия', 'Имя', 'Отчество', 'Компания',
                'Подразделение', 'Отдел', 'Должность', 'Руководитель ID',
                'Локация ID', 'Рабочий телефон',
                'Дата рождения', 'Инженер', 'Дата загрузки', 'Статус'
            ]
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            for row, user in enumerate(users, start=1):
                try:
                    status_format = status_formats.get(user.status, cell_format)
                    worksheet.write(row, 0, user.id, cell_format)
                    worksheet.write(row, 1, user.unique_id, cell_format)
                    worksheet.write(row, 2, user.secondname or '', cell_format)
                    worksheet.write(row, 3, user.firstname or '', cell_format)
                    worksheet.write(row, 4, user.thirdname or '', cell_format)
                    worksheet.write(row, 5, user.company or '', cell_format)
                    worksheet.write(row, 6, user.department or '', cell_format)
                    worksheet.write(row, 7, user.otdel or '', cell_format)
                    worksheet.write(row, 8, user.appointment or '', cell_format)
                    worksheet.write(row, 9, user.boss_id or '', cell_format)
                    worksheet.write(row, 10, user.current_location_id or '', cell_format)
                    worksheet.write(row, 11, user.work_phone or '', cell_format)
                    worksheet.write(row, 12, str(user.birth_date) if user.birth_date else '', cell_format)
                    worksheet.write(row, 13, 'Да' if user.is_engineer else 'Нет', cell_format)
                    worksheet.write(row, 14, str(user.upload_date) if user.upload_date else '', cell_format)
                    worksheet.write(row, 15, user.status.value, status_format)
                    
                except Exception as e:
                    export_logger.error(f"Ошибка записи пользователя {user.id}: {e}")
                    continue
            
            worksheet.set_column(0, 0, 8)   # ID
            worksheet.set_column(1, 1, 15)  # Уникальный ID
            worksheet.set_column(2, 4, 20)  # ФИО
            worksheet.set_column(5, 5, 25)  # Компания
            worksheet.set_column(6, 7, 20)  # Подразделение, Отдел
            worksheet.set_column(8, 8, 25)  # Должность
            worksheet.set_column(9, 10, 12) # ID руководителя и локации
            worksheet.set_column(11, 11, 15) # Телефон
            worksheet.set_column(12, 12, 12) # Дата рождения
            worksheet.set_column(13, 13, 10) # Инженер
            worksheet.set_column(14, 14, 15) # Дата загрузки
            worksheet.set_column(15, 15, 12) # Статус
            
            stats_worksheet = workbook.add_worksheet('Статистика')
            
            # Статистика по статусам
            status_counts = {}
            for user in users:
                status_counts[user.status.value] = status_counts.get(user.status.value, 0) + 1

            stats_headers = ['Статус', 'Количество']
            for col, header in enumerate(stats_headers):
                stats_worksheet.write(0, col, header, header_format)
            
            for row, (status, count) in enumerate(status_counts.items(), start=1):
                stats_worksheet.write(row, 0, status, cell_format)
                stats_worksheet.write(row, 1, count, cell_format)
            
            stats_worksheet.write(len(status_counts) + 2, 0, 'Всего пользователей:', header_format)
            stats_worksheet.write(len(status_counts) + 2, 1, len(users), cell_format)
            
            if status_filter:
                stats_worksheet.write(len(status_counts) + 3, 0, f'Фильтр по статусу:', header_format)
                stats_worksheet.write(len(status_counts) + 3, 1, status_filter, cell_format)
            
            stats_worksheet.set_column(0, 0, 20)
            stats_worksheet.set_column(1, 1, 15)

            workbook.close()
            output.seek(0)
            data = output.getvalue()
            output.close()
            
            export_logger.info(f"Экспорт завершен успешно. Размер файла: {len(data)} байт")
            return data
            
        except Exception as e:
            export_logger.error(f"Ошибка экспорта в XLSX: {e}")
            raise
