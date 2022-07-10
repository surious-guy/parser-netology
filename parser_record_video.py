from urllib.error import HTTPError
from urllib.request import urlopen

import requests
from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from multiprocessing import Pool
from tqdm import tqdm
from selenium.common.exceptions import WebDriverException
import time
import pickle
import json
import os

ua = UserAgent()
user_agent = ua.random

headers = {
    "accept": "*/*",
    "user-agent": user_agent
}


def initialization_driver():
    """Инициализация сессии"""
    options = webdriver.FirefoxOptions()
    options.set_preference("general.useragent.override", user_agent)
    options.headless = False  # Включение фонового режима
    return webdriver.Firefox(
        executable_path=os.getcwd() + f"\\geckodriver.exe",
        options=options)


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


def get_links(driver, url, name_class_icon, name_class_icon_presentation, name_class_block, name_class_title_video):
    """Получение ссылок на вебинары/записанные видео на сайте Нетологии

    Keyword arguments:
    driver -- webdriver.Firefox
    url -- ссылка на модуль
    name_class_icon -- значение атрибута class тега div для иконки видео
    name_class_icon_presentation -- значение атрибута class тега div для иконки презентации
    name_class_block -- значение атрибута class тега div для блока с видео
    name_class_title_video -- значение атрибута class тега div для наименования видео
    """
    try:
        xpath_block = f'//div[@class="{name_class_block}"]'
        xpath_video = f'//div[@class="{name_class_icon}"]//ancestor::a'
        xpath_presentation = f'//div[@class="{name_class_icon_presentation}"]//ancestor::a'
        xpath_name_video = f'.//div[@class="{name_class_title_video}"]'
        data = []
        authorized_session(driver, url)
        list_elements = driver.find_elements(By.XPATH, xpath_block)
        for element in tqdm(list_elements, desc="Click blocks...", unit="process"):
            element.click()
        elements_video = driver.find_elements(By.XPATH, xpath_video)
        elements_presentation = driver.find_elements(By.XPATH, xpath_presentation)
        for i in range(0, len(elements_video)-1):
            name = elements_video[i].find_element(By.XPATH, xpath_name_video).text
            url = elements_video[i].get_attribute("href")
            url_presentation = elements_presentation[i].find_element(By.XPATH, xpath_presentation).get_attribute("href")
            data.append(
                {
                    "name": name,
                    "url": url,
                    "url_presentation": url_presentation
                }
            )
        # for item in tqdm(elements_video, desc="Parsing links...", unit="process"):
        #     name = item.find_element(By.XPATH, xpath_name_video).text
        #     url = item.get_attribute("href")
        #     url_presentation = item.find_element(By.XPATH, xpath_presentation).get_attribute("href")
        #     data.append(
        #         {
        #             "name": name,
        #             "url": url,
        #             "url_presentation": url_presentation
        #         }
        #     )
        return data
    except Exception as ex:
        print(ex)
    finally:
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


def write_to_txt(name_dict, filename, list_name):
    """Запись в файл прямой ссылки на видео"""
    with open(f"{name_dict}\\{filename}.txt", "w", encoding="UTF-8") as file:
        print(*list_name, file=file, sep="\n")


# endregion


def get_url_video(url):
    """Получение прямой ссылки на видео и аудио с вебинара

    Keyword arguments:
    url -- ссылка на вебинар/записанное видео
    """
    pats = ("1080p.mp4", "720p.mp4", "480p.mp4", "360p.mp4")
    driver = initialization_driver()
    authorized_session(driver, url)
    driver.implicitly_wait(60)
    pat_audio = "audio_0.mp4"
    video_url, audio_url = "", ""
    try:
        for pat in pats:
            try:
                video_url = driver.wait_for_request(pat).url
                audio_url = driver.wait_for_request(pat_audio).url
            except WebDriverException:
                continue
    except WebDriverException as ex:
        print(ex)
        print(url)
    finally:
        driver.close()
        driver.quit()
        return [video_url, audio_url]


def get_url_iframe(url):
    """Получение прямой ссылки на видео и аудио с вебинара

        Keyword arguments:
        url -- ссылка на вебинар/записанное видео
        """
    pats = ("1080p", "720p", "480p", "360p")
    driver = initialization_driver()
    authorized_session(driver, url)
    driver.implicitly_wait(60)
    xpath_iframe = './/div[@class="src-components-common-KinescopePlayer2--iframeWrapper--GJ0Ou"]/iframe'
    url_kinescope = driver.find_element(By.XPATH, xpath_iframe).get_attribute("src").split("?", 1)[0]
    video_url = ""
    try:
        for pat in pats:
            try:
                video_url = url_kinescope + pat
                response = urlopen(video_url)
                if response.getcode() == 200:
                    return video_url
            except HTTPError:
                continue
    except WebDriverException as ex:
        print(ex)
        print(url)
    finally:
        driver.close()
        driver.quit()
        return video_url


def get_url_presentation(url):
    """Получение прямой ссылки на презентацию с вебинара

    Keyword arguments:
    url -- ссылка на презентацию
    """
    driver = initialization_driver()
    authorized_session(driver, url)
    driver.implicitly_wait(60)
    xpath_download = f'//a[@class="src-components-common-PdfViewer--download--z4lsW"]'
    try:
        url_presentation = driver.find_element(By.XPATH, xpath_download).get_attribute("href")
        return url_presentation
    except WebDriverException as ex:
        print(ex)
        print(url)
        return ""
    finally:
        driver.close()
        driver.quit()


def replace_path(name):
    symbols = (".", ",", "-", "\n", "'", "(", ")", '"', ":", "?")
    for i in symbols:
        name = name.replace(i, "_")
    return name


def main():
    # url модуля для парсера
    url = "https://netology.ru/profile/program/and-pdc-1/schedule"
    driver = initialization_driver()
    driver.implicitly_wait(20)
    directory = "Основы программирования"
    # name_class_icon_video = "src-components-lms-shared-LessonItemIcon--root--ARxp7 src-components-lms-shared-LessonItemIcon--video--oH0yw"
    name_class_icon_webinar = "src-components-lms-shared-LessonItemIcon--root--ARxp7 src-components-lms-shared-LessonItemIcon--webinar--xpsv0"
    name_class_icon_presentation = "src-components-lms-shared-LessonItemIcon--root--ARxp7 src-components-lms-shared-LessonItemIcon--attachment--BG6hr"
    name_class_block = "src-features-lms-lessons-components-Lessons-components-Lesson--root--_9T5o"
    name_class_title_video = "src-features-lms-lessons-components-Lessons-components-Lesson-components-LessonItems--itemTitle--qBEs_"
    links_to_webinar = get_links(
        driver,
        url,
        name_class_icon_webinar,
        name_class_icon_presentation,
        name_class_block,
        name_class_title_video
    )
    print(links_to_webinar)
    write_to_json(links_to_webinar, "name_and_url")

    list_name = read_of_json("name_and_url", "name")
    list_url_video = read_of_json("name_and_url", "url")
    list_url_presentation = read_of_json("name_and_url", "url_presentation")
    # with Pool(10) as p:
    #     list_url_video = list(tqdm(p.imap(get_url_video, list_url_video),
    #                                desc="Парсинг ссылок на видео",
    #                                total=len(list_url_video),
    #                                unit="process"))

    # print(list_url_video)
    # with Pool(10) as p:
    #     list_url_video = list(tqdm(p.imap(get_url_iframe, list_url_video),
    #                                desc="Парсинг ссылок на видео",
    #                                total=len(list_url_video),
    #                                unit="process"))
    # for i in range(len(list_url_video)):
    #     print(list_url_video[i])

    print(list_url_presentation)
    with Pool(10) as p:
        list_url_presentation = list(tqdm(p.imap(get_url_presentation, list_url_presentation),
                                          desc="Парсинг ссылок на презентации",
                                          total=len(list_url_presentation),
                                          unit="process"))
    print(list_url_presentation)

    # for i in range(len(list_url_video)):
    #     list_url_video[i].append(list_url_presentation[i])
    # list_name_replace = list(map(replace_path, list_name))
    # print(list_name_replace)
    # print(list_url_video)
    # for i in range(len(list_url_video)):
    #     write_to_txt(directory, str(i + 1) + ". " + list_name_replace[i], list_url_video[i])


if __name__ == "__main__":
    main()
