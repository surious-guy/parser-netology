import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from fake_useragent import UserAgent
from multiprocessing import Pool
from tqdm import tqdm
from selenium.common.exceptions import WebDriverException
import time
import pickle
import json
import os

from index import download_video

ua = UserAgent()
user_agent = ua.random

headers = {
    "accept": "*/*",
    "user-agent": user_agent
}


def initialization_driver():
    """Инициализация сессии"""
    service = Service(executable_path=os.getcwd() + f"\\geckodriver.exe")
    options = webdriver.FirefoxOptions()
    options.set_preference("general.useragent.override", user_agent)
    options.headless = False  # Включение фонового режима
    options.add_argument("--headless=old")
    return webdriver.Firefox(
        options=options,
        service=service
    )


def get_cookies(driver, url):
    """Получение куки"""
    try:
        driver.get(url=url)
        time.sleep(5)
        email_input = driver.find_element_by_name("email")
        email_input.clear()
        email_input.send_keys("daniil_vasilenko757@mail.ru")
        time.sleep(5)
        password_input = driver.find_element_by_name("password")
        password_input.send_keys("Wither757!")
        password_input.send_keys(Keys.ENTER)
        time.sleep(20)
        pickle.dump(driver.get_cookies(), open("cookies", "wb"))
        print("Cookies записаны в файл cookies")
    except Exception as ex:
        print(ex)


def authorized_session(driver, url):
    """Получение авторизованной сессии"""
    try:
        driver.get(url=url)
        for cookie in pickle.load(open(os.getcwd() + "\\cookies", "rb")):
            driver.add_cookie(cookie)
        driver.refresh()
    except Exception as ex:
        print(ex)


def get_links(url, name_class_icon_video, name_class_icon_webinar, name_class_block, name_class_title_video):
    """Получение ссылок на вебинары/записанные видео на сайте Нетологии

    Keyword arguments:
    driver -- webdriver.Firefox
    url -- ссылка на модуль
    name_class_icon -- значение атрибута class тега div для иконки видео
    name_class_icon_presentation -- значение атрибута class тега div для иконки презентации
    name_class_block -- значение атрибута class тега div для блока с видео
    name_class_title_video -- значение атрибута class тега div для наименования видео
    """

    data = []
    try:
        xpath_block = f'//div[@class="{name_class_block}"]'
        xpath_video = f'//div[@class="{name_class_icon_video}"]//ancestor::a'
        xpath_webinar = f'//div[@class="{name_class_icon_webinar}"]//ancestor::a'
        xpath_name_video = f'.//div[@class="{name_class_title_video}"]'
        driver = initialization_driver()
        authorized_session(driver, url)
        driver.implicitly_wait(60)
        list_elements = driver.find_elements(By.XPATH, xpath_block)
        for element in tqdm(list_elements, desc="Click blocks...", unit="process"):
            element.click()
        elements_video = driver.find_elements(By.XPATH, xpath_video) + driver.find_elements(By.XPATH, xpath_webinar)
        for i in range(0, len(elements_video) - 1):
            name = elements_video[i].find_element(By.XPATH, xpath_name_video).text
            url = elements_video[i].get_attribute("href")
            data.append(
                {
                    "name": replace_path(name),
                    "url": url,
                }
            )
    except Exception as ex:
        print(ex)
    finally:
        return data
        driver.close()
        driver.quit()


# region Работа с файлами


def write_to_json(data, name):
    with open(f"{name}.json", "w") as file:
        json.dump(data, file, indent=4)


def read_of_json(name, key):
    """Получение списка со ссылками на вебинары на сайте Нетологии"""
    with open(f"{name}.json", "r") as file:
        data = json.load(file)
    return [item[key] for item in data if isinstance(item, dict)]


def convert_json_to_array(name):
    """Получение списка со ссылками на вебинары на сайте Нетологии"""
    with open(f"{name}.json", "r") as file:
        data = json.load(file)
    return [(item['url'], item['name']) for item in data if isinstance(item, dict)]


def convert_json_to_dict(name):
    """Получение списка со ссылками на вебинары на сайте Нетологии"""
    with open(f"{name}.json", "r") as file:
        data = json.load(file)
    return [{'url': item['url'], 'name': item['name']} for item in data if isinstance(item, dict)]


def write_to_txt(name_dict, filename, list_name):
    """Запись в файл прямой ссылки на видео"""
    with open(f"{name_dict}\\{filename}.txt", "w", encoding="UTF-8") as file:
        print(*list_name, file=file, sep="\n")


# endregion

def get_id_video(*args):
    url, name = args[0]
    xpath_video = 'iframe[src]'
    driver = initialization_driver()
    authorized_session(driver, url)
    driver.implicitly_wait(60)
    try:
        url: str = driver.find_element(By.CSS_SELECTOR, xpath_video).get_attribute('src')
        return {
            'url': url.split('?', 1)[0].split('/')[-1],
            'name': name
        }
    except WebDriverException as ex:
        print(ex)
        print(url)
    finally:
        driver.close()
        driver.quit()


def extract_and_save_links(url):
    name_class_icon_video = "src-components-lms-shared-LessonItemIcon--root--ARxp7 src-components-lms-shared-LessonItemIcon--video--oH0yw"
    name_class_icon_webinar = "src-components-lms-shared-LessonItemIcon--root--ARxp7 src-components-lms-shared-LessonItemIcon--webinar--xpsv0"
    name_class_block = "src-features-lms-lessons-components-Lessons-components-Lesson--root--_9T5o"
    name_class_title_video = "src-features-lms-lessons-components-Lessons-components-Lesson-components-LessonItems--itemTitle--qBEs_"
    links_to_webinar = get_links(
        url,
        name_class_icon_video,
        name_class_icon_webinar,
        name_class_block,
        name_class_title_video
    )
    write_to_json(links_to_webinar, "name_and_url")


def process_links_from_file():
    list_url_video = convert_json_to_array("name_and_url")
    with Pool(10) as p:
        video_ids = list(
            tqdm(
                p.imap(get_id_video, list_url_video),
                desc="Парсинг id на видео",
                total=len(list_url_video),
                unit="process"
            )
        )
    write_to_json(video_ids, 'filename_video_with_id')


def replace_path(name):
    pattern = r"[^\w\d]+"
    replacement = "_"
    return re.sub(pattern, replacement, name)


def main():
    # extract_and_save_links("https://netology.ru/profile/program/ajs-46/schedule")
    # process_links_from_file()
    for item in convert_json_to_dict('filename_video_with_id'):
        download_video(item['url'], replace_path(item['name']))


if __name__ == "__main__":
    main()
