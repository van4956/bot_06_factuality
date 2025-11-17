#!/usr/bin/env python3
"""
Скрипт для автоматического заполнения пустых msgstr в .po файлах.
Копирует содержимое из msgid в msgstr, если msgstr пустой.
"""

import sys
from pathlib import Path


def process_po_file(input_file: str, output_file: str):
    """
    Обрабатывает .po файл: заполняет пустые msgstr содержимым из msgid.

    Args:
        input_file: путь к исходному .po файлу
        output_file: путь к результирующему .po файлу
    """

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result = []
    i = 0
    first_entry = True  # Флаг для пропуска заголовка файла
    pending_comments = []  # Накопитель комментариев перед msgid

    while i < len(lines):
        line = lines[i]

        # Устаревшие записи (начинаются с #~) - копируем как есть
        if line.startswith('#~'):
            # Сначала сбрасываем накопленные комментарии
            result.extend(pending_comments)
            pending_comments = []
            result.append(line)
            i += 1
            continue

        # Комментарии и пустые строки между блоками - накапливаем
        if line.startswith('#') or (line.strip() == '' and i > 0 and not lines[i-1].startswith('msgstr')):
            pending_comments.append(line)
            i += 1
            continue

        # Если нашли начало блока msgid
        if line.startswith('msgid '):
            # Сбрасываем накопленные комментарии в результат
            result.extend(pending_comments)
            pending_comments = []

            # Проверяем на plural формы (msgid_plural) - их пропускаем
            has_plural = False
            temp_i = i
            while temp_i < len(lines) and not lines[temp_i].strip() == '':
                if lines[temp_i].startswith('msgid_plural'):
                    has_plural = True
                    break
                temp_i += 1

            if has_plural:
                # Копируем весь блок с plural как есть до пустой строки
                while i < len(lines):
                    result.append(lines[i])
                    i += 1
                    if i < len(lines) and lines[i].strip() == '':
                        result.append(lines[i])
                        i += 1
                        break
                continue

            # Собираем содержимое msgid
            msgid_lines = []
            msgid_line = lines[i]  # добавляем "msgid ..."
            msgid_lines.append(msgid_line)
            i += 1

            # Проверяем, однострочный или многострочный msgid
            # Однострочный: msgid "текст"
            # Многострочный: msgid "" + строки в кавычках
            is_multiline_msgid = msgid_line.strip() == 'msgid ""'

            # Читаем продолжение msgid (строки в кавычках) только для многострочных
            if is_multiline_msgid:
                while i < len(lines) and lines[i].startswith('"'):
                    msgid_lines.append(lines[i])
                    i += 1

            # Проверяем, что дошли до msgstr
            if i >= len(lines) or not lines[i].startswith('msgstr '):
                # Что-то пошло не так, копируем как есть
                result.extend(msgid_lines)
                continue

            # Нашли msgstr
            msgstr_line = lines[i]
            i += 1

            # Собираем содержимое msgstr
            msgstr_content = []
            while i < len(lines) and lines[i].startswith('"'):
                msgstr_content.append(lines[i])
                i += 1

            # Пропускаем первый блок (заголовок файла с метаданными)
            if first_entry and msgid_lines[0].strip() == 'msgid ""':
                # Проверяем, что это действительно заголовок
                if msgstr_content and 'Project-Id-Version' in ''.join(msgstr_content):
                    result.extend(msgid_lines)
                    result.append(msgstr_line)
                    result.extend(msgstr_content)
                    first_entry = False
                    continue

            first_entry = False

            # Анализируем msgstr
            msgstr_empty = len(msgstr_content) == 0 and msgstr_line.strip() == 'msgstr ""'

            # Записываем msgid
            result.extend(msgid_lines)

            # Записываем msgstr
            if msgstr_empty:
                # msgstr пустой - копируем из msgid
                if is_multiline_msgid:
                    # Для многострочных: берем строки в кавычках
                    result.append(msgstr_line)
                    content_lines = [line for line in msgid_lines if line.startswith('"')]
                    result.extend(content_lines)
                else:
                    # Для однострочных: извлекаем текст из msgid и вставляем в msgstr
                    # msgid "текст" -> msgstr "текст"
                    msgid_text = msgid_line.replace('msgid ', '', 1)
                    result.append(f"msgstr {msgid_text}")
                print(f"✓ Заполнен пустой msgstr на строке {i}")
            else:
                # msgstr не пустой - записываем как есть или сравниваем
                result.append(msgstr_line)

                if is_multiline_msgid:
                    # Для многострочных: сравниваем содержимое
                    msgid_content = [line for line in msgid_lines if line.startswith('"')]

                    if msgid_content == msgstr_content:
                        # Совпадает - оставляем как есть
                        result.extend(msgstr_content)
                    else:
                        # Не совпадает - заменяем на msgid
                        result.extend(msgid_content)
                        print(f"⚠ Заменен отличающийся msgstr на строке {i}")
                else:
                    # Для однострочных: просто оставляем msgstr как есть (уже записали)
                    pass

            # Добавляем пустую строку после блока (если она есть)
            if i < len(lines) and lines[i].strip() == '':
                result.append(lines[i])
                i += 1
            else:
                result.append('\n')
        else:
            # Обычная строка - копируем как есть
            result.append(line)
            i += 1

    # Сбрасываем оставшиеся комментарии
    result.extend(pending_comments)

    # Записываем результат
    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(result)

    print(f"\n✅ Обработка завершена!")
    print(f"📥 Исходный файл: {input_file}")
    print(f"📤 Результат сохранен: {output_file}")


def main():
    """Главная функция с обработкой аргументов командной строки."""

    if len(sys.argv) < 2:
        print("Использование:")
        print("  python processing_file_po.py <input_file.po> [output_file.po]")
        print("\nПример:")
        print("  python processing_file_po.py locales/ru/LC_MESSAGES/bot_06_factuality.po")
        print("  python processing_file_po.py locales/en/LC_MESSAGES/bot_06_factuality.po _bot_06_factuality.po")
        sys.exit(1)

    input_file = sys.argv[1]

    # Если выходной файл не указан, создаем с префиксом "_"
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"_{input_path.name}")

    # Проверяем существование входного файла
    if not Path(input_file).exists():
        print(f"❌ Ошибка: файл не найден: {input_file}")
        sys.exit(1)

    print(f"🔄 Начинаем обработку файла: {input_file}")
    print(f"📝 Результат будет сохранен в: {output_file}\n")

    process_po_file(input_file, output_file)


if __name__ == "__main__":
    main()
