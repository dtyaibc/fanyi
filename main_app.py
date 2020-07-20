from flask import Flask, render_template, request, redirect, session
import pymongo
import hashlib
import datetime
import uuid
 #请开始你的表演，我先撤了啊 
# 创建Flask对象app
app = Flask(__name__)
# 设置密钥
app.secret_key = '833/dik902#d'

'''
    --------与任务本有关的路由--------

    /todo             访问“任务列表页面”，实现查询任务功能
    /todo/add         访问“添加任务页面”
    /add_check        处理添加任务表单，实现添加任务功能

'''
# 路由：访问“任务列表页面”，实现查询功能
@app.route('/todo')
def list_page():
    # 访问控制：如果没有登录，则重定向到登录页面
    username = session.get('username')
    if username == None:
        return redirect('/login')

    # 创建数据库查询条件
    condition = {}
    condition['owner'] = username

    # 1、获取提交的subject
    subject = request.args.get('subject')

    # 2、将subject添加到查询条件condition
    if subject != None and subject != '全部':
        condition['subject'] = subject

    # 在控制台输出条件
    print(condition)

    # 使用find_todo()函数查询符合条件的任务数据
    todo_list = find_todo(condition)

    # 使用查询到的任务列表渲染页面
    subject_options = ['全部', '语文', '数学', '英语', '编程']

    return render_template('list.html',
                           t_username=username,
                           t_todo_list=todo_list,
                           t_subject_options=subject_options,
                           t_subject=subject)

# 路由：返回“添加任务页面”
@app.route('/todo/add')
def todo_add():
    # 访问控制：如果没有登录，则重定向到登录页面
    username = session.get('username')
    if username == None:
        return redirect('/login')

    # 获取今天的日期字符串
    today = str_today()
    # 创建任务时的可选科目
    subjects = ['语文', '数学', '英语', '编程']
    return render_template('todo_add.html',
                           t_username=username,
                           t_subject_options=subjects,
                           t_date=today)



# 路由：获取添加任务表单提交的数据，实现添加任务功能
@app.route('/add_check', methods=['POST'])
def add_check():

    # 访问控制：pip uninstall如果没有登录，则重定向到登录页面
    username = session.get('username')
    if username == None:
        return redirect('/login')

    # 创建存储任务信息的字典
    todo = {}

    # 【提示1】获取表单提交的'subject'、'content'，并将获取到的值存入任务信息字典todo中
    todo["subject"] = request.form.get("subject")
    todo["content"] = request.form.get("content")
    # 【提示2】给任务信息字典todo中添加'_id'(唯一标识)，'state'(任务状态：unfinished)，'owner'(任务拥有者：用户名)，'date'(今天的日期)
    todo["_id"] = str(uuid.uuid1())
    todo["state"] = 'unfinished'             
    todo["owner"] = username
    todo["date"] = str_today()

    # 将存储任务信息的字典存入数据库
    insert_todo(todo)

    # 重定向到任务本主页
    return redirect('/todo')


'''
    --------与任务本有关的自定义函数--------

    insert_todo()      存储新的任务
    find_todo()        根据条件查询任务
    str_today()        获取今天的日期(字符串)

'''


# 函数：存储新的任务
def insert_todo(todo):
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db_todo = client['db_todo']
    c_todo = db_todo['todo']
    c_todo.insert_one(todo)


# 函数：根据条件查询任务
def find_todo(condition):
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db_todo = client['db_todo']
    c_todo = db_todo['todo']
    cursor = c_todo.find(condition)
    todo_list = []
    for item in cursor:
        todo_list.append(item)
    return todo_list


# 函数：获取今天的日期(字符串)
def str_today():
    # 获取今天的日期
    today = datetime.date.today()
    # 返回字符串格式的日期
    return str(today)



# ----------------与注册有关的路由-------------------

# 路由：访问“注册页面”
@app.route('/register')
def register():
    return render_template('register.html')


# 路由：处理注册表单，实现注册功能
@app.route('/register_check', methods=['POST'])
def register_check():
    username = request.form['username']
    password = request.form['password']

    # 将提交的注册用户名做为查询条件从数据库中查询数据
    user_list = find_user({'username': username})

    if len(user_list) == 0:
        # 将原密码进行加密，并返回加密后的密码
        pwd = encrypt(password)

        user = {'username': username, 'password': pwd}
        insert_user(user)

        return render_template('register.html', t_msg='注册成功')

    else:
        return render_template('register.html', t_username=username, t_msg='用户名已存在')


# ----------------与登录有关的路由-------------------

# 路由：返回“登录页面”（注意：这个路由的资源路径不要修改，否则会造成部署失败）
@app.route('/login')
def login():
    return render_template('login.html')


# 路由：处理登录表单，实现登录功能
@app.route('/login_check', methods=['POST'])
def login_check():
    username = request.form['username']
    password = request.form['password']

    # 将原密码进行加密，并返回加密后的密码
    pwd = encrypt(password)

    condition = {'username': username, 'password': pwd}
    user_list = find_user(condition)

    if len(user_list) == 1:
        session['username'] = username
        # 登录成功，重定向到“任务列表页面”
        return redirect('/todo')
    else:
        return render_template('login.html', t_error='用户名或密码错误')


# 路由：用户退出登录
@app.route('/logout')
def logout():
    # 删除session中的登录用户名
    session.pop('username')
    # 退出登录后，重定向到登录页面
    return redirect('/login')

# ----------------自定义函数：插入数据、查询数据、加密-------------------

# 使用MD5对密码进行加密
def encrypt(password):
    pwd = hashlib.md5(password.encode(encoding='UTF-8')).hexdigest()
    return pwd

# 函数: 将注册用户数据存入数据库
def insert_user(user):
    client = pymongo.MongoClient('mongodb://localhost:27017')
    db = client['db_user']
    collection = db['user']
    collection.insert_one(user)

# 函数：根据指定条件查找注册用户信息
def find_user(condition):
    client = pymongo.MongoClient('mongodb://localhost:27017')
    db = client['db_user']
    collection = db['user']
    res = collection.find(condition)
    user_list = []
    for item in res:
        user_list.append(item)
    return user_list




if __name__ == '__main__':
    app.run(port=5001)
