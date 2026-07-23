from filters import check_keywords, check_priority, process_message
from config import load_config

config = load_config()

print("Config keywords:", config['filters']['keywords'])
print("Config priority keywords:", config['filters']['priority_keywords'])

test_texts = [
    "Срочно ищу виллу в аренду!",
    "Хочу снять квартиру",
    "Продаю дом",
    "Ищу комнату, срочно"
]

for text in test_texts:
    print("\nTesting text:", text)
    print("check_keywords:", check_keywords(text, config['filters']['keywords']))
    print("check_priority:", check_priority(text, config['filters']['priority_keywords']))
    print("process_message:", process_message(text, config))
