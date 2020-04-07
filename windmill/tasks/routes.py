








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os
import subprocess as sub
from datetime import datetime

from windmill.main.utils import trace, divisor, __resolve_path, MsgTypes
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === globals and config ======================================================
TASKS = [] #THIS SHOULD BE CHANGED IN FUTURE FOR SOME DATABASE MODEL DATA REPRESENTATION
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

tasks = Blueprint('tasks', __name__)

# === HELPERS functions =======================================================
@tasks.route('/test')
def test():
    return render_template('running_t.html')
    #return render_template('test.html')

def _filter_task_by_id_or_name(name_id):
    global TASKS
    selected_task_arr = list(filter(lambda task : (task["name"] == name_id or task["id"] == str(name_id)), TASKS))
    selected_task = None
    if(len(selected_task_arr) > 0):
        selected_task = selected_task_arr[0]
    return (selected_task_arr, selected_task)

def isAlive(task):
    return (task["pointer"] != None and task["pointer"].poll() == None)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



# === WRAPPED FUNCTIONS =======================================================
def _play_task(task_id):
    global TASKS
    try:
        print("tasks", divisor)
        print("tasks", "PLAY invoked ", task_id)
        print("tasks", divisor)
        (_, task) = _filter_task_by_id_or_name(task_id)
        print("tasks", "PLAY> ", task)

        if(task != None):
            print("tasks", divisor)
            print("tasks", app.config['python_cmd'] + " ", os.path.join(app.config['UPLOAD_FOLDER'], task["entry"]))
            print("tasks", divisor)
            log = open((task["name"]+'.txt'), 'a')  # so that data written to it will be appended
            #p = sub.Popen(['python3 ', (os.path.join(app.config['UPLOAD_FOLDER'], task["entry"]))], stdout=log)
            p = sub.Popen([(app.config['python_cmd'] + ' '), (os.path.join(app.config['UPLOAD_FOLDER'], task["entry"]))], stdout=log)
            TASKS[task_id]["pointer"] = p
            TASKS[task_id]["pid"] = p.pid
            TASKS[task_id]["status"] = "running"
            print("tasks", "EXECUTING .. ", (os.path.join(app.config['UPLOAD_FOLDER'], task["entry"])))
            print("tasks", divisor)
            print("tasks", "SUCESS ", app.config['SUCCESS'])
            flash({'title' : "Task Action", 'msg' : "Task id:{} is now running".format(str(task['id'])), 'type' : MsgTypes['SUCCESS']})
            return app.config['SUCCESS']
        else:
            return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

def _stop_task(task_id):
    global TASKS
    try:
        print("tasks", "STOP invoked")
        (_, task) = _filter_task_by_id_or_name(task_id)

        if(task != None):
            TASKS[task_id]["pointer"].kill()
            TASKS[task_id]["status"] = "not active"
            print("tasks", "KILLING .. ", task["entry"])
            flash({'title' : "Task Action", 'msg' : "Task id:{} is now stopped".format(str(task['id'])), 'type' : MsgTypes['SUCCESS']})
            return app.config['SUCCESS']
        else:
            return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

def _schedule_task(task_id):
    global TASKS
    try:
        print("tasks", "SCHEDULE invoked")
        (_, task) = _filter_task_by_id_or_name(task_id)

        if(task != None):
            print("tasks", "task is not None")
            p = sub.Popen([(app.config['python_cmd'] + ' '), '.\executor.py', (os.path.join(app.config['UPLOAD_FOLDER'], task["entry"])), "seconds", "90"])
            TASKS[task_id]["pointer"] = p
            TASKS[task_id]["pid"] = p.pid
            TASKS[task_id]["status"] = "running (schdl)"
            print("tasks", "SCHEDULED .. ", (os.path.join(app.config['UPLOAD_FOLDER'], task["entry"])))
            return app.config['SUCCESS']
        else:
            return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === API routes ==============================================================
@tasks.route('/api/tasks/', methods=["GET","POST"])
def running():
    global TASKS
    try:
        if(request.method == "POST"):
            print("tasks", "running - POST")
            print("tasks", request.form)

            TASKS.append({
                    "id" : str(len(TASKS)),
                    "pid" : None,
                    "name" : request.form['taskName'],
                    "entry" : __resolve_path(request.form['taskEntry']),
                    "cron" : "{} {} {} {} {}".format(
                        '/s' if request.form['datetimepicker1_input'] else '-',
                        request.form['taskCronValueHours'],
                        request.form['taskCronValueMins'],
                        request.form['taskCronValueSecs'],
                        '/e' if request.form['datetimepicker2_input'] else '-',
                    ),
                    "pointer" : None,
                    "status" : "not running",
                    "started_at" : datetime.now().strftime("%Y-%d-%m %H:%M:%S")
                })
            flash({ 'title' : "Task", 'msg' : "Task {} created with id: {}.".format(str(TASKS[-1]['name']), str(TASKS[-1]['id'])), 'type' : MsgTypes['SUCCESS'] })
            return redirect('/') #render_template('running.html', tasks=TASKS)
        elif(request.method == "GET"):
            print("tasks", "running - GET")
            for idx, task in enumerate(TASKS):
                TASKS[idx]["status"] = "running" if(isAlive(task)) else "not running"
            return jsonify(list(map(lambda task : {
                'id': task['id'], 'pid': task['pid'], 'name': task['name'], 'entry': task['entry'],
                'cron': task['cron'], 'status': task['status'], 'started_at': task['started_at']}, list(filter(lambda task :
                task['status'] != 'deleted' ,TASKS)))))
        return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

@tasks.route('/api/task/<int:task_id>', methods=["DELETE", "GET"])
def task(task_id):
    global TASKS
    try:
        print("tasks", "TASK -> ", request.method, " --> ", task_id)
        if(request.method == "DELETE"):
            (_, task) = _filter_task_by_id_or_name(task_id)
            if(task != None):
                if(TASKS[task_id]["pointer"]):
                    TASKS[task_id]["pointer"].kill()
                TASKS[task_id]["status"] = "deleted"
                return app.config['SUCCESS']
            else:
                return abort(404)
        elif(request.method == "GET"):
            (_, task) = _filter_task_by_id_or_name(task_id)
            if(task != None):
                return jsonify({
                    'id': task['id'], 'pid': task['pid'], 'name': task['name'], 'entry': task['entry'],
                    'cron': task['cron'], 'status': task['status'], 'started_at': task['started_at']})
            else:
                return abort(404)
        return abort(405)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

@tasks.route('/api/task/info/<int:task_id>')
def info_task(task_id):
    global TASKS
    try:
        print("tasks", "INFO invoked")
        (_, task) = _filter_task_by_id_or_name(task_id)
        data = ""
        if(task != None):
            print("tasks", "task is not None")
            with open((task["name"]+'.txt'), 'r') as task_file:
                data = task_file.read()
            return jsonify(data)
        else:
            return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

@tasks.route('/api/task/play/<int:task_id>')
def api_play_task(task_id):
    ans = _play_task(task_id)
    print("tasks", "PLAY return", ans, app.config['SUCCESS'], ans == app.config['SUCCESS'])
    if(ans == app.config['SUCCESS']):
        return jsonify(success=True)
    else:
        return ans

@tasks.route('/api/task/stop/<int:task_id>')
def api_stop_task(task_id):
    ans = _stop_task(task_id)
    if(ans == app.config['SUCCESS']):
        return jsonify(success=True)
    else:
        return ans

@tasks.route('/api/task/schedule/<int:task_id>')
def api_schedule_task(task_id):
    ans = _schedule_task(task_id)
    if(ans == app.config['SUCCESS']):
        return jsonify(success=True)
    else:
        return ans
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# === Application routes ======================================================
@tasks.route('/')
def home():
    global TASKS
    error = ''
    try:
        if(request.method == "POST"):
            print("tasks", "home-POST")
            print("tasks", request.form)

            TASKS.append({
                    "id" : str(len(TASKS)),
                    "pid" : None,
                    "name" : request.form['taskName'],
                    "entry" : __resolve_path(request.form['taskEntry']),
                    "cron" : None,
                    "pointer" : None,
                    "status" : "not running",
                    "no_runs" : 0,
                    "started_at" : datetime.now().strftime("%Y-%d-%m %H:%M:%S")
                })
            flash({'title' : "Task", 'msg' : "Task {} created with id: {}.".format(str(TASKS[-1]['name']), str(TASKS[-1]['id'])), 'type' : MsgTypes['SUCCESS']})
            print("tasks", TASKS)
        elif(request.method == "GET"):
            for idx, task in enumerate(TASKS):
                TASKS[idx]["status"] = "running" if(isAlive(task)) else "not running"
            print("tasks", "home-GET")

        print("tasks", divisor)
        print("tasks", " --> TASKS", TASKS)
        print("tasks", divisor)
        return render_template('running.html', tasks=TASKS)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

@tasks.route('/task/play/<int:task_id>')
def play_task(task_id):
    ans = _play_task(task_id)
    if(ans == app.config['SUCCESS']):
        return redirect('/')
    else:
        return ans

@tasks.route('/task/stop/<int:task_id>')
def stop_task(task_id):
    ans = _stop_task(task_id)
    if(ans == app.config['SUCCESS']):
        return redirect('/')
    else:
        return ans

@tasks.route('/task/schedule/<int:task_id>')
def schedule_task(task_id):
    ans = _schedule_task(task_id)
    if(ans == app.config['SUCCESS']):
        return redirect('/')
    else:
        return ans
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++