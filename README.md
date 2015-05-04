# Opengrid website

Opengrid website. Needs flask (http://flask.pocoo.org/).

## Installation on the droplet

Install uWSGI:

    apt-get install uwsgi uwsgi-plugin-python

Configure it by adapting the path in the file opengrid.uwsgi.ini and then:

 * Copy the file to /etc/uwsgi/apps-available/opengrid.ini
 * Symlink it in /etc/uwsgi/apps-enabled

Flask will be run as the user www-data, therefore the following needs to be taken care of:

 * Make sure the root path is rw by www-data, e.g.:
```
# ls -ld /usr/local/src/website/
drwxrwxr-x 5 root www-data 4096 May  4 19:54 /usr/local/src/website
```
 * Make sure /path/to/hp_anonymous.pkl is writeable by www-data, e.g.:
```
# ls -ld /usr/local/src/website/hp_anonymous.pkl 
-rw-rw-r-- 1 root www-data 40472 May  4 19:47 /usr/local/src/website/hp_anonymous.pkl
```

Start uWSGI:

    # service uwsgi start opengrid

Configure nginx by putting the following lines in the `server` block 
of `/etc/nginx/sites-available/default`:

    location / {
    	# First attempt to serve request as file, then
    	# pass it to flask 
    	try_files $uri @opengrid-flask;
    	autoindex on;
    }
    
    location @opengrid-flask {
      include uwsgi_params;
      uwsgi_pass unix:/var/run/uwsgi/app/opengrid/socket;
    }
    
    # Serve /static/ from the directory of the website
    location /static/ {
      root /usr/local/src/website;
    }

Make sure the path to the website's code correct.

