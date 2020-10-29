from jinja2 import Template
from jnpr.junos import Device
from jnpr.junos.exception import *
from jnpr.junos.utils.config import Config

def create_file(jinja,vars,dest):
    fi=open('jinja_templates/'+jinja+'.j2','r')
    ts=fi.read()
    fi.close()
    t=Template(ts)
    to=t.render(vars)
    fo=open(vars['working_path']+"/"+dest+jinja,'w')
    fo.write(to)
    fo.close()

def config_devices(sconf):
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
