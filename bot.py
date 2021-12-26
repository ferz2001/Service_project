import requests
import os

from dotenv import load_dotenv

import time
from selenium import webdriver
import vk_api
import telebot as tg
from telebot import types
import httplib2
import googleapiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

LOGIN_WEB_SITE = os.getenv('LOGIN_WEB_SITE')
PASSWORD_WEB_SITE = os.getenv('PASSWORD_WEB_SITE')
CHAT_ID = os.getenv('CHAT_ID')
TOKEN = os.getenv('TOKEN')
token='e1c8c9878839fa28799e43b576b68b93881522ff95bf7406d80d294e7f3e398c05340958f908dd97fca2d'

bot = tg.TeleBot(TOKEN)

data = []
src_data=[]
def add_to_vk(data, src_data):
    photo_ids=[]
    vk_session = vk_api.VkApi(token=token)
    session_api = vk_session.get_api()
    photo_url = session_api.photos.getMarketUploadServer(group_id=195760904,
                                                         main_photo=1
                                                         )['upload_url']
    for src in src_data:
        files = {
            'file': (src, open(src, 'rb')),
        }
        response = requests.post(photo_url, files=files).json()
        photo_id = session_api.photos.saveMarketPhoto(group_id=195760904,
                                                      photo=response['photo'],
                                                      server=response['server'],
                                                      crop_data=response['crop_data'],
                                                      crop_hash=response['crop_hash'],
                                                      hash=response['hash'])[0]['id']
        photo_ids.append(photo_id)
    session_api.market.add(owner_id=-195760904,
                           name=data[0],
                           description=data[1],
                           category_id=404,
                           price=data[2],
                           access_token=token,
                           main_photo_id=photo_ids[0],
                           photo_ids=photo_ids)
    photo_ids.clear()

def add_to_excel(data):
    CREDENTIALS_FILES = os.getcwd() + '\\' + 'sacc1.json'
    sheet_id = '1mDMvd6Dqj4b8N5b88A4yHDK3Sc4u9gWuqCrIRHm1a54'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILES,
        'https://www.googleapis.com/auth/spreadsheets'
    )
    httpAuth = credentials.authorize(httplib2.Http())
    service = googleapiclient.discovery.build('sheets', 'v4', http = httpAuth)
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="Лист1!A1",
        valueInputOption="RAW",
        body={'values': [[data[0], data[1], data[2]]]}
    ).execute()

def add_to_website(data, src_data):
    driver = webdriver.Chrome()
    driver.get('https://bmw.etk.club/manager')
    username_input = driver.find_element_by_id("inputEmail")
    username_input.clear()
    username_input.send_keys(LOGIN_WEB_SITE)
    password_input = driver.find_element_by_id("inputPassword")
    password_input.clear()
    password_input.send_keys(PASSWORD_WEB_SITE)
    driver.find_element_by_name("submit").click()
    driver.get('https://bmw.etk.club/manager')
    driver.find_element_by_link_text("Добавить").click()
    time.sleep(1)
    number_input=driver.find_element_by_id("number_add")
    number_input.send_keys(data[1])
    count_input = driver.find_element_by_id("costt")
    count_input.send_keys(data[2])
    text_input = driver.find_element_by_id("text")
    text_input.send_keys(data[0])
    driver.find_elements_by_name("submit")[0].click()
    time.sleep(1)
    driver.find_element_by_link_text('Добавить фото').click()
    time.sleep(1)
    driver.switch_to.window(driver.window_handles[1])
    time.sleep(0.5)
    for src in src_data:
        driver.find_element_by_xpath("//input[@type='file']").send_keys(src)
        time.sleep(0.2)
    driver.find_element_by_xpath("//button[@type='submit']").click()
    time.sleep(1)
    driver.close()
    driver.quit()


@bot.message_handler(commands=['start'])
def wake_up(message):
    name = message.chat.first_name
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item = types.KeyboardButton("Добавить деталь")
    button.add(item)
    bot.send_message(message.chat.id,
                     f'Привет, {name}.Нажмите кнопку, если хотите добавить деталь.',
                     reply_markup=button)


@bot.message_handler(content_types=['text'])
def main(message):
    if message.chat.type == 'private':
        if message.text == 'Добавить деталь':
            button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item = types.KeyboardButton("Отменить")
            button.add(item)
            send = bot.send_message(message.chat.id, "Введите название детали", reply_markup=button)
            bot.register_next_step_handler(send, handle_name)
        elif message.text == 'Нет':
            name = message.chat.first_name
            button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item = types.KeyboardButton("Добавить деталь")
            button.add(item)
            bot.send_message(message.chat.id,
                            f'Хорошо, {name}. Жду команды...',
                            reply_markup=button)
        elif message.text == 'Да':
            send = bot.send_message(message.chat.id, "Введите название детали")
            bot.register_next_step_handler(send, handle_name)
        elif message.text == 'Загрузить':
            add_to_vk(data=data, src_data=src_data)
            add_to_excel(data=data)
            add_to_website(data=data, src_data=src_data)
            for src in src_data:
                os.remove(src)
            button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1 = types.KeyboardButton("Да")
            item2 = types.KeyboardButton("Нет")
            button.add(item1, item2)
            bot.send_message(message.chat.id,
                            'Детали загружены на все сервисы! Хотите ещё добавить деталь?',
                            reply_markup=button)
            src_data.clear()
            data.clear()

def close(message):
    name = message.chat.first_name
    data.clear()
    src_data.clear()
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item = types.KeyboardButton("Добавить деталь")
    button.add(item)
    bot.send_message(message.chat.id, f'Хорошо, {name}. Жду команды...', reply_markup=button)

def handle_name(message):
    if message.text.lower() == 'отменить':
        close(message)
        return
    data.append(message.text)
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item = types.KeyboardButton("Отменить")
    button.add(item)
    send = bot.send_message(message.chat.id, "Введите номер детали (минимум 10 символов)", reply_markup=button)
    bot.register_next_step_handler(send, handle_number)
    
      
def handle_number(message):
    if message.text.lower() == 'отменить':
        close(message)
        return
    data.append(message.text)
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item = types.KeyboardButton("Отменить")
    button.add(item)
    send = bot.send_message(message.chat.id, "Введите цену детали", reply_markup=button)
    bot.register_next_step_handler(send, handle_price)
    

def handle_price(message):
    if message.text.lower() == 'отменить':
        close(message)
        return
    data.append(message.text)
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item = types.KeyboardButton("Отменить")
    button.add(item)
    send = bot.send_message(message.chat.id, "Отправьте главную фотографию детали ", reply_markup=button)
    bot.register_next_step_handler(send, handle_main_photo)
    


def handle_main_photo(message):
    if message.text == 'Отменить':
        close(message)
        return
    try:
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = os.getcwd() + '\\' + message.photo[1].file_id + '.jpg'
        src_data.append(src)
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
    except Exception as e:
        bot.reply_to(message,e )
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = types.KeyboardButton("Загрузить")
    item2 = types.KeyboardButton("Отменить")
    button.add(item1, item2)
    send = bot.send_message(message.chat.id, "Отправьте дополнительные фотографии детали, и нажмите Загрузить, чтобы отправить данные на обработку", reply_markup=button)
    bot.register_next_step_handler(send, handle_next_photos)
    
    

@bot.message_handler(content_types=['photo'])
def handle_next_photos(message):
    if message.text == 'Отменить':
        close(message)
        return
    try:
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = os.getcwd() + '\\' + message.photo[1].file_id + '.jpg'
        src_data.append(src)
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
    except Exception as e:
        bot.reply_to(message, e)
    


bot.polling(none_stop=True)

    