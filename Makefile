init:
	python3 -m venv .venv
	. .venv/bin/activate && pip3 install -r requirements.txt

test:
	. .venv/bin/activate && nosetests tests

clean:
	rm -rf .venv
