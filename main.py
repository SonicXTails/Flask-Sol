from web3 import Web3
from web3.middleware import geth_poa_middleware
from contract_info import abi, contract_address

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

contract = w3.eth.contract(address=contract_address, abi=abi)


class EstateAgency:
    estateType = {
        0: "House",
        1: "Flat",
        2: "Loft",
        3: "Dacha"
    }
    advertisementType = {
        0: "Opened",
        1: "Closed"
    }

def is_common_password(password):
    common_passwords = [
        "password",
        "123456",
        "qwerty",
        "abc123",
        "password1",
        "123456789",
        "12345678",
        "12345",
        "1234567",
        "1234567890",
        "letmein",
        "password123",
        "admin",
        "welcome",
        "monkey",
        "login",
        "!@#$%^&*",
        "password!",
        "passw0rd",
        "123123"
    ]
    return password in common_passwords

# Регистрация и авторизация
def login():
    public_key = input("Введите публичный ключ: ")
    password = input("Введите пароль: ")
    try:
        w3.geth.personal.unlock_account(public_key, password)
        print("Авторизация прошла успешно!")
        return public_key
    except Exception as e:
        print(f"Ошибка авторизации: {e}")
        return None

def register():
    password = input("Введите пароль: ")
    
    if is_common_password(password):
        print("Ошибка: Ваш пароль слишком распространенный. Пожалуйста, выберите более сложный пароль.")
        return

    # Проверки сложности пароля
    if len(password) < 12:
        print("Пароль должен содержать не менее 12 символов")
        return
    if not any(char.isupper() for char in password):
        print("Пароль должен содержать хотя бы одну заглавную букву")
        return
    if not any(char.islower() for char in password):
        print("Пароль должен содержать хотя бы одну строчную букву")
        return
    if not any(char.isdigit() for char in password):    
        print("Пароль должен содержать хотя бы одну цифру")
        return
    if not any(char in "!@#$%^&*()-_=+{}[];:'\";<>?,./`~" for char in password):
        print("Пароль должен содержать хотя бы один специальный символ")
        return

    # Все проверки пройдены, можно создать аккаунт
    try:
        account = w3.geth.personal.new_account(password)
        print(f"Публичный ключ вашего нового аккаунта: {account}")
        return account
    except Exception as e:
        print(f"Ошибка регистрации: {e}")
        return None

# Создание недвижимости
def createEstate(account):
    while True:
        addressEstate = input("Введите адрес недвижимости: ")
        if not addressEstate:
            print("Ошибка: адрес недвижимости не может быть пустым.")
            continue

        square = input("Введите площадь недвижимости: ")
        if not square.isdigit():
            print("Ошибка: площадь недвижимости должна быть числом.")
            continue

        print("Выберите тип недвижимости:")
        for i, esType in enumerate(EstateAgency.estateType.values()):
            print(f"{i+1}. {esType}")
        esType_choice = input("Введите номер выбранного типа недвижимости: ")
        if not esType_choice.isdigit() or int(esType_choice) < 1 or int(esType_choice) > 4:
            print("Ошибка: выберите корректный тип недвижимости.")
            continue

        esType = int(esType_choice) - 1
        try:
            tx_hash = contract.functions.createEstate(addressEstate, int(square), esType).transact({
                "from": account
            })
            print(f"Транзакция создания недвижимости отправлена: {tx_hash.hex()}")
            break 
        except Exception as e:
            print(f"Ошибка создания недвижимости: {e}")



# Создание объявления
def createAd(account):
    idEstate = int(input("Введите ID недвижимости, к которой относится объявление: "))
    price = int(input("Введите цену: "))
    try:
        tx_hash = contract.functions.createAd(idEstate, price).transact({
            "from": account
        })
        print(f"Транзакция создания объявления отправлена: {tx_hash.hex()}")
    except Exception as e:
        print(f"Ошибка создания объявления: {e}")

# Изменение статуса недвижимости
def updateEstateActive(account):
    idEstate = int(input("Введите ID недвижимости, чей статус вы хотите изменить: "))
    isActive = input("Введите 'true' для активации или 'false' для деактивации (изначально false): ").lower() == 'true'
    try:
        tx_hash = contract.functions.updateEstateActive(idEstate, isActive).transact({
            "from": account
        })
        print(f"Транзакция изменения статуса недвижимости отправлена: {tx_hash.hex()}")
    except Exception as e:
        print(f"Ошибка изменения статуса недвижимости: {e}")

# Изменение статуса объявления
def updateAdType(account):
    idAd = int(input("Введите ID объявления, чей статус вы хотите изменить: "))
    print("Выберите тип статуса объявления:")
    print("1. Открытое")
    print("2. Закрытое")
    adType_choice = int(input("Введите номер выбранного типа статуса объявления: "))
    adType = adType_choice - 1 
    try:
        tx_hash = contract.functions.updateAdType(idAd, adType).transact({
            "from": account
        })
        print(f"Транзакция изменения статуса объявления отправлена: {tx_hash.hex()}")
    except Exception as e:
        print(f"Ошибка изменения статуса объявления: {e}")


# Покупка недвижимости
def buyEstate(account):
    idAd = input("Введите ID объявления, по которому хотите купить недвижимость: ")
    if not idAd.isdigit():
        print("Ошибка: ID объявления должен быть числом.")
        return

    try:
        ads = contract.functions.getAd().call()
        if int(idAd) >= len(ads):
            print("Ошибка: выбранного объявления не существует.")
            return

        selected_ad = ads[int(idAd)] 
        price = selected_ad[0]

        tx_hash = contract.functions.buyEstate(int(idAd)).transact({
            "from": account,
            "value": price 
        })
        print(f"Транзакция покупки недвижимости отправлена: {tx_hash.hex()}")
    except Exception as e:
        print(f"Ошибка покупки недвижимости: {e}")


# Вывод средств
def withdraw(account):
    try:
        tx_hash = contract.functions.withdraw().transact({
            "from": account
        })
        print(f"Транзакция вывода средств отправлена: {tx_hash.hex()}")
    except Exception as e:
        print(f"Ошибка вывода средств: {e}")


# Получение различной информации
def getAvailableEstates():
    try:
        estates = contract.functions.getEstates().call()
        print("Доступные недвижимости:")
        for estate in estates:
            print(f"ID: {estate[5]}, Адрес: {estate[0]}, Площадь: {estate[1]}, Тип: {EstateAgency.estateType[estate[2]]}, Статус: {'Активна' if estate[4] else 'Неактивна'}")
    except Exception as e:
        print(f"Ошибка при получении информации о недвижимости: {e}")

def getCurrentAds():
    try:
        ads = contract.functions.getAd().call()
        print("Текущие открытые объявления о продаже недвижимости:")
        for ad in ads:
            print(f"Цена: {ad[0]}, ID недвижимости: {ad[1]}, Адрес владельца: {ad[2]}, Адрес покупателя: {ad[3]}, Дата: {ad[4]}, Тип объявления: {ad[5]}")
    except Exception as e:
        print(f"Ошибка при получении информации о текущих объявлениях: {e}")

def getContractBalance(account):
    try:
        balance = contract.functions.getBalance().call({
            "from": account
        })
        print(f"Баланс на смарт-контракте: {balance}")
    except Exception as e:
        print(f"Ошибка просмотра баланса: {e}")

def getAccountBalance(account):
    try:
        balance = w3.eth.get_balance(account)
        print(f"Баланс на аккаунте: {balance}")
    except Exception as e:
        print(f"Ошибка при получении баланса на аккаунте: {e}")


if __name__ == "__main__":
    account = ""
    is_auth = False
    while True:
        if not is_auth:
            choice = input("Выберите действие:\n1. Авторизация\n2. Регистрация\n3. Выход\n")
            if choice == "1":
                account = login()
                if account:
                    is_auth = True
            elif choice == "2":
                account = register()
                if account:
                    is_auth = True
            elif choice == "3":
                break
            else:
                print("Выберите корректный вариант.")
        elif is_auth:
            choice = input("Выберите действие:\n"
                           "1. Создать недвижимость\n"
                           "2. Создать объявление о продаже недвижимости\n"
                           "3. Изменить статус недвижимости\n"
                           "4. Изменить статус объявления\n"
                           "5. Купить недвижимость\n"
                           "6. Вывести средства\n"
                           "7. Получить информацию о доступных недвижимостях\n"
                           "8. Получить информацию о текущих объявлениях о продаже недвижимости\n"
                           "9. Получить баланс на смарт-контракте\n"
                           "10. Получить баланс на аккаунте\n"
                           "11. Выйти из системы\n\n")
            if choice == "1":
                createEstate(account)
            elif choice == "2":
                createAd(account)
            elif choice == "3":
                updateEstateActive(account)
            elif choice == "4":
                updateAdType(account)
            elif choice == "5":
                buyEstate(account)
            elif choice == "6":
                withdraw(account)
            elif choice == "7":
                getAvailableEstates()
            elif choice == "8":
                getCurrentAds()
            elif choice == "9":
                getContractBalance(account)
            elif choice == "10":
                getAccountBalance(account)
            elif choice == "11":
                is_auth = False
            else:
                print("Выберите корректный вариант.")