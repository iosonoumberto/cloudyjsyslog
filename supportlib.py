from jinja2 import Template

def create_file(jinja,vars,dest):
    fi=open('jinja_templates/'+jinja+'.j2','r')
    ts=fi.read()
    fi.close()
    t=Template(ts)
    to=t.render(vars)
    fo=open(vars['working_path']+"/"+dest+jinja,'w')
    fo.write(to)
    fo.close()
