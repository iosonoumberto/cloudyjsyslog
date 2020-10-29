import os
import subprocess
import shutil
import yaml
from jinja2 import Template
import supportlib

from jnpr.junos import Device
from jnpr.junos.exception import *
from jnpr.junos.utils.config import Config

sd=os.getcwd()

fi=open('stack_conf.yaml','r')
sconf = yaml.load(fi, Loader=yaml.FullLoader)
fi.close()

if os.path.isdir(sconf['working_path']):
    print("CLEAN")
    os.chdir(sconf['working_path'])
    subprocess.run(["docker-compose", "down"])
    os.chdir(sd)
    shutil.rmtree(sconf['working_path'])

os.mkdir(sconf['working_path'])
os.mkdir(sconf['working_path']+"/grafana_data")
os.mkdir(sconf['working_path']+"/grafana_data/dashboards")
os.mkdir(sconf['working_path']+"/grafana_prov")
os.mkdir(sconf['working_path']+"/grafana_prov/dashboards")
os.mkdir(sconf['working_path']+"/grafana_prov/datasources")
os.mkdir(sconf['working_path']+"/influxdb_data")
os.mkdir(sconf['working_path']+"/fluentd")

shutil.copyfile('support_files/Dockerfile_fluentd',sconf['working_path']+"/fluentd/Dockerfile")
shutil.copyfile('support_files/dash_prov.yml',sconf['working_path']+"/grafana_prov/dashboards/all.yml")

supportlib.create_file('docker-compose.yml',sconf,"")
supportlib.create_file('dash_definition.json',sconf,"grafana_data/dashboards/")
supportlib.create_file('datasource_definition.yml',sconf,"grafana_prov/datasources/")
supportlib.create_file('fluent.conf',sconf,"")

os.chdir(sconf['working_path'])
subprocess.run(["docker-compose", "up", "-d"])
os.chdir(sd)

for d in sconf['devices']:
    dev=Device(host=d['ip'], user=d['user'], password=d['pass'])
    try:
        dev.open()
    except ConnectError as err:
        print ("ERROR Cannot connect to device: {0}".format(err))
        exit()
    except Exception as err:
        print ("ERROR while connecting to device - " + str(err))
        exit()
    try:
        cfg=Config(dev, mode='private')
    except Exception as err:
        print("[ERROR] Cannot open configuration - " + str(err))
        dev.close()
        sys.exit()
    try:
        cfg.lock()
    except Exception as err:
        print("[ERROR] Cannot lock configuration - " + str(err))
        dev.close()
        sys.exit()
    logvars= { 'log_server' : sconf['log_server'], 'src_log' : d['src']}
    cfg.load(template_path=str('jinja_templates/junos.conf.j2'), template_vars=logvars, format='set')
    try:
        cfg.commit(comment="Device sending log to cloudyjsyslog")
    except Exception as err:
        print("[ERROR] Cannot commit configuration - " + str(err))
        print("[ERROR] Rollback and exit")
        cfg.rollback()
        dev.close()
        sys.exit()
    dev.close()
