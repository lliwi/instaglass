from flask import (
    Blueprint, flash, g, render_template, request, url_for, session, redirect, current_app, make_response, Response
)
from app.db import get_db
import re
import os
import time
import datetime
from datetime import timedelta
from apify_client import ApifyClient
from openai import OpenAI

bp = Blueprint('instaglass', __name__, url_prefix='/')


def openai_cli(image_url, observations):
  OPENAI_API_KEY = current_app.config['OPENAI_API_KEY'] 
  client = OpenAI(api_key=OPENAI_API_KEY)
  response = client.responses.create(
      model="gpt-4.1",
      input=[
          {
              "role": "user",
              "content": [
                  { "type": "input_text", "text": """Eres un asistente experto en detectar fraude en las actividades laborales. Se te proporcionarán imágenes de redes sociales de un empleado que se encuentra de baja laboral y las observaciones correspondientes. Tu tarea es analizar cada imagen detenidamente y establecer si hay indicios de actividad física, social o recreativa que no sea compatible con un estado de convalecencia.
                    Para cada imagen, por favor, genera una respuesta que incluya los siguientes puntos:
                        1. Descripción general de la imagen: ¿Qué se ve en la imagen? (ej. personas, lugares, objetos).
                        2. Actividades representadas: ¿Qué están haciendo las personas en la imagen? ¿Hay alguna actividad específica que se esté llevando a cabo?
                        3. Contexto y entorno: ¿Dónde se tomó la imagen? (ej. interior/exterior, ciudad, playa, montaña, evento social). ¿Qué tipo de ambiente se percibe?
                        4. Indicios de actividad física o esfuerzo:
                        · ¿La persona está realizando alguna actividad que requiera esfuerzo físico (ej. deportes, baile, levantar objetos pesados, caminar largas distancias, etc.)?
                        · ¿La vestimenta o el equipamiento sugieren actividad física (ej. ropa deportiva, equipamiento de ocio)?
                        · ¿Hay signos de movimiento o dinamismo en la imagen?
                        5. Indicios de actividad social o recreativa:
                        · ¿La persona está en un entorno social (ej. reuniones, fiestas, eventos, bares, restaurantes)?
                        · ¿La actividad parece ser de ocio o recreación (ej. viajes, vacaciones, conciertos, festivales)?
                        · ¿Hay elementos que sugieran un ambiente de diversión o entretenimiento?
                        6. Discrepancia con la convalecencia: Basándose en los puntos anteriores, ¿la imagen sugiere alguna actividad que podría ser inconsistente con una baja laboral por convalecencia? Justifica tu respuesta.

                    Responde con una valoración del 0 al 10 donde 10 es que la actividad es completamente incompatible con la convalecencia y 0 es que es completamente compatible. Ten en cuenta las observaciones:{observations}
                        Ejemplo de salida esperada:
                        · Descripción de la imagen: La imagen muestra a una persona de pie en una pista de pádel al aire libre, sosteniendo una raqueta. Hay otra persona en el fondo. El clima parece soleado.
                        · Actividades representadas: La persona está equipada para jugar pádel, lo que implica una actividad física.
                        · Contexto y entorno: La imagen fue tomada en una pista de pádel al aire libre, lo que sugiere un entorno deportivo o recreativo.
                        · Indicios de actividad física o esfuerzo: La persona está vestida con ropa deportiva y sostiene una raqueta de pádel, indicando una actividad física activa que requiere movimiento y esfuerzo.
                        · Indicios de actividad social o recreativa: Se trata de una actividad deportiva, a menudo practicada en grupo, lo que también la clasifica como recreativa y social.
                        · Discrepancia con la convalecencia: La imagen sugiere una actividad física intensa (jugar pádel) que podría ser inconsistente con una baja laboral por convalecencia, ya que implica movimientos rápidos, torsiones y esfuerzo cardiovascular, que no son típicos de alguien en recuperación.
                        · Valoración: 10""" },
                  {
                      "type": "input_image",
                      "image_url": image_url
                  }
              ]
          }
      ],
      temperature=0.2
  )

  return response

@bp.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@bp.route('/cron', methods=['GET'])
def cron():
    db, c = get_db()
    c.execute("select Id, date, observation, instagram_account from employees where active = 'on';")
    employees = c.fetchall()

    for employee in employees:
        c.execute('select instagram_last_post from tasks where employee_id = %s;', (employee['Id'],))
        last_post = c.fetchone()

        if  last_post is not None:
            if last_post['instagram_last_post'].date() > employees[0]['date']:
                last_date = last_post['instagram_last_post'].date() + timedelta(days=1)
            else:
                last_date = employees[0]['date']
        else:
            last_date = employees[0]['date']
        
        client = ApifyClient(current_app.config['APIFY_KEY'])
        run_input = {
            "directUrls": [
                f"https://www.instagram.com/{employee['instagram_account']}"
            ],
            "resultsLimit": 5,
            "resultsType": "posts",
            "searchLimit": 1,
            "searchType": "user",
            "onlyPostsNewerThan": last_date,
        }

        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        count = 0
        try:
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                item['caption'] = item['caption'].replace('/n', '')
                item['caption'] = item['caption'].replace('#', '')
                item['timestamp'] = datetime.datetime.strptime(item['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
                item['hashtags'] = ", ".join(item['hashtags']) if item['hashtags'] else ''
                item['mentions'] = ", ".join(item['mentions']) if item['mentions'] else ''
                item['latestComments'] = ", ".join(item['latestComments']) if item['latestComments'] else ''
                item['images'] = ", ".join(item['images']) if item['images'] else ''
                item['childPosts'] = ", ".join(item['childPosts']) if item['childPosts'] else ''
                count += 1

                #hashtags, mentions, lastComments, images, childPosts
                #print(item)
                add_post = ('insert into instagram' 
                        '(employee_id, InputUrl, Type, ShortCode, Caption, Hashtags, Mentions, CommentsCount, FirstComment, LatestComments, DisplayUrl, Images, AltText, LikesCount, Timestamp, OwnerFullName, OwnerUsername)'
                        ' values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)') 
                data_post = (employee['Id'], item['inputUrl'], item['type'],  item['shortCode'], item['caption'], item['hashtags'], item['mentions'], item['commentsCount'], item['firstComment'], item['latestComments'], item['displayUrl'], item['images'], item['alt'], item['likesCount'],  item['timestamp'], item['ownerFullName'], item['ownerUsername'])
                c.execute(add_post, data_post)
                db.commit()

                c.execute('select employee_id from tasks where employee_id = %s', (employee['Id'],))
                if c.fetchone() is None:
                    c.execute('insert into tasks (employee_id, instagram_last_post) values (%s, %s);', (employee['Id'], item['timestamp']))
                else:
                    c.execute('update tasks set instagram_last_post = %s where employee_id = %s;', (item['timestamp'], employee['Id']))
                db.commit()
        except Exception as e:
            print(f"No new posts found for {employee['Id']} - {employee['instagram_account']}: {e}")
        if count > 0:

        
            # Get posts description and score from OpenAI
            c.execute("select employees.Id, employees.observation, instagram.DisplayUrl, instagram.ShortCode from employees JOIN instagram ON instagram.employee_id = employees.Id WHERE employees.active = 'on';")
            posts = c.fetchall()

            for post in posts:
                try:
                    result = openai_cli(post['DisplayUrl'], post['observation'])
                    #print(result.output_text)
                    valoracion = re.search(r"Valoración: (\d+)", result.output_text)
                    if valoracion:
                        score = valoracion.group(1)
                    else:
                        score = None

                    c.execute('insert into posts (employee_id, ShortCode, Description, Score) values (%s, %s, %s, %s);', (post['Id'], post['ShortCode'], result.output_text, score))
                    db.commit()
                except Exception as e:
                    print(f"Error processing post {post['ShortCode']}: {e}")

    return 'Cron job completed successfully', 200
