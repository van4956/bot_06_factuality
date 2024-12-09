import os
import datetime
from openai import OpenAI

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debug >>> ')

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

API_GPT = os.getenv('API_GPT')
# ic(API_GPT)

client = OpenAI(api_key=API_GPT)
# ic(client)

models = client.models.list()
# ic(models)

list_models = []

for model in models.data:
    if 'gpt' in model.id:
        # skip = ' ' * (30 - len(model.id))
        dt_object = datetime.datetime.fromtimestamp(model.created, tz=datetime.timezone.utc)
        time = dt_object.strftime('%H:%M')
        dt = dt_object.strftime('%Y-%m-%d')
        model = (dt, time, model.id, model.owned_by)
        list_models.append(model)
        # print(f"Created: {dt} {time},   Model: {model.id},{skip} Owned by: {model.owned_by}")

list_models = sorted(list_models, reverse=True)[:8]
ic(list_models)



print('='*100)

content = ("Ты полезный помощник. Твой тон должен быть официальным. Ответы должны быть краткими и понятными. "
            "Дай ответ без использования символов форматирования текста Markdown, таких как решетки или звездочки. "
            "Ответы должены быть в формате простого текста.")

print(content)

response = client.chat.completions.create(
                        model="gpt-4o",
                        # response_format={ "type": "json_object" },
                        messages=[
                            {"role": "system", "content": content},
                            {"role": "user", "content": "Кто выиграл президенские выборы в России в 2024 году?"}
                        ]
                        )

print('='*100)
print(response.choices[0].message.content)
print('='*100)