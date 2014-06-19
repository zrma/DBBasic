# sudo ipfw add 100 fwd 127.0.0.1,8080 tcp from any to any 80 in
# sudo ipfw flush

from flask import Flask, url_for, session, escape, request, redirect
from flask import render_template

from sqlalchemy import Column, Integer, String, text, bindparam, outparam
from flask.ext.sqlalchemy import SQLAlchemy

import datetime
import hashlib
import string, random

dbhost = 'win.nhnnext.net'
dbuser = 'db_user'
dbpass = '1234'
dbname = 'mydb'
DB_URI = 'mysql+pymysql://' + dbuser + ':' + dbpass + '@' + dbhost + '/' +dbname


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI

db = SQLAlchemy(app)

@app.route('/wiki/<string:input_uri>')
def wiki(input_uri):
	output = ''
	
	if 'username' in session:
		output = output + '<a href = "/logout?request_uri=' + input_uri + '">Log Out</a>&nbsp;&nbsp;&nbsp;&nbsp;'
		output = output + 'You signed in as ' + session['username'][1] + '&nbsp;&nbsp;'
		
		if session['username'][2] == 'admin':
			output = output + '[admin]<br><br><br>'
		else:
			output = output + '[member]<br><br><br>'
	else:
		output = output + '<a href = "/login?request_uri=' + input_uri + '">Login</a>&nbsp;&nbsp;&nbsp;&nbsp;'
		output = output + '<a href = "/join">Join</a><br><br><br>'
	
	if input_uri == 'main':
		if 'username' in session:
			return output + render_template('main.html', user_name = escape(session['username'][1]))
		else:
			return output + render_template('main.html')
		
	else:
		result = ''
		
		try:
			result = db.session.execute(text('CALL sp_read(:in1, @out1)', bindparams=[bindparam('in1', type_=String, value=input_uri)])).fetchall()
			
			output = output + 'Call Procedure Success<br><br>'
		except:
			pass
			
		output = output + ''
		result_code = 0
		
		if result is not None:
			for row in result:
				if 'output_result' in row:
					result_code = row['output_result']
					output = output + 'ResultNo : ' + str(result_code) + '<br>'
					
					if result_code == 0:
						output = '/input/' + input_uri
						
						return redirect(output)
					
				if 'contents' in row:
					output = output + 'Contents : ' + row['contents'] + '<br>'
					output = output + '<br><a href = "/history/' + input_uri +'">View History</a>'
					
					if 'username' in session:
						if result_code > 0:
							output = output + '<br><a href = "/edit/' + input_uri + '">Edit</a>'
						else:
							output = output + '<br>This Document is Locked by Admin'
						
						if session['username'][2] == 'admin':
							output = output + '<br><a href = "/delete/' + input_uri + '">Delete</a>'
							
							if result_code > 0:
								output = output + '<br><a href = "/lock/' + input_uri + '">Lock</a>'
							else:
								output = output + '<br><a href = "/unlock/' + input_uri + '">Unlock</a>'
						
		return output

@app.route('/lock/<string:input_uri>')
def lock(input_uri):
	output = '/wiki/' + input_uri
			
	if 'username' in session and session['username'][2] == 'admin':
		try:
			user_index = session['username'][0]
			#CALL sp_lock(user_index, 'title', user_index);
			db.session.execute(text('CALL sp_lock(:in1, :in2, :in3)', bindparams=[bindparam('in1', type_=Integer, value=user_index),bindparam('in2', type_=String, value=input_uri),bindparam('in3', type_=Integer, value=user_index)])).fetchall()

		except:
			pass
				
	return redirect(output)

@app.route('/unlock/<string:input_uri>')
def unlock(input_uri):
	output = '/wiki/' + input_uri
				
	if 'username' in session and session['username'][2] == 'admin':
		try:
			user_index = session['username'][0]
			#CALL sp_lock(user_index, 'title', user_index);
			db.session.execute(text('CALL sp_lock(:in1, :in2, :in3)', bindparams=[bindparam('in1', type_=Integer, value=user_index),bindparam('in2', type_=String, value=input_uri),bindparam('in3', type_=Integer, value=0)])).fetchall()

		except:
			pass
					
	return redirect(output)

@app.route('/block/<string:input_uri>')
def block_user(input_uri):
	output = '/wiki/main'
	
	if 'username' in session and session['username'][2] == 'admin':
		try:
			user_index = session['username'][0]
			#CALL sp_block(index, 'login_id');
			db.session.execute(text('CALL sp_block(:in1, :in2)', bindparams=[bindparam('in1', type_=Integer, value=user_index),bindparam('in2', type_=String, value=input_uri)])).fetchall()

		except:
			pass
						
	return redirect(output)

@app.route('/delete/<string:input_uri>')
def delete(input_uri):
	output = '/wiki/' + input_uri
	
	if 'username' in session and session['username'][2] == 'admin':
		try:
			user_index = session['username'][0]
			#CALL sp_delete(index, 'title');
			db.session.execute(text('CALL sp_delete(:in1, :in2)', bindparams=[bindparam('in1', type_=Integer, value=user_index),bindparam('in2', type_=String, value=input_uri)])).fetchall()

		except:
			pass
		
	return redirect(output)
	
@app.route('/history/<string:input_uri>', methods=['GET'])
def history(input_uri):
	output = ''

	if 'username' in session:
		output = output + '<a href = "/logout?request_uri=' + input_uri + '">Log Out</a>&nbsp;&nbsp;&nbsp;&nbsp;'
		output = output + 'You signed in as ' + session['username'][1] + '&nbsp;&nbsp;'
				
		if session['username'][2] == 'admin':
			output = output + '[admin]<br><br><br>'
		else:
			output = output + '[member]<br><br><br>'
	else:
		output = output + '<a href = "/login?request_uri=' + input_uri + '">Login</a>&nbsp;&nbsp;&nbsp;&nbsp;'
		output = output + '<a href = "/join">Join</a><br><br><br>'
		
	try:
		if request.method == 'GET':
			history_index = request.args.get('history_index')
			
			if history_index is None:
				history_index = 0
				
			result = db.session.execute(text('CALL sp_history(:in1, :in2);', bindparams=[bindparam('in1', type_=Integer, value=history_index),bindparam('in2', type_=String, value=input_uri)])).fetchall()
			output = output + 'Call Procedure Success<br><br>'
	
			if result is not None:
				if history_index == 0:
					output = output + '<a href = "/wiki/' + input_uri + '">Back To Wiki Page</a><br><br>'
					for row in result:
						output = output + '<a href = "/history/' + input_uri + '?history_index=' + str(row['document_index']) + '">'
						output = output + 'Index : ' + str(row['document_index']) + ' '
						output = output + 'Author - ' + row['name'] + ' '
						output = output + 'Date ' + str(row['written_time']) + '</a>'
						output = output + '<br>'
					
				else:
					output = output + '<a href = "/history/' + input_uri + '">Back To History</a><br><br>'
					for row in result:
						output = output + 'Index : ' + str(row['document_index']) + ' '
						output = output + 'Author - ' + row['name'] + ' '
						output = output + 'Date ' + str(row['written_time']) + '<br>'
						output = output + row['contents'] + '<br>'
				
				return output
	except:
		return output

@app.route('/edit/<string:input_uri>', methods=['POST', 'GET'])
def update_contents(input_uri):
	output = '' + input_uri
	
	if 'username' not in session:
		output = 'You have to Login for creating page<br><br>'
		output = output + '<a href = '
		target_uri = '/login?request_uri=' + input_uri
			
		output = output + target_uri + '>Login</a>'
			
		return output
	
	if request.method == 'POST':
			
		try:
			#CALL sp_update(index, 'title', 'contents');
			user_number = session['username'][0]
			contents = request.form['contents']
				
			db.session.execute(text('CALL sp_update(:in1, :in2, :in3)', bindparams=[bindparam('in1', type_=Integer, value=user_number), bindparam('in2', type_=String, value=input_uri), bindparam('in3', type_=String, value=contents)])).fetchall()

		except:
			pass
			
		target_uri = '/wiki/' + input_uri
		return redirect(target_uri)
		
	else:
		result_contents = ''
		result = ''
				
		try:
			result = db.session.execute(text('CALL sp_read(:in1, @out1)', bindparams=[bindparam('in1', type_=String, value=input_uri)])).fetchall()
					
			output = output + 'Call Procedure Success<br><br>'
		except:
			pass
		
		if result is not None:
			for row in result:
				if 'output_result' in row:
					result_code = row['output_result']
					output = output + 'ResultNo : ' + str(result_code) + '<br>'
							
					if result_code == 0:
						output = '/input/' + input_uri
								
						return redirect(output)
							
					if 'contents' in row:
						result_contents = row['contents']
						
		return render_template('update.html', input_uri = input_uri, contents = result_contents)

@app.route('/input/<string:input_uri>', methods=['POST', 'GET'])
def input_contents(input_uri):
	output = '' + input_uri

	if 'username' not in session:
		output = 'You have to Login for creating page<br><br>'
		output = output + '<a href = '
		target_uri = '/login?request_uri=' + input_uri
		
		output = output + target_uri + '>Login</a>'
		
		return output
	
	if request.method == 'POST':
		
		try:
			# CALL sp_write(1, 'title', 'contents', 'category');
			user_number = session['username'][0]
			contents = request.form['contents']
			category = request.form['category']
			
			db.session.execute(text('CALL sp_write(:in1, :in2, :in3, :in4)', bindparams=[bindparam('in1', type_=Integer, value=user_number), bindparam('in2', type_=String, value=input_uri), bindparam('in3', type_=String, value=contents), bindparam('in4', type_=String, value=category)])).fetchall()

		except:
			pass
		
		target_uri = '/wiki/' + input_uri
		return redirect(target_uri)
	else:
		output_array = []
		
		try:
			result = db.session.execute('SELECT category_name FROM category').fetchall()
			
			if result is not None:
				for row in result:
					result_str = row['category_name']
					output_array.append(result_str)
		except:
			pass
		return render_template('input.html', category = output_array, input_uri = input_uri)

#url routing
@app.errorhandler(404)
def page_not_found(error):
	return '<br><br><br><center>Page Not Found</center>'

@app.after_request
def shutdown_session(response):
	db.session.remove()
	return response

@app.route('/join', methods=['POST', 'GET'])
def join():
	try:
		if request.method == 'POST':
			
			id = request.form['id']
			name = request.form['name']
			password = request.form['password']
			
			output = ''
			
			if name:
				result_code = 0
				result = ''
		
				try:
					# CALL sp_enterance('id', 'name', 'password', @result);
					result = db.session.execute(text('CALL sp_enterance(:in1, :in2, :in3, @out1)', bindparams=[bindparam('in1', type_=String, value=id), bindparam('in2', type_=String, value=name), bindparam('in3', type_=String, value=password)])).fetchall()

					if result is not None:
						for row in result:
							if 'output_result' in row:
								result_code = row['output_result']
								
								if result_code == 0:
									output = output + 'Sign Up Succeeded. Please Sign In By Your ID<br><br><br>'
									output = output + '<a href = "/login?request_uri=main">Login</a>'
								else:
									output = output + 'Sign Up Failed. Please Sign Up Another ID Again<br><br><br>'
									output = output + '<a href = "/join">Join</a>'

				except:
					pass

				return output
		else:
			return render_template('join.html')

	except:
		pass
	
	return redirect('wiki/main')
	
@app.route('/login', methods=['POST', 'GET'])
def login(user_name = None):
	if 'username' in session:
		return redirect('wiki/main')
	
	try:
		if request.method == 'GET':
			from_uri = request.args.get('request_uri')
			if from_uri is not None:
				session['from_uri'] = from_uri
	except:
		pass
		
	try:
		if request.method == 'POST':
			
			id = request.form['id']
			password = request.form['password']
			
			output = ''
			
			if id:
				result_code = 0
				result = ''
					
				try:
					result = db.session.execute(text('CALL sp_login(:in1, :in2, @out1)', bindparams=[bindparam('in1', type_=String, value=id), bindparam('in2', type_=String, value=password)])).fetchall()
						
					if result is not None:
						for row in result:
							if 'output_result' in row:
								result_code = row['output_result']
								output = output + 'ResultNo : ' + str(result_code) + '<br>'
											
								if result_code == 0:
									output = output + 'Not Found ID <br>'
								elif result_code == -1:
									output = output + 'Wrong Password <br>'
								elif result_code == -2:
									output = output + 'Blocked ID <br>'
								else:
									level = row['user_level']
									user_name = row['user_name']
									
									session['username'] = [result_code, user_name, level]

				except:
					pass
			
			if 'username' in session:
				if 'from_uri' in session and session['from_uri'] is not None:
					target_uri = '/wiki/' + session['from_uri']
					return redirect(target_uri)
			
				return redirect('wiki/main')
			else:
				output = '<a href = "/login">Login</a><br><br><br>' + output
				return output

		else:
			return render_template('login.html')
	
	except KeyError, err:
		print '[error] : ', err
		
		return '<br><br><br><center>Bad Request</center>'

@app.route('/logout', methods=['GET'])
def logout():
	try:
		if request.method == 'GET':
			from_uri = request.args.get('request_uri')
			if from_uri is not None:
				session['from_uri'] = from_uri
	except:
		pass
		
	session.pop('username', None)
	
	if 'from_uri' in session and session['from_uri'] is not None:
		target_uri = '/wiki/' + session['from_uri']
		session.pop('from_uri', None)
		
		return redirect(target_uri)
	else:
		return redirect('/wiki/main')


@app.route('/wiki/')
def wiki_init_slash():
	return redirect('/wiki/main')


@app.route('/wiki')
def wiki_init():
	return redirect('/wiki/main')

			
@app.route('/')
def init():
	return redirect('/wiki/main')

			
if __name__ == '__main__':
	app.secret_key = "\xa4e\xb6K\xa6\xae$\xaa\x85\x0b\xe1'\xf6D\xff}\x8d\xbd\xfa\xd5\xff$=\xf4"
	app.run(debug=True, port=8080) # host='0.0.0.0', 