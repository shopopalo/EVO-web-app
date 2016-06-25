import os
import random
import json
import sqlite3
from flask import Flask, request, g, redirect, url_for, render_template, Response

app = Flask(__name__)
app.config.from_object(__name__)

# загрузка дефолтного конфига для того что бы переопределить некоторые поля
app.config.update(
	dict(
		DATABASE=os.path.join(app.root_path, 'main.db'),
		SECRET_KEY='dev key',
		USERNAME='admin',
		PASSWORD='admin'
	)
)

def connect_db():
	'''
	соединение с БД
	'''
	connection = sqlite3.connect(app.config['DATABASE'])
	return connection

def get_db():
	'''
	Если в текущем контекте приложения нет соединения с БД под
	именем sqlite_db, тогда создаем новое соединение
	'''
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = connect_db()
	return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
	'''
	Если контекст приложения обрушится, то
	декоратор teardown_appcontext будет вызывать ф-цию close_db
	для закрытия соединения с БД
	'''
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()

def init_db():
	'''
	инициализация БД для текущего приложения;
	выполняется создание таблиц базы данных
	'''
	with app.app_context():
		db = get_db()
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()
		print('Database have been create')


@app.route('/compose_message', methods=['POST'])
def compose_message():
	welcome = ''
	# привидение имени "Карл" к "карл"
	name = request.json.lower()
	# соединяемся с БД
	db = get_db()
	try:
		# пытаемся добавить новое имя в БД
		curr = db.execute('insert into names (name) values (?)', [name])
		# сохранение изменений в БД
		db.commit()
		# получаем id только что добавленого имени
		name_id = curr.lastrowid

		# указание как будут отображатся данные из БД
		# в данном случае в виде списка [val1, val2, val3]
		db.row_factory = lambda cursor, row: row[0]

		try:
			# пытаемся получить первый неиспользованый эпитет; 0 означает false
			epitet_id = db.execute('select id from epitets where used=?', [0]).fetchall()[0]
			# указываем что епитет уже использован
			db.execute('update epitets set used=? where id=?', [1, epitet_id])
			db.commit()
		except IndexError:
			# определяем общее количество эпитетов
			count_epitets = len(db.execute('select id from epitets').fetchall())
			# если все эпитеты уже использованы
			# берем рандомное id эпитета
			random_id = random.randint(0,count_epitets-1)
			epitet_id = db.execute('select id from epitets').fetchall()[random_id]

		#db.execute('update epitets set used=? where id=?', [1, epitet_id])
		#db.commit()

		# добавляем к имени id эпитета
		db.execute('update names set epitet_id=? where id=?', [epitet_id, name_id])
		db.commit()

		# получаем эпитет
		epitet = db.execute('select epitet from epitets where id=?', [epitet_id]).fetchall()[0]
		# состовляем сообщение
		welcome = "Рад тебя видеть, {} {}!".format(epitet, name.capitalize())
	except sqlite3.IntegrityError:
		# если вызнано исключение, то имя уже существует в БД
		# получаем id эпитета для этого имени
		exists_name_epited_id = db.execute('select epitet_id from names where name=?', [name]).fetchall()[0][0]

		try:
			epitet = db.execute('select epitet from epitets where id=?', [exists_name_epited_id]).fetchall()[0][0]
		except IndexError:
			epitet = db.execute('select epitet from epitets where id=?', [exists_name_epited_id]).fetchall()

		welcome = "Рад тебя видеть снова, {} {}!".format(epitet, name.capitalize())
	return Response(
		json.dumps({'message': welcome}),
		mimetype='application/json',
		headers={
			'Cache-Control': 'no-cache',
			'Access-Control-Allow-Origin': '*'
		}
	)

@app.route('/add_ep', methods=['POST', 'GET'])
def add_epitet():
	if request.method == 'POST':
		db = get_db()
		db.execute('insert into epitets (epitet, used) values (?, ?)',
					[request.form['epitet'].lower(), 0])
		db.commit()
		return redirect(url_for('add_epitet'))
	elif request.method == 'GET':
		db = get_db()
		cursor = db.execute('select epitet from epitets')
		epitets = cursor.fetchall()
		return render_template("add_epitet.html", epitets=epitets)

@app.route('/', methods=['GET'])
def index():
	welcome = 'Welcome'
	return render_template("index.html", welcome=welcome)


if __name__=='__main__':
	#init_db()
	app.run(debug=True)