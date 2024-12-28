import pandas as pd
import datetime
from django.db import connection
from django.http import HttpRequest


def make_session_id(x: pd.Series):

    id_ = f"{x['date']}-{x['time']}-{x['type_of_lesson']}-{x['location']}"

    return id_


def load_surf_schedule_data(request: HttpRequest, next_days: int = 3):
    """
    this helper function will fetch the surf schedule for the upcoming
    next three days
    """

    is_management = request.user.groups.filter(name="Management").exists()

    today = datetime.datetime.today()

    if is_management:
        end_date = today + datetime.timedelta(days=next_days)
    else:
        end_date = today + datetime.timedelta(days=1)

    filter_query = ""

    if not is_management:
        filter_query = f"""
            INNER JOIN (
	         	SELECT lc1.lesson_id FROM schedule_lesson_coach AS lc1
	         		INNER JOIN schedule_coach AS c 
	         			ON c.id = lc1.coach_id
	         		INNER JOIN auth_user AS u
	         			ON u.id = c.user_id
	                     WHERE u.id = {request.user.id}
	                 ) AS tmp
	                     ON tmp.lesson_id = l.id
        """

    sql_query = f"""
            SELECT l.id, l."date",l."time", l.meeting_point,
            u.username AS coach,
            l.type_of_lesson, l."location", 
            concat(s.first_name, ' ',s.last_name) AS student,
            l.number_of_participants as total,
            l.comment
            FROM schedule_lesson AS l
            INNER JOIN schedule_lesson_coach AS lc
                ON l.id = lc.lesson_id
            INNER JOIN schedule_coach AS c
                ON c.id = lc.coach_id
            INNER JOIN auth_user AS u
                ON u.id = c.user_id
            LEFT JOIN schedule_lesson_participant AS p
                ON p.lesson_id = l.id 
            LEFT JOIN schedule_student AS s
                ON s.id = p.student_id
            {filter_query}
            WHERE l.date >= '{today.date()}'
            AND l.date <= '{end_date.date()}'
            AND l.status = 'LIVE'
            ORDER BY l."date", l."time", u.username
            """

    tabledata = pd.read_sql_query(sql_query, con=connection)

    for field in ["date", "time"]:
        tabledata[field] = tabledata[field].astype(str)

    session_fields = ["date", "time", "type_of_lesson", "location"]

    tabledata["session_id"] = tabledata.apply(make_session_id, axis=1)

    comments = tabledata.groupby("session_id").comment.last().to_dict()
    print(comments)
    jsondata = tabledata.to_dict("records")

    return jsondata, comments
