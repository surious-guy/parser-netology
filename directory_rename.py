import os


def main():
    path = "D:\\Курсы по программированию\\Веб-разработчик\\1. HTML-верстка с нуля до первого макета\\3. Всплывающие и flex-элементы\\3.2. Позиционирование flex-элементов\\"
    list_dict_path = os.listdir(path)
    i = 0
    for item in list_dict_path:
        i += 1
        os.rename(path + item, path + str(i) + "_" + item.split("_", 1)[1])


if __name__ == "__main__":
    main()
