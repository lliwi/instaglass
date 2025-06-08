
from flask import (
    Blueprint, flash, g, render_template, request, url_for, session, redirect, current_app, make_response, send_file
)

from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import functools
import os
import csv
import zipfile
import uuid

from app.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db, c = get_db()
        error = None
        c.execute(
            'select id, user, password from users where user = %s', (username.lower(),)
        )

        user = c.fetchone()

        if user is None:
            error = 'invalid user / password'
        elif not check_password_hash(user['password'], password):
            error = 'invalid user / password'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('auth.index'))

        flash(error)
        print('si, error')

        resp = make_response(render_template('auth/login.html', error=error))
        return resp

    else:

        resp = make_response(render_template('auth/login.html'))
        return resp


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.usert = None
    else:
        db, c = get_db()
        c.execute(
            'select * from users where id = %s', (user_id,)
        )
        g.user = c.fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.route('/')
@login_required
def index():

    resp = make_response(render_template('auth/index.html'))
    return resp

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():

    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        username = request.form['username']
        password = request.form['password']

        db, c = get_db()
        error = None
        c.execute(
            'select id from users where user = %s', (username,)
        )
        if not username:
            error = 'Username es requerido'
        if not password:
            error = 'Password es requerido'
        elif c.fetchone() is not None:
            error = 'User {} exists.'.format(
                username)

        if error is None:
            c.execute(
                'insert into users (name, surname, user, password) values (%s, %s, %s, %s)',
                (name, surname, username.lower(), generate_password_hash(password))
            )
            db.commit()

            db, c = get_db()
            c.execute('select id, name, surname, user from users')
            users = c.fetchall()
   
            return render_template('auth/register.html', users=users)
        db, c = get_db()
        c.execute('select id, name, surname, user from users')
        users = c.fetchall()

        flash(error)
       
        return render_template('auth/register.html', error=error, users=users)
        error = None

    else:
        db, c = get_db()
        c.execute('select id, name, surname, user from users')
        users = c.fetchall()
        return render_template('auth/register.html',  users=users)


@bp.route('/delete')
@login_required
def delete():
    id = request.args.get('id')
    db, c = get_db()
    c.execute('delete  from users where id = %s', (id,))
    db.commit()

    db, c = get_db()
    c.execute('select id, name, surname, user from users')
    users = c.fetchall()
    return redirect(url_for('auth.register'))

@bp.route('/employees', methods=['GET', 'POST'])
@login_required
def employees():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        date = request.form['date']
        observation = request.form['observation']
        instagram_account = request.form['instagram_account']
        facebook_account = request.form['facebook_account']
        active = request.form.get('active')
                        
        if not name:
            error = 'Name es requerido'
        if not surname:
            error = 'Surname es requerido'
        if not date:
            error = 'Date es requerido'
        else :
            error = None

        if error is None:
            db, c = get_db()
            c.execute(
                'insert into employees (name, surname, date, observation, instagram_account, facebook_account, active) values (%s, %s, %s, %s, %s, %s, %s)',
                (name, surname, date, observation, instagram_account, facebook_account, active)
            )
            db.commit()

            db, c = get_db()
            c.execute('select id, name, surname, date, observation, instagram_account, facebook_account, active from employees')
            employees = c.fetchall()

            return render_template('auth/employees.html', employees=employees)
        db, c = get_db()
        c.execute('select id, name, surname, date, observation, instagram_account, facebook_account, active from employees')
        users = c.fetchall()

        flash(error)
       
        return render_template('auth/employees.html', users=users)
        error = None

    else:
        db, c = get_db()
        c.execute('select id, name, surname, date, observation, instagram_account, facebook_account, active from employees')
        employees = c.fetchall()
        return render_template('auth/employees.html', employees=employees)


@bp.route('/employee_delete')
@login_required
def employee_delete():
    id = request.args.get('id')
    db, c = get_db()
    c.execute('delete  from employees where id = %s', (id,))
    db.commit()

    db, c = get_db()
    c.execute('select id, name, surname, date, observation, instagram_account, facebook_account, active from employees')
    employees = c.fetchall()
    #return render_template('auth/employees.html', employees=employees)
    return redirect(url_for('auth.employees'))

@bp.route('/export')
@login_required
def employee_export():
    export_dir = os.path.join(current_app.root_path, 'static/export')
    for filename in os.listdir(export_dir):
        if filename.endswith(".zip"):
            file_path = os.path.join(export_dir, filename)
            try:
                os.remove(file_path)
                print(f"  - Eliminado: '{filename}'")
            except PermissionError:
                print(f"  - Error de permisos: No se pudo eliminar '{filename}'.")
            except OSError as e:
                print(f"  - Error del sistema: No se pudo eliminar '{filename}': {e}")
         

    db, c = get_db()
    c.execute('select id, name, surname, date, observation, instagram_account, facebook_account, active from employees')
    employees = c.fetchall()

    csv_file_name = 'employees.csv'
    csv_file_path = os.path.join(current_app.root_path, 'static/export', csv_file_name)

    with open(csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['id', 'name', 'surname', 'date', 'observation', 'instagram_account', 'facebook_account', 'active']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for employee in employees:
            writer.writerow(employee)
    
    c.execute('select employee_id, InputUrl, Type, ShortCode, Caption, Hashtags, Mentions, CommentsCount, FirstComment, LatestComments, DisplayUrl, Images, AltText, LikesCount, Timestamp, OwnerFullName, OwnerUsername from instagram')
    instagram_posts = c.fetchall()
    instagram_csv_file_name = 'instagram_posts.csv'
    instagram_csv_file_path = os.path.join(current_app.root_path, 'static/export', instagram_csv_file_name)

    with open(instagram_csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['employee_id', 'InputUrl', 'Type', 'ShortCode', 'Caption', 'Hashtags', 'Mentions', 'CommentsCount', 'FirstComment', 'LatestComments', 'DisplayUrl', 'Images', 'AltText', 'LikesCount', 'Timestamp', 'OwnerFullName', 'OwnerUsername']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for post in instagram_posts:
            writer.writerow(post)
    c.execute('select employee_Id, ShortCode, Description, Score, creation_date from posts')
    posts = c.fetchall()
    posts_csv_file_name = 'posts.csv'
    posts_csv_file_path = os.path.join(current_app.root_path, 'static/export', posts_csv_file_name)

    with open(posts_csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['employee_Id', 'ShortCode', 'Description', 'Score', 'creation_date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for post in posts:
            writer.writerow(post)

    # Return the CSV files as a zip file or individual files
    response = make_response()
    response.headers['Content-Disposition'] = 'attachment; filename=export.zip'
    response.headers['Content-Type'] = 'application/zip'
    unique_id = uuid.uuid4().hex
    zip_file_path = os.path.join(current_app.root_path, 'static/export', f'export_{unique_id}.zip')


    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        zipf.write(csv_file_path, arcname=csv_file_name)
        zipf.write(instagram_csv_file_path, arcname=instagram_csv_file_name)
        zipf.write(posts_csv_file_path, arcname=posts_csv_file_name)
    # Clean up the individual CSV files if needed
    if os.path.exists(csv_file_path):
        os.remove(csv_file_path)
    if os.path.exists(instagram_csv_file_path):
        os.remove(instagram_csv_file_path)
    if os.path.exists(posts_csv_file_path):
        os.remove(posts_csv_file_path)
 
    return send_file(zip_file_path, as_attachment=True)



@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


   

