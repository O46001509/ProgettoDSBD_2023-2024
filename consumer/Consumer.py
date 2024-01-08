from kafka import KafkaConsumer
import time, json, requests

bootstrap_servers = 'kafka:9092'
topic_name = 'example-topic'

consumer = KafkaConsumer(topic_name, 
    bootstrap_servers=bootstrap_servers)#, 
    #group_id='my-group')#,
    #value_deserializer=json.loads,
    #auto_offset_reset="latest")

#consumer.subscribe(topic_name)

for message in consumer:
    print(f"Consumed: {message.value.decode('utf-8')}")

    url = f"https://api.telegram.org/bot6891484766:AAFPTKTsqt0RiynexY1bgc1Q0B73jFpEn-A/sendMessage?chat_id=659173906&text={message.value.decode('utf-8')}"

    requests.get(url).json() # this sends the message

    # with open('prova.txt', 'a') as file:
    #     file.write(message.value.decode('utf-8'))



# while(True):
#     data=next(consumer)
#     print(data)
#     print(data.value)

consumer.close()

