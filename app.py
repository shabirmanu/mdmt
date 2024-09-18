from flask import Flask, render_template,  flash, redirect, url_for, session, request, make_response, jsonify
from flask_mysqldb import MySQL
from forms import *
import random,os, csv
from tasks import TaskType, TaskIns
from prime import *
import numpy as np
import json
import datetime
import urllib
import requests
from textblob import TextBlob, Word
#import pallete


def connection():
    conn = MySQL.connect(host="localhost", user="root", passwd = "", db="mdmt")
    c = conn.cursor()
    return c, conn


app = Flask(__name__)
app.debug = True
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "cpsarchitecture"
app.config['MYSQL_CURSORCLASS'] = "DictCursor"

mysql = MySQL(app)

app.config.from_object('config')

data=[]

class AddMicroService(Form):
    title = StringField('Name', [validators.required("Please enter title for the micro service.")])
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name from services")
        choices = cur.fetchall()

    choices_data = [(-1,'Select Service')]
    for i in choices:
        choices_data += [(i['id'],i['name'])]
        print(i['id'],i['name'])

    service = SelectField('Select Service',choices=choices_data,id="select_service_id"
    )
    description = TextAreaField('Description', [validators.required("Please enter Description for the service.")])

class AddTask(Form):
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name from services")
        choices = cur.fetchall()

    choices_data = [(-1,'Select Service')]
    for i in choices:
        choices_data += [(i['id'],i['name'])]

    service = SelectField(
        'Select Service',
        choices=choices_data,
        id="select_service"
    )
    microservice = SelectField(
        'Select Micro Service',
        choices=[(-1,'Select Microservice')],
        id="select_mservice"
    )
    title = StringField('Title', [validators.required("Please enter title for the task.")])
    period = IntegerField('Period', [validators.required("Please enter period of the task.")])
    arrivalTime = IntegerField('Please enter Arrival Time Range', [validators.required("Please enter Arrival time End")])
    execution = IntegerField('Execution Time', [validators.required("Please enter Execution time")])
    deadline =      IntegerField('Deadline (To)', [validators.required("Please enter Deadline")])
    out_maxthreshold = IntegerField('Sensing Maximum Threshold',
                               [validators.required("Sensing Maximum Threshold")])
    out_minthreshold = IntegerField('Sensing Minimum Threshold', [validators.required("Please enter minimum Sensing threshold time")])
    period_maxthreshold = IntegerField('Period Maximum Threshold', [validators.required("Please enter maximum period threshold")])
    period_minthreshold = IntegerField('Period Minimum Threshold', [validators.required("Please enter minimum period threshold")])
    isEvent     = BooleanField( 'Event Driven Task')
    OperationMode     = BooleanField( 'Check for Observing Mode')
    #cur.close()


@app.route('/save-configuration')
def saveConf():
    return "saved"


@app.route('/gendataset', methods=['GET','POST'])
def genDataset():
    bme_url = "http://192.168.1.37/read-sensor?task=getTemperature"
    dust_url = "http://192.168.1.37/dust-sensor"
    co2_url = "http://192.168.1.80/getCo2"
    f = requests.get(bme_url)
    myfile = f.read()
    print(myfile)



@app.route('/deploy-tasks')
def deployTasks():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM mapped_task mt inner join virtualobjects as vo on vo.id = mt.vo_id inner join tasks t on t.id = mt.task_id  ")
    rows = cur.fetchall()
    return render_template("deploy_tasks.html", **locals())


@app.route('/virtual-objects')
def virtualObjects():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM virtualobjects")
    rows = cur.fetchall()



    return render_template("virtual-objects.html", **locals())

@app.route('/map-tasks')
def mapTasks():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM virtualobjects")
    vos = cur.fetchall()

    cur.execute("SELECT * FROM tasks")
    tasks = cur.fetchall()

    return render_template("map_tasks.html", **locals())


@app.route('/')
def tasks():
    return render_template("index.html")

@app.route('/addvirtualobj',methods=['GET','POST'])
def addVirtualObject():
    form = AddVirtualObject(request.form)
    if (request.method == 'POST' and form.validate()):
        name = form.name.data
        taskTags = json.dumps(form.taskTags.data)
        url = form.url.data
        methods = json.dumps(form.methods.data)
        attributes = json.dumps(form.attributes.data)



        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO virtualobjects(name, tasktags, url, methods, attributes) VALUES (%s, %s, %s, %s, %s)", (name, taskTags, url, methods, attributes))
        mysql.connection.commit()
        cur.close()

        flash('Task created successfully', 'success')


    return render_template("addvirtualobj.html",form=form)

@app.route('/addservice',methods=['GET','POST'])
def addService():
    form = AddService( request.form )
    if (request.method == 'POST' and form.validate()):
        title = form.title.data
        description = form.description.data

        cur = mysql.connection.cursor()

        now = datetime.datetime.now()

        cur.execute("INSERT INTO services(name, description, created_at, updated_at) VALUES (%s, %s, %s, %s)", (title, description, now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d %H:%M:%S")))
        mysql.connection.commit()
        inserted_id = cur.lastrowid
        cur.close()

        flash('Service created successfully', 'success')
        ms, tasks = _analyzeService(description)
        return render_template("addservice.html",service_id=inserted_id, ms=ms, tasks=tasks, suggestion = 1, form=form)

    return render_template("addservice.html",suggestion =0, form=form)


@app.route('/addmicroservice',methods=['GET','POST'])
def addMicroService():
    form = AddMicroService( request.form )

    # if request.method == 'GET':
    #     return render_template('addmicroservice.html', form=form)
    if (request.method == 'POST' ):
        service_id = form.service.data
        title = form.title.data
        description = form.description.data

        cur = mysql.connection.cursor()

        now = datetime.datetime.now()

        cur.execute("INSERT INTO microservices(name, description, service_id, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)", (title, description, service_id, now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d %H:%M:%S")))
        mysql.connection.commit()
        cur.close()

        flash('MicroService created successfully', 'success')
        #_analyzeService(description)

    return render_template("addmicroservice.html",form=form)

# Some NLP for analyzing Service Requirement
def _analyzeService(text):
    goal_synonym = set(['goal', 'motivation', 'purpose', 'task', 'responsible for'])
    sensor_synonym = set(['sensor', 'sense', 'read'])
    periodic_synonym = set(['period', 'periodically', 'repeat', 'repeatedly'])
    blob = TextBlob(text)
    sentences = blob.sentences
    matches = [s for s in blob.sentences if goal_synonym & set(s.words)]
    if (len(matches) > 0):
        ms_sentence = matches[0]

    ms_index = sentences.index(ms_sentence)
    ms_sentences = sentences.pop(ms_index)

    if (len(matches) > 0):
        ms_sentence = matches[0]

    # Get Microservice Suggestions
    micro_services = []
    for ms in ms_sentences.noun_phrases:
        ms_arr = ms.split(" ")
        ms_arr_set = set(ms_arr)

        if goal_synonym & set(ms_arr_set):
            g_matches = goal_synonym & set(ms_arr_set)
            print(ms)
            print(g_matches)
            continue
        micro_services.append(ms)

    tasks = []
    for sentence in sentences:
        for np in sentence.noun_phrases:
            np_array = np.split(" ")
            # print(np_array[0],np_array[1])
            if (np_array[1] == "sensor"):
                verb = "get"
                task_name = verb + np_array[0]
            else:
                verb = Word(np_array[0]).lemmatize()
                task_name = np_array[0] + np_array[1]
            tasks.append(task_name)

    return micro_services, tasks



@app.route('/discard',methods=['POST','GET'])
def discardPost():
    tasks = request.args.get('tasks')
    ms = request.args.get('ms')
    index = request.args.get('tableIndex')
    flag = request.args.get('flag')

    if(flag):
        tasks.pop(index)
        msg = "Task"
    else:
        msg = "Microservice"
        ms.pop(index)

    return jsonify(tasks), jsonify(ms)






@app.route('/addtask',methods=['GET','POST'])
def addTask():
    form = AddTask( request.form )
    services = form.service.data
    microservices = form.microservice.data
    if request.method == 'GET':
        task_def_val = request.args.get('tname')
        ser_def_val = request.args.get('sid')
        form.title.data = task_def_val
        form.service.default = ser_def_val
        #form.service = str(ser_def_val)
        return render_template('addtask.html',form=form)
    if (request.method == 'POST'):
        title = form.title.data
        period = int (form.period.data)
        arrivalTime = int (form.arrivalTime.data)
        execution = int (form.execution.data)
        deadline = int (form.deadline.data)
        op_max = int (form.out_maxthreshold.data)
        op_min = int (form.out_minthreshold.data)
        period_max = int (form.period_maxthreshold.data)
        period_min = int (form.period_minthreshold.data)
        is_observing = bool (form.OperationMode.data)
        isEvent = form.isEvent.data

        if(isEvent == True):
            urgency = urgency = random.randint( int( 0 ), int( 1 ) )
        else:
            urgency = 'NA'

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tasks(title, period, deadline, arrival, execution,ms_id, op_max, op_min, period_max, period_min, is_observing) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (title, period, deadline, arrivalTime, execution, microservices, op_max, op_min, period_max, period_min, is_observing))
        mysql.connection.commit()
        cur.close()

        flash('Task created successfully', 'success')


    return render_template("addtask.html",form=form)


# @app.route('/edittask/<int:task_id>', methods=['GET','POST'])
# def edit_task(task_id):
#     return render_template( "addtask.html", form=form )

@app.route('/_save_states/', methods=['GET','POST'])
def _save_states():
    from_id = request.args.get('from', '01', type=str)
    to_id = request.args.get('to', '01', type=str)
    cur = mysql.connection.cursor()
    now = datetime.datetime.now()
    cur.execute(
        "INSERT INTO mapped_task(task_id, vo_id, mapped_time) "
        "VALUES (%s, %s, %s)", (
        from_id, to_id, now.strftime("%Y-%m-%d %H:%M:%S")))
    mysql.connection.commit()
    cur.close()
    return jsonify(1)

@app.route('/_get_microservices/')
def _get_microservices():
    service_id = request.args.get('service', '01', type=str)
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name from microservices where service_id=%s",service_id)
        choices = cur.fetchall()

    choices_data = [(-1,'Select Microservice')]
    for i in choices:
        choices_data += [(i['id'],i['name'])]
        print(i['id'],i['name'])
    return jsonify(choices_data)

@app.route('/gentasks', methods=['GET','POST'])
def genTasks():
    form = GenerateTasks(request.form)
    if(request.method == 'POST' and form.validate()):
        noTasks = form.noOfTasks.data
        periodRangeFrom = form.periodRangeFrom.data
        periodRangeTo = form.periodRangeTo.data
        timeRangeFrom = form.timeRangeFrom.data
        timeRangeTo = form.timeRangeTo.data
        execRangeTo = form.execRangeFrom.data
        execRangeFrom = form.execRangeTo.data


        global data
        file_headers = ['Tasks No', 'Period', 'Execution Time', 'Start Time', 'Deadline', 'Urgency']
        data.append(file_headers)



        file = open( 'tasks.csv', 'w' , newline='')
        writer = csv.writer( file, delimiter=',', quotechar='"' )



        overhead = 0
        while(True):
            overhead += 1
            hyp = []
            data = []
            data.append( file_headers )
            for i in range( 0, int( noTasks ) ):
                period = random.randint( int( periodRangeFrom ), int( periodRangeTo ) )
                if(int(execRangeFrom) < period):
                    executiontime = random.randint( int( execRangeTo ), int(execRangeFrom) )
                else:
                    executiontime = random.randint( int( execRangeTo ), int( period ) )
                    executiontime = executiontime - 1

                starttime = 0
                deadline = period
                hyp.append(period)

                urgency = random.randint( int( 0 ), int( 1 ) )
                data.append([str(i+1), str(period), str(executiontime), str(starttime), str(deadline), str(urgency)])

            hyperperiod = lcm(hyp)
            print (hyperperiod)

            if(hyperperiod < 500):
                break


        print (overhead);
        print ('o====h')
        print (hyperperiod)


        writer.writerows(data)
        data = []
        file.close()

        flash("Tasks Generated Successfully!!",'success')
        redirect(url_for('index'))
    return render_template("gentasks.html", form=form)




@app.route('/edittask')
def editTask():
    hyperperiod, task_types, total_tasks = _tasksReaderDB( 'tasks.csv' )
    return render_template("edittask.html", **locals())

def getKey(obj):
    return obj.Tno

@app.route('/ratemonotonic')
def rateMono():

    page_title = "Arrival Based Scheduling"

    hyperperiod,task_types, total_tasks = _tasksReaderDB()

    html_color = {'Core1': 'red', 'Core2': 'blue', 'Core3': 'green', 'Core4': 'aqua', 'Empty': 'grey',
                  'Finish': 'black'}

    tasks = []
    line = []
    total = 0
    # Create task instances
    task_types = sorted(task_types, key=getKey)
    for i in np.arange( 0, int(hyperperiod) ):
        for task_type in task_types:

            if(task_type.period != 0 ):
                _cond = (int(i) - int(task_type.release)) % int(task_type.period)

                if (_cond == 0 and int(i) >= int(task_type.release)):
                    start = i
                    end = start + task_type.execution
                    priority = task_type.urgency
                    deadline = start + task_type.deadline
                    Task_no = task_type.Tno
                    vo_name = task_type.vo
                    # We make some attributes 0 because these are not required in this protocol
                    tasks.append( TaskIns( start=start, end=end, priority=priority, name=task_type.name, deadline=deadline,
                                           Tno=Task_no,pD=0, pP=0, pS=0, pE=0, urgency=0, vo=vo_name, pB=0) )
                    total = total + task_type.execution



    core = round( total / float( hyperperiod ) )


    print ("Least No of Cores Needed: " + str( core ))


    # Check if the tasks are schedulable

    process_utilization = total_tasks*(2**(1/total_tasks)-1)


    cpu_utilization = 0
    for task_type in task_types:
        if(task_type.period != 0):
            cpu_utilization += float( task_type.execution ) / float( task_type.period )

    if(cpu_utilization < process_utilization):
        print ("all tasks are schedulable")

    if cpu_utilization > 1:
        a = 1
        error = True
        error_msg = "utilization greater than 1, so some tasks will not be able to reach deadline"
       # return render_template( "ratemono.html", **locals() )

    hyperperiod = int (hyperperiod)

    clock_step = 1
    html = ''
    task_timeline = []

    cpu_tasks = []
    for i in np.arange( 0, hyperperiod, clock_step ):
        # Fetch possible tasks that can use cpu and sort by priority
        possible = []
        for t in tasks:
            if t.start <= i:
                possible.append( t )
        possible = sorted( possible, key=cmp_to_key(priority_cmp) )

        # Select task with highest priority

        if len( possible ) > 0:
            on_cpu = possible[0]
            print (on_cpu.get_unique_name(), " uses the processor. ")
            html += '<div class="wrapper"><div class="counter">'+ str(i) +'~'+ str(i+1) +' </div><div class="cpu_used" data-toggle="modal" data-target="#myModal">' + on_cpu.get_unique_name() + '</div></div>'
            cpu_tasks.append({'cpu_time':i,'task_instance':on_cpu})
            task_timeline.append({'cpu_time':i,'task_instance':on_cpu})
            if on_cpu.use( clock_step ):
                tasks.remove( on_cpu )
                print ("Finish!")
        else:
            print ('No task uses the processor. ')
            task_timeline.append( {'cpu_time': i, 'task_instance': None} )
            html += '<div class="wrapper"><div class="counter">'+ str(i) +'~'+ str(i+1) +' </div><div class="cpu_empty">Empty</div></div>'
            print ("\n")
    #Print remaining periodic tasks
    html += "<br /><br />"
    s1 = on_cpu.name
    for t in task_types:
        s2 = t.name.rstrip()
        if s1 == s2:
            ET = (i) - on_cpu.start
            if t.RT > ET or t.RT == -1:
                t.RT = ET

            if i <= on_cpu.priority_deadline:
                t.times += 1
            else:
                t.missed += 1

    for p in tasks:
        print (p.get_unique_name() + " is dropped due to overload!")
        html += "<p>" + p.get_unique_name() + " is dropped due to overload!</p>"





    return render_template("fef.html", **locals())


def _getUrgencyFromClass(priority_string):
    if(priority_string == "Normal Periodic"):
        return 0
    if (priority_string == "High Priority Periodic"):
        return 1
    if (priority_string == "Normal Event Driven"):
        return 2
    if (priority_string == "High Urgency Event Driven"):
        return 3
    return -1

def _prepareTaskInstances(hyperperiod, task_types, tasks, total):
    instance_data = []

    file_headers = ['Instance Id','Tasks No', 'Start', 'End', 'Priority', 'Task Name', 'Urgency', 'Priority Deadline', 'Priority Period',
                    'Priority Slack', 'Priority Execution',  'Sensing Output']
    instance_data.append(file_headers)

    file = open("instances.csv", 'w', newline='')
    writer = csv.writer(file, delimiter=',', quotechar='"')

    for i in np.arange(0, hyperperiod):
        for task_type in task_types:
            # check if its event driven tasks
            vo_name = task_type.vo
            if task_type.period == 0 and i == task_type.release:

                Task_no, end, pD, pE, pP, pS, priority, start, urgency, i_output = _createTaskInstances(i, task_type)

                task_instance = TaskIns(start=start, end=end, priority=priority, name=task_type.name, urgency=urgency, pD=pD,
                            pP=pP, pS=pS, pE=pE, Tno=Task_no, deadline=task_type.deadline, i_out=i_output,pB=0,vo=vo_name)
                tasks.append(task_instance)
                instance_data.append([str(task_instance.id), str(task_instance.Tno), str(task_instance.start),
                                     str(task_instance.end),
                                     str(task_instance.priority), str(task_instance.name), str(task_instance.urgency),
                                     str(task_instance.priority_deadline),
                                     str(task_instance.priority_period), str(task_instance.priority_slack), str(task_instance.priority_exec),
                                     str(task_instance.i_out)])
                total = total + task_type.execution
            # In case tasks are periodic
            elif task_type.period != 0:
                if (i - task_type.release) % task_type.period == 0 and i >= task_type.release:
                    Task_no, end, pD, pE, pP, pS, priority, start, urgency, i_output = _createTaskInstances(i, task_type)

                    task_instance = TaskIns(start=start, end=end, priority=priority, name=task_type.name, urgency=urgency, pD=pD,
                                pP=pP, pS=pS, pE=pE, deadline=task_type.deadline, Tno=Task_no,i_out=i_output,pB=0, vo=vo_name)
                    tasks.append(task_instance)
                    instance_data.append([str(task_instance.id), str(task_instance.Tno), str(task_instance.start), str(task_instance.end),
                                 str(task_instance.priority), str(task_instance.name), str(task_instance.urgency), str(task_instance.priority_deadline),
                                         str(task_instance.priority_period), str(task_instance.priority_slack),
                                         str(task_instance.priority_exec), str(task_instance.i_out)])
                    #print(event_instance.start, event_instance.id)

                    total = total + task_type.execution

    print(instance_data)
    writer.writerows(instance_data)
    instance_data = []
    file.close()
    return total


def _createTaskInstances(i, task_type):
    start = i
    end = start + task_type.execution
    priority = start + task_type.deadline
    urgency = task_type.urgency
    Task_no = task_type.Tno
    pD = start + task_type.deadline
    pP = task_type.period
    pS = (start + task_type.deadline) - (start + task_type.execution)
    pE = task_type.execution
    i_out =  random.randint(10, 100)
    return Task_no, end, pD, pE, pP, pS, priority, start, urgency, i_out



@app.route('/fef')
def fef():
    # Variables
    # html_color = { 'Task1':'red', 'Task2':'blue', 'Task3':'green', 'Task4':'aqua', 'Task5':'coral', 'Empty':'grey', 'Finish':'black'}
    global scenarios
    global sampling
    filename = request.args.get("filename")
    page_title = "Priority Based Hybrid Scheduling"
    html_color = {'Core1': 'red', 'Core2': 'blue', 'Core3': 'green', 'Core4': 'aqua', 'Empty': 'grey',
                  'Finish': 'black'}
    scenario_id = request.args.get('scenario_id')
    task_types = []
    tasks = []
    hyperperiod = []
    No = 0

    hyperperiod, task_types, No = _tasksReaderDB()



   # package_dir = os.path.dirname(os.path.abspath(__file__) + "/files/")
   # thefile = os.path.join(package_dir, filename)


    #print ("Hyper period: " + str( hyperperiod ))


    total = 0
    # Create task instances

    # This function goes through all the task typers and create task instances and return total instances.
    total = _prepareTaskInstances(hyperperiod, task_types, tasks, total)

    # Suggest No of Procesors
    # print "HP: " + str(HP)
    # print "Required: " +str(total)
    core = round( total/hyperperiod )
    print ("Least No of Cores Needed: " + str( core ))

    # Html output start
    html = "<!DOCTYPE html><html><head><title>EDF Scheduling</title></head><body>"

    # Simulate clock
    clock_step = 1
    res = 1
    PF = 0  # processor utilization
    MissedDeadline = []
    task_timeline = []
    cpu_tasks = []

    for i in np.arange( 0, hyperperiod, clock_step ):  # hyperperiod -> 6
        # Fetch possible tasks that can use cpu and sort by priority
        possible = []
        Periodic = []
        Periodic_Period = []
        Periodic_Deadline = []
        Periodic_Slack = []
        Event = []
        Event_Urgency = []
        Event_Deadline = []
        Event_Slack = []
        FM = 0

        Event_SameUrgenecy = []
        Event_SameDeadline = []

        MightSafe = []

        for t in tasks:
            if t.start <= i:
                possible.append( t )
                if t.urgency > 1:
                    if int(float(t.urgency)) == 2:
                        Event.append( t )
                    else:
                        Event_Urgency.append( t )
                else:
                    Periodic.append( t )


        possible = sorted( possible, key=cmp_to_key(priority_cmp) )
        Periodic = sorted( Periodic, key=cmp_to_key(priority_cmp) )
        Periodic_Deadline = sorted( Periodic, key=cmp_to_key(priority_cmp_deadline) )
        Periodic_Period = sorted( Periodic, key=cmp_to_key(priority_cmp_period) )
        Periodic_Slack = sorted( Periodic, key=cmp_to_key(priority_cmp_slack) )

        Event_Deadline = sorted( Event, key=cmp_to_key(priority_cmp_deadline) )
        Event_Urgency = sorted( Event_Urgency, key=cmp_to_key(priority_cmp_Urgency) )
        Event_Slack = sorted( Event, key=cmp_to_key(priority_cmp_slack) )

        if i == 0:
            print ("\n")
            print ("Arrived Tasks at time: " + str( i ))

            print ("Event_Urgency: ")
            for j3 in range( 0, len( Event_Urgency ) ):
                print ("    " + str( Event_Urgency[j3] ))

            print ("Event: ")
            for j1 in range( 0, len( Event ) ):
                print ("    " + str( Event[j1] ))

            print ("Periodic: ")
            for j2 in range( 0, len( Periodic ) ):
                print ("    " + str( Periodic[j2] ))
            print ("\n")

        NoCores = 1

        for j in range( 0, NoCores ):
            # Select task with highest priority

            if len( possible ) > 0:
                if len( Event ) > 0 or len( Event_Urgency ) > 0:
                    if len( Event_Urgency ) > 0:
                        if len( Event_Urgency ) == 1:
                            on_cpu = Event_Urgency[0]
                        else:
                            TempDeadline = []
                            TempDeadline = sorted( Event_Urgency, key=cmp_to_key(priority_cmp_deadline) )
                            Event_SameDeadline.append( TempDeadline[0] )
                            for k in range( 1, len( TempDeadline ) ):
                                if (TempDeadline[0].priority_deadline == TempDeadline[k].priority_deadline):
                                    Event_SameDeadline.append( TempDeadline[k] )
                            if len( Event_SameDeadline ) > 1:
                                TempArrival = []
                                TempArrival = sorted( Event_SameDeadline, key=cmp_to_key(priority_cmp_arrival) )
                                on_cpu = TempArrival[0]
                            else:
                                on_cpu = TempDeadline[0]
                    else:
                        if len( Periodic ) > 0:  #########################################
                            if (Event_Slack[0].priority_slack >= (2 * (Periodic_Slack[0].priority_slack))):  ##
                                on_cpu = Periodic_Slack[0]  ##       Urgency Calculation;
                            else:  ## threshold can be changed with survey
                                on_cpu = Event_Slack[0]  ##

                elif len( Event_Urgency ) == 0:
                    if len( Periodic ) > 0:
                        Periodic_Deadline = sorted( Periodic, key=cmp_to_key(priority_cmp_deadline) )
                        Periodic_Period = sorted( Periodic, key=cmp_to_key(priority_cmp_period) )
                        Periodic_Slack = sorted( Periodic, key=cmp_to_key(priority_cmp_slack) )
                        MightMiss = []
                        Periodic_SameDeadline = []
                        Periodic_SameSlack = []
                        Periodic_SamePeriod = []

                        m = len( Periodic_Deadline )
                        FD = Periodic_Deadline[m - 1].priority_deadline

                        for k1 in range( 0, m ):
                            if (Periodic[k1].priority_slack < 1):
                                MightMiss.append( Periodic[k1] )
                            else:
                                MightSafe.append( Periodic[k1] )

                        TotalExec = i

                        for t in tasks:
                            if (t.end - 3) < FD:  # -3 added to consider deadlines at the edge
                                TotalExec = TotalExec + t.priority_exec

                        if (TotalExec > FD):
                            FM = 1

                        if FM == 0 and len( MightMiss ) > 0:
                            print ("FD: " + str( FD ))
                            print ("TotalExec: " + str( TotalExec ))
                            if (len( MightMiss ) == 0):
                                on_cpu = MightMiss[0]
                            else:
                                MightMiss = sorted( MightMiss, key=cmp_to_key(priority_cmp_slack) )
                                Periodic_SameSlack.append( MightMiss[0] )
                                for k3 in range( 1, len( MightMiss ) ):
                                    if (MightMiss[0].priority_slack == MightMiss[k3].priority_slack):
                                        Periodic_SameSlack.append( MightMiss[k3] )
                                if len( Periodic_SameSlack ) > 1:
                                    TempPeriod = []
                                    TempPeriod = sorted( Periodic_SameSlack, key=cmp_to_key(priority_cmp_period ))
                                    on_cpu = TempPeriod[0]
                                else:
                                    on_cpu = MightMiss[0]
                        else:
                            if len( Periodic_Period ) > 1:
                                Periodic_SamePeriod.append( Periodic_Period[0] )
                                for k4 in range( 1, len( Periodic_Period ) - 1 ):
                                    if (Periodic_Period[0].priority_period == Periodic_Period[k4].priority_period):
                                        Periodic_SamePeriod.append( Periodic_Period[k4] )
                                if len( Periodic_SamePeriod ) > 1:
                                    TempArrival = []
                                    TempArrival = sorted( Periodic_SamePeriod, key= cmp_to_key(priority_cmp_arrival) )
                                    on_cpu = TempArrival[0]
                                else:
                                    on_cpu = Periodic_Period[0]
                            else:
                                on_cpu = Periodic_Period[0]


                on_cpu.priority_exec -= 1
                for t in tasks:
                    if t.start <= i:
                        if t.priority_slack != 0:
                            t.priority_slack -= 1



                #print(on_cpu.deadline, on_cpu.urgency)
                if(on_cpu.priority_period == 0 and on_cpu.urgency == 1):
                    cls = "urgent-event"
                if (on_cpu.priority_period == 0 and on_cpu.urgency == 0):
                    cls = "normal-event"
                if (on_cpu.priority_period != 0 and on_cpu.urgency == 1):
                    cls = "urgent-periodic"
                if (on_cpu.priority_period != 0 and on_cpu.urgency == 0):
                    cls = "normal-periodic"

                html += '<div class="wrapper"><div class="counter">'+ str(i) +'~'+ str(i+1) +' </div><div class="cpu_used '+cls+'">' + on_cpu.get_unique_name()  +  '</div>'
                cpu_tasks.append( {'cpu_time': i, 'task_instance': on_cpu} )
                task_timeline.append( {'cpu_time': i, 'task_instance': on_cpu} )

                if on_cpu.use( clock_step ):
                    tasks.remove( on_cpu )
                    possible.remove( on_cpu )
                    if on_cpu.urgency > 1:
                        if on_cpu.urgency == 2:
                            Event.remove( on_cpu )
                        else:
                            Event_Urgency.remove( on_cpu )
                    else:
                        Periodic.remove( on_cpu )

                    s1 = on_cpu.name
                    for t in task_types:
                        s2 = t.name.rstrip()
                        if s1 == s2:
                            ET = (i) - on_cpu.start
                            if t.RT > ET or t.RT == -1:
                                t.RT = ET

                            if i <= on_cpu.priority_deadline:
                                t.times += 1
                            else:
                                t.missed += 1

                html += '</div>'

                if i > on_cpu.priority_deadline:
                    MissedDeadline.append( on_cpu )
                    # print "...... Missed Deadline...."
                    # print on_cpu


            else:
                print ('No task uses the processor. ')
                html += '<div class="wrapper"><div class="counter">'+ str(i) +'~'+ str(i+1) +' </div><div class="cpu_empty">Empty</div></div>'
                task_timeline.append( {'cpu_time': i, 'task_instance': None} )
                PF = PF + 1;  # processor free
                # print "\n"
    count = 0
    missedD = 0
    # Print remaining periodic tasks
    html += "<br /><br />"
    for p in tasks:
        if p.priority <= hyperperiod:
            # print p.get_unique_name() + " is dropped due to overload!  " + str(p.start) +" "+ str(p.priority)+" "+str(p.end)
            count = count + 1

    if len( MissedDeadline ) > 0:
        missedD = len( MissedDeadline )
        print ("Missed Deadlines = " + str( missedD ))

    print ("Tasks Missed: " + str( count ))
    print ("\n")

    # Print Task Schedulability
    html += "<br /><br />"
    if count == 0:
        print ("Task is Schedulable")
        html += "<p> Task is Schedulabl!</p>"
    else:
        print ("Task is NOT Schedulable")
        html += "<p> Task is NOT Schedulabl!</p>"

    print ("\n")

    # Print Processor Utilization
    html += "<br />"

    if PF == 0:
        print ("Processor was free " + str( PF ) + " units of time")
        print ("Processor Utlization = 100%")
        html += "Processor was free " + str( PF ) + " units of time <br />"
        html += "Processor Utlization = 100%"
    else:
        print ("Processor was free " + str( PF ) + " units of time \n")
        html += "Processor was free " + str( PF ) + " units of time <br />"

    print ("\n")

    # No of times ech task ran
    for t in task_types:
        print (str( t.name.rstrip() ) + " completed " + str( t.times ) + " times during the hyper-period")
        html += "<p>" + t.name + " completed " + str( t.times ) + " times during the hyper-period</p>"
    for t in task_types:
        print (str(t.name.rstrip()) + " missed " + str(t.missed) + " times during the hyper-period")
        html += "<p>" + t.name + " missed " + str(t.missed) + " times during the hyper-period</p>"
    task_labels = []
    task_rt = []
    #icolor = palette.Color("#aaaa00")
    #bg_color = ["#aaaa00"]
    for t in task_types:
        print (str(t.Tno) + " response time: " + str(t.RT))
        #response_time.append({'id':t.Tno, 'rt':t.RT})
        task_labels.append(t.name)
        task_rt.append(t.RT)
        #icolor.rgb8.r = (icolor.rgb8.r + 10) % 255
        #icolor.rgb8.g = (icolor.rgb8.g -10) % 255
        #icolor.rgb8.b = (icolor.rgb8.b + 10) % 255

        #bg_color.append(icolor.hex)

        html += "<p>" + t.name + " response time: " + str(t.RT) + " </p>"

        task_types = sorted(task_types, key=getKey)

    # Html output end
    html += "</body></html>"

    return render_template("fef.html", **locals())

@app.route('/help')
def help():
    return render_template("help.html")

#################### Utility Functions######################################
def  _tasksReader(fileName):
    if os.path.isfile(fileName) == 0:
        return 0

    file =  open( fileName, 'rt' )
    task_types = []
    hyperperiod = []
    try:
        reader = csv.reader(file)
        i=0;
        total_tasks = 0
        for row in reader:
            if(i > 0):
            # temp_p = int(row(1))
            # if(temp_p > 0):
            #     hyperperiod.append(temp_p)

                if(int(row[1]) > 0):
                    hyperperiod.append(int(row[1]))
                task_types.append(TaskType(period=int(row[1]), release=int(row[3]), execution=int(row[2]), deadline=int(row[4]), name='task'+row[0], time=0,
                                           Tno=int(row[0]), missed=0, urgency=row[5]))

            i = i+1
            total_tasks = total_tasks + 1
    finally:

        hyperperiod = lcm(hyperperiod)
        task_types = sorted( task_types, key=cmp_to_key( tasktypes_cmp ) )
        file.close()
    return hyperperiod,task_types, total_tasks
############################################################################

#################### Utility Functions######################################
def  _tasksReaderDB():
    task_types = []
    hyperperiod = []
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT mt.task_id, mt.vo_id, t.title, t.priority, t.arrival, t.period, t.execution, t.deadline, v.name FROM `mapped_task` mt INNER JOIN tasks t ON mt.task_id = t.id INNER JOIN virtualobjects v ON mt.vo_id = v.id ")
        tasks = cur.fetchall()

        i=0
        total_tasks = 0
        for row in tasks:
            if(int(row['period']) > 0):
                hyperperiod.append(int(row['period']))
            task_types.append(TaskType(period=int(row['period']), release=int(row['arrival']), execution=int(row['execution']),
                                       deadline=int(row['deadline']), name=row['title'], time=0,
                                       Tno=int(row['task_id']), vo=row['name'], missed=0, urgency=(row['priority'])))
            total_tasks = total_tasks + 1
    finally:

        hyperperiod = lcm(hyperperiod)
        task_types = sorted( task_types, key=cmp_to_key( tasktypes_cmp ) )

    return hyperperiod,task_types, total_tasks

if(__name__ == '__main__'):
    app.run(debug=True)