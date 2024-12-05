from todoist_api_python.api import TodoistAPI
from flask import Flask, render_template
import paramiko
import json
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from datetime import datetime

with open("config.json", "r") as config_file:
    config = json.load(config_file)

api = TodoistAPI(config["todoist_api_key"])
todoist_project = next((x for x in  api.get_projects() if x.name == config['todoist_project_name']), None)

def connect_client(server):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host = f'{server[1]}@{server[0]}'
    try:
        if server[2] != None:
            print(f"Connecting to {server[0]} as {server[1]} using password {'*' * len(server[2])}")
            client.connect(server[0], username=server[1], password=server[2], timeout=0.5)
        else:
            print(f"Connecting to {server[0]} as {server[1]} using private key {server[3]}")
            private_key = paramiko.RSAKey.from_private_key_file('./keys/' + server[3])
            client.connect(server[0], username=server[1], pkey=private_key, timeout=0.5)
        
        return [host, client]
    except Exception as e:
        print(f"Error while connecting to {server[0]}")
        print(e)
        return [host, None]

shells = []
for server in config['servers']:
    shells.append(connect_client(server))

def disconnect_clients():
    print(f"Disconnecting clients")
    for client in shells:
        if client[1] is not None:
            print(f"Disconnecting from {client[0]}")
            client[1].close()

def client_is_alive(client):
    try:
        transport = client.get_transport()
        transport.send_ignore()
        return True
    except Exception as e:
        # print(f"Client is not active")
        return False

server_data = dict()
tasks_data = []
def update_data():
    global tasks_data
    print(f"Updating tasks data")

    try:
        tasks_data = api.get_tasks(project_id=todoist_project.id)
        tasks_data.sort(key= lambda x: datetime.strptime(x.due.date, "%Y-%m-%d"))       
    except Exception as e:
        print(f"Error while retrieving Todoist tasks")
        print(e)

    print(f"Updating server data")
    for idx, shell in enumerate(shells):
        host = shell[0]

        cpu = "awk '{u=$2+$4; t=$2+$4+$5; if (NR==1){u1=u; t1=t;} else print ($2+$4-u1) * 100 / (t-t1) \"%\"; }' <(grep 'cpu ' /proc/stat) <(sleep 1;grep 'cpu ' /proc/stat)"
        disk = "df -h /"
        docker = 'docker ps -a --format "table <b>{{.Names}}</b> {{.Status}}"'

        if shell[1] is None or not client_is_alive(shell[1]):
            shells[idx] = connect_client(config['servers'][idx]) # smells so bad

        client = shells[idx][1]

        cpu_data = '-'
        disk_data = '-'
        docker_data = "<i style='text-align: center; width:100%; display:inline-block'>Can't connect to server!</i>"

        if client is not None and client_is_alive(client):
            stdin, stdout, stderr = client.exec_command(cpu)
            cpu_data = stdout.read().decode()
            # print(f'CPU: stdout: {cpu_data}, stderr: {stderr.read().decode()}')

            stdin, stdout, stderr = client.exec_command(disk)
            disk_data = stdout.read().decode()
            # print(f'DISK: stdout: {disk_data}, stderr: {stderr.read().decode()}')
            disk_data = disk_data[disk_data.index('\n')+1:].replace('\n', '<br>')

            stdin, stdout, stderr = client.exec_command(docker)
            docker_data = stdout.read().decode()
            # print(f'DISK: stdout: {disk_data}, stderr: {stderr.read().decode()}')
            docker_data = docker_data[docker_data.index('\n')+1:].replace('\n', '<br>')
        else:
            print(f"Can't get data from unconnected server: {host}, skipping")

        server_data[host] = [cpu_data, disk_data, docker_data]

data_update_scheduler = BackgroundScheduler()
data_update_scheduler.add_job(func=update_data, trigger="interval", seconds=config['data_update_timer'])
update_data()
data_update_scheduler.start()
atexit.register(lambda: data_update_scheduler.shutdown())
atexit.register(disconnect_clients)

def get_data_table():
    table = '<div>'

    for host, data in server_data.items():
        cpu_data = data[0]
        disk_data = data[1]
        docker_data = data[2]

        table += f"<h3 style='text-align: center; margin-bottom:0'>{host}</h3>"
        table += f"<p style='width:100%;text-align:center; display: inline-block; margin:0; font-size: small; font-weight: bold'>{disk_data}{cpu_data}</p><p style='font-size: smaller; margin:0; margin-bottom:10px;'>{docker_data}</p>"

    table += '</div>'

    return table

def get_tasks_table():
    table = '<ul>'

    for task in tasks_data:
        table += f'<li><span>{task.content}</span><span style="font-size: initial; float: right">{task.due.string}</span></li>'

    table += '</ul>'

    return table

app = Flask(__name__)
@app.route("/")
def hello_world():
    return render_template('index.html', tasks_table = get_tasks_table(), data_table = get_data_table(), refresh_timer = config['refresh_timer'])
