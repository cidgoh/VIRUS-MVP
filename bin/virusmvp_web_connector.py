import requests
import base64
import configparser
import sys
import argparse
import os





def create_wordpress_post(config_file, title, content):

    config = configparser.ConfigParser()
    config.read(config_file)

    # Read from the configuration
   
    password = config['DEFAULT']['password']
    api_url = config['DEFAULT']['api_url']
    category_id = config['DEFAULT']['category_id']
    username = config['DEFAULT']['username']
    password = config['DEFAULT']['password']

    credentials = username + ":" + password
    token = base64.b64encode(credentials.encode()).decode('utf-8')
    header = {'Authorization': 'Basic ' + token}

    # data
    data = {
        'title': title,
        'status': 'publish',
        'content': content,
        'categories': category_id
    }

    response = requests.post(api_url, headers=header, json=data)
    print(response.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='add update to virusmvp', add_help=False)
    parser.add_argument('-t', '--title',  help = "title of the update", required = True)
    parser.add_argument('-c', '--content', help = "Content of the update", required = True)
    parser.add_argument('-r', '--config', help = "Config file")
    args = parser.parse_args()
    if args.config is None and not os.path.isfile("config.ini"):
        print('\n'+'Error: please provide a configue file'+'\n')    
        parser.print_help()
        sys.exit()
    if args.config: 
        config_file = args.config
    else: 
        config_file = "config.ini"

    create_wordpress_post(config_file, args.title, args.content)

