from flask import Flask, render_template, request, redirect, url_for, session, flash
from web3 import Web3
from web3.middleware import geth_poa_middleware
from contract_info import abi, contract_address

app = Flask(__name__)
app.secret_key = 'your_secret_key'
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

contract = w3.eth.contract(address=contract_address, abi=abi)

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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        public_key = request.form['public_key']
        password = request.form['password']
        try:
            w3.geth.personal.unlock_account(public_key, password)
            session['account'] = public_key  # Сохраняем аккаунт в сессии
            return redirect(url_for('dashboard'))
        except Exception as e:
            error = "Ошибка авторизации: неправильный публичный ключ или пароль"
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form['password']
        
        if is_common_password(password):
            error = "Ошибка: Ваш пароль слишком распространенный. Пожалуйста, выберите более сложный пароль."
            return render_template('register.html', error=error)
        if len(password) < 12:
            error = "Пароль должен содержать не менее 12 символов"
            return render_template('register.html', error=error)
        if not any(char.isupper() for char in password):
            error = "Пароль должен содержать хотя бы одну заглавную букву"
            return render_template('register.html', error=error)
        if not any(char.islower() for char in password):
            error = "Пароль должен содержать хотя бы одну строчную букву"
            return render_template('register.html', error=error)
        if not any(char.isdigit() for char in password):    
            error = "Пароль должен содержать хотя бы одну цифру"
            return render_template('register.html', error=error)
        if not any(char in "!@#$%^&*()-_=+{}[];:'\";<>?,./`~" for char in password):
            error = "Пароль должен содержать хотя бы один специальный символ"
            return render_template('register.html', error=error)
        try:
            account = w3.eth.account.create(password)
            session['account'] = account.address 
            return redirect(url_for('register_success', account=account.address)) 
        except Exception as e:
            flash("Ошибка регистрации: неправильный пароль", "error")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/register_success/<account>')
def register_success(account):
    return render_template('register_success.html', account=account)

@app.route('/dashboard')
def dashboard():
    account = session.get('account')
    if account:
        shortened_account = account[-5:]  
    else:
        shortened_account = 'Гость'
    return render_template('dashboard.html', shortened_account=shortened_account)

@app.route('/logout')
def logout():
    session.pop('account', None)
    return redirect(url_for('index'))

from flask import request, redirect, url_for, render_template, flash

@app.route('/create-estate', methods=['GET', 'POST'])
def create_estate():
    error = None
    
    if request.method == 'POST':
        address = request.form['address']
        square = request.form['square']
        estate_type = request.form['estate_type']
        
        try:
            account = session.get('account')
            if not account:
                flash("Пользователь не аутентифицирован", "error")
                return redirect(url_for('login'))
            existing_estates = contract.functions.getEstates().call()
            for estate in existing_estates:
                if estate[0] == address and estate[1] == int(square) and estate[2] == int(estate_type):
                    error = "Нельзя создать недвижимость с такими же данными, она уже существует"
                    return render_template('create_estate.html', error=error)

            tx_hash = contract.functions.createEstate(address, int(square), int(estate_type)).transact({
                "from": account
            })
            print(f"Транзакция создания недвижимости отправлена: {tx_hash.hex()}")
            return redirect(url_for('dashboard'))
        except Exception as e:
            error = f"Ошибка создания недвижимости: {e}"
            return render_template('create_estate.html', error=error)

    return render_template('create_estate.html', error=error)

@app.route('/available-estates')
def available_estates():
    try:
        estates = contract.functions.getEstates().call()
        return render_template('available_estates.html', estates=estates)
    except Exception as e:
        error_message = f"Ошибка при получении списка доступных недвижимостей: {e}"
        flash(error_message, "error")
        return redirect(url_for('dashboard'))
    

@app.route('/update-estate', methods=['GET', 'POST'])
def update_estate():
    if request.method == 'POST':
        estate_id = int(request.form['estate_id'])
        is_active = 'is_active' in request.form
        try:
            account = session.get('account')
            if not account:
                flash("Пользователь не аутентифицирован", "error")
                return redirect(url_for('login'))

            print(f"estate_id: {estate_id}, is_active: {is_active}")

            tx_hash = contract.functions.updateEstateActive(estate_id, is_active).transact({
                "from": account
            })
        except Exception as e:
            flash(f"Ошибка изменения статуса недвижимости: {e}", "error")
        return redirect(url_for('dashboard'))
    
    return render_template('update_estate.html')

@app.route('/create-ad', methods=['GET', 'POST'])
def create_ad():
    if request.method == 'POST':
        account = session.get('account')
        if not account:
            flash("Пользователь не аутентифицирован", "error")
            return redirect(url_for('login'))
        
        id_estate = int(request.form['estate_id'])
        price = int(request.form['price'])
        
        estates = contract.functions.getEstates().call()

        estate = estates[id_estate - 1]
        if not estate[4]:
            error = "Данная недвижимость не активна"
            return render_template('create_ad.html', error=error)
        if price <= 0:
            error = "Вы ввели цену меньше или равную 0"
            return render_template('create_ad.html', error=error)
        try:
            tx_hash = contract.functions.createAd(id_estate, price).transact({
                "from": account
            })
            return redirect(url_for('dashboard'))
        except Exception as e:
            error = f"Ошибка создания объявления: Вы ввели неактивную недвижимость"
            return render_template('create_ad.html', error=error)
    else:
        return render_template('create_ad.html')

@app.route('/current-ads')
def current_ads():
    try:
        ads = contract.functions.getAd().call()
        return render_template('current_ads.html', ads=ads)
    except Exception as e:
        flash(f"Ошибка при получении информации о текущих объявлениях: {e}", "error")
        return redirect(url_for('dashboard'))


@app.route('/update-ad', methods=['GET', 'POST'])
def update_ad():
    if request.method == 'POST':
        id_ad = int(request.form['ad_id'])
        is_open = 'is_open' in request.form
        is_open_value = 1 if is_open else 0
        try:
            account = session.get('account')
            if not account:
                flash("Пользователь не аутентифицирован", "error")
                return redirect(url_for('login'))

            tx_hash = contract.functions.updateAdType(id_ad, is_open_value).transact({
                "from": account
            })
        except Exception as e:
            flash(f"Ошибка изменения статуса объявления: {e}", "error")
        return redirect(url_for('dashboard'))
    
    return render_template('update_ad.html')

def get_contract_balance(account):
    try:
        balance = contract.functions.getBalance().call({
            "from": account
        })
        return balance
    except Exception as e:
        return f"Ошибка просмотра баланса на смарт-контракте: {e}"

def get_account_balance(account):
    try:
        balance = w3.eth.get_balance(account)
        return balance
    except Exception as e:
        return f"Ошибка при получении баланса на аккаунте: {e}"


@app.route('/contract-balance')
def contract_balance():
    account = session.get('account')  
    if not account:
        flash("Пользователь не аутентифицирован", "error")
        return redirect(url_for('login'))

    contract_balance = get_contract_balance(account)  
    return render_template('contract_balance.html', contract_balance=contract_balance)

@app.route('/account-balance')
def account_balance():
    account = session.get('account')  
    if not account:
        flash("Пользователь не аутентифицирован", "error")
        return redirect(url_for('login'))

    account_balance = get_account_balance(account)
    return render_template('account_balance.html', account_balance=account_balance)


@app.route('/buy-estate', methods=['GET', 'POST'])
def buy_estate():
    if request.method == 'POST':
        account = session.get('account')
        
        if not account:
            flash("Пользователь не аутентифицирован", "error")
            return redirect(url_for('login'))
        
        id_ad = request.form['ad_id']
        
        if not id_ad.isdigit():
            flash("Ошибка: ID объявления должен быть числом.", "error")
            return redirect(url_for('buy_estate'))

        try:
            id_ad = int(id_ad)
            ads = contract.functions.getAd().call()
            
            if id_ad >= len(ads):
                flash("Ошибка: выбранного объявления не существует.", "error")
                return redirect(url_for('buy_estate'))
            
            ad = ads[id_ad]
            price = ad[0]
            ad_owner = ad[2]
            buyer = ad[3]
            
            if buyer != '0x0000000000000000000000000000000000000000':
                flash("Ошибка: Недвижимость уже продана.", "error")
                return redirect(url_for('buy_estate'))
            
            if account == ad_owner:
                flash("Ошибка: Вы не можете купить свою собственность.", "error")
                return redirect(url_for('buy_estate'))
            
            account_balance = w3.eth.get_balance(account)
            if account_balance < price:
                flash("Ошибка: Недостаточно средств на аккаунте.", "error")
                return redirect(url_for('buy_estate'))

            tx_hash = contract.functions.buyEstate(id_ad).transact({
                "from": account,
                "value": price
            })
            flash(f"Транзакция покупки недвижимости отправлена: {tx_hash.hex()}", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"Ошибка покупки недвижимости: {e}", "error")
            return redirect(url_for('buy_estate'))
    return render_template('buy_estate.html')


@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        account = session.get('account')
        if not account:
            flash("Пользователь не аутентифицирован", "error")
            return redirect(url_for('login'))
        
        try:
            tx_hash = contract.functions.withdraw().transact({
                "from": account
            })
            flash("Транзакция вывода средств отправлена", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"Ошибка вывода средств: {e}", "error")
            return redirect(url_for('dashboard'))
    else:
        return render_template('withdraw.html')


if __name__ == '__main__':
    app.run(debug=True)