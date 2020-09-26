$ python -m venv env
$ source env/bin/activate
(env) $ pip install -r requirements.txt

(env) $ python
>>> from main import db
>>> db.create_all()
>>> exit()



assumption: if user updates their order, the time is updated