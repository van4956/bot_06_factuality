import sys
import time
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# API ключ OpenAI из .env
API_GPT = os.getenv('API_GPT') 


def translate_with_openai(russian_text: str) -> str:
    """
    Переводит текст с русского на английский через OpenAI API.

    Args:
        russian_text: Текст на русском языке для перевода

    Returns:
        Переведенный текст на английском языке
    """

    system_prompt = """You are a professional translator specializing in educational content.
Translate from Russian to English for a Telegram bot about Hans Rosling's "Factfulness" book quiz.

CRITICAL RULES:
1. Keep ALL placeholders EXACTLY as they are: {user_answer}, {cnt_res}, {avg_result:.1f}, etc.
2. Keep ALL HTML tags EXACTLY: <i>, <b>, <code>
3. Keep ALL line breaks (\\n) exactly as in original
4. Keep ALL emojis unchanged (📖, 📊, ℹ️, 🤖, etc.)
5. Translate "Правильно:" as "Correct answer:"
6. Translate "Ваш ответ:" as "Your answer:"
7. Translate "Объяснение:" as "Explanation:"
8. Translate "UPD 2025:" as "UPD 2025:" (keep unchanged)
9. Maintain professional educational tone
10. For button text, use concise translations

RESPOND ONLY WITH THE TRANSLATED TEXT, NO EXPLANATIONS OR COMMENTS."""

    # Инициализируем клиент внутри функции
    client = OpenAI(api_key=API_GPT)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Экономичная модель с отличным качеством
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": russian_text}
            ],
            temperature=0.3,  # Низкая температура для стабильности перевода
            max_tokens=2000  # Достаточно для длинных объяснений
        )

        translated = response.choices[0].message.content.strip()
        return translated

    except Exception as e:
        print(f"❌ Ошибка при переводе: {e}")
        return russian_text  # В случае ошибки возвращаем оригинал


def extract_text_from_lines(lines: list) -> str:
    """
    Извлекает текст из строк msgid/msgstr формата .po файла.

    Примеры:
        msgid "Текст"  ->  "Текст"
        msgid ""
        "Строка 1"
        "Строка 2"     ->  "Строка 1\\nСтрока 2"
    """
    result = []

    for line in lines:
        line = line.strip()

        # Однострочный формат: msgid "текст"
        if line.startswith('msgid ') or line.startswith('msgstr '):
            # Извлекаем все после 'msgid ' или 'msgstr '
            quote_part = line.split(' ', 1)[1] if ' ' in line else '""'
            if quote_part.startswith('"') and quote_part.endswith('"'):
                text = quote_part[1:-1]
                result.append(text)
        # Многострочный формат: "текст"
        elif line.startswith('"') and line.endswith('"'):
            text = line[1:-1]
            result.append(text)

    return ''.join(result)


def format_text_to_lines(text: str, is_multiline_original: bool) -> list:
    """
    Форматирует переведенный текст обратно в формат .po файла.

    Args:
        text: Переведенный текст
        is_multiline_original: Был ли оригинальный msgid многострочным

    Returns:
        Список строк для записи в .po файл
    """
    if not text:
        return ['msgstr ""\n']

    # Если оригинал был однострочным, пытаемся сохранить однострочный формат
    if not is_multiline_original and '\n' not in text and len(text) < 80:
        return [f'msgstr "{text}"\n']

    # Многострочный формат
    result = ['msgstr ""\n']

    # Разбиваем по \n, сохраняя их как часть текста
    lines = text.split('\\n')

    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            result.append(f'"{line}\\n"\n')
        else:
            result.append(f'"{line}"\n')

    return result


def process_po_file(input_file: str, output_file: str):
    """
    Обрабатывает .po файл: заполняет пустые msgstr переводом из msgid.

    Args:
        input_file: путь к исходному .po файлу
        output_file: путь к результирующему .po файлу
    """

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result = []
    i = 0
    first_entry = True
    pending_comments = []

    translation_count = 0
    skip_count = 0

    print(f"\n🔄 Начинаем обработку файла: {input_file}")
    print(f"📝 Результат будет сохранен в: {output_file}\n")

    while i < len(lines):
        line = lines[i]

        # Устаревшие записи (#~) - копируем как есть
        if line.startswith('#~'):
            result.extend(pending_comments)
            pending_comments = []
            result.append(line)
            i += 1
            continue

        # Комментарии и пустые строки - накапливаем
        if line.startswith('#') or (line.strip() == '' and i > 0 and not lines[i-1].startswith('msgstr')):
            pending_comments.append(line)
            i += 1
            continue

        # Если нашли начало блока msgid
        if line.startswith('msgid '):
            # Сбрасываем накопленные комментарии
            result.extend(pending_comments)
            pending_comments = []

            # Проверяем на plural формы - пропускаем
            has_plural = False
            temp_i = i
            while temp_i < len(lines) and not lines[temp_i].strip() == '':
                if lines[temp_i].startswith('msgid_plural'):
                    has_plural = True
                    break
                temp_i += 1

            if has_plural:
                # Копируем весь блок с plural как есть
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
            msgid_line = lines[i]
            msgid_lines.append(msgid_line)
            i += 1

            # Определяем, однострочный или многострочный msgid
            is_multiline_msgid = msgid_line.strip() == 'msgid ""'

            # Читаем продолжение msgid
            if is_multiline_msgid:
                while i < len(lines) and lines[i].startswith('"'):
                    msgid_lines.append(lines[i])
                    i += 1

            # Проверяем, что дошли до msgstr
            if i >= len(lines) or not lines[i].startswith('msgstr '):
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

            # Обрабатываем msgstr
            if msgstr_empty:
                # msgstr пустой - переводим через OpenAI

                # Извлекаем текст из msgid
                russian_text = extract_text_from_lines(msgid_lines)

                if not russian_text:
                    # Пустой msgid - оставляем пустой msgstr
                    result.append(msgstr_line)
                    skip_count += 1
                else:
                    # Переводим через OpenAI
                    print(f"🔄 Перевод [{translation_count + 1}]: {russian_text[:60]}...")

                    english_text = translate_with_openai(russian_text)

                    print(f"✅ Готово: {english_text[:60]}...\n")

                    # Форматируем обратно в .po формат
                    translated_lines = format_text_to_lines(english_text, is_multiline_msgid)
                    result.extend(translated_lines)

                    translation_count += 1

                    # Небольшая задержка между запросами (rate limiting)
                    time.sleep(0.5)
            else:
                # msgstr уже заполнен - оставляем как есть
                result.append(msgstr_line)
                result.extend(msgstr_content)
                skip_count += 1

            # Добавляем пустую строку после блока
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
    print(f"📊 Статистика:")
    print(f"   🔄 Переведено записей: {translation_count}")
    print(f"   ⏭️  Пропущено (уже заполнено): {skip_count}")
    print(f"📥 Исходный файл: {input_file}")
    print(f"📤 Результат сохранен: {output_file}")


def main():
    """Главная функция с обработкой аргументов командной строки."""
    if len(sys.argv) < 2:
        print("Использование: python processing_EN_file_po.py <input_file> [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else str(Path(input_file).parent / f"_{Path(input_file).name}")

    if not Path(input_file).exists():
        print(f"❌ Ошибка: файл {input_file} не найден!")
        sys.exit(1)

    process_po_file(input_file, output_file)


if __name__ == "__main__":
    main()
