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


















# data = {
#         'title': 'Auto Update 2023_09',
#         'status': 'publish',
#         'content': 'This is the content of the post',
#         'excerpt': 'test',
#         'categories':10
#     }



# def create_wordpress_post():
#     api_url = "https://virusmvp.cidgoh.ca/wp-json/wp/v2/posts"
    
#     response = requests.post(api_url, headers=wordpress_header, json=data)
#     print(response.text)

# create_wordpress_post()











# valid_action = ['get', 'post', 'update']
# parser = argparse.ArgumentParser(description='Sequdas data management system', add_help=False)
# parser.add_argument('-a', '--action', choices = valid_action, help ='Choose one of the options: Get, Post, Update')
# parser.add_argument('-r', '--qc_run_level',  action = 'append', help = "Files for run level QC")
# parser.add_argument('-i', '--json_run',  help = "Json file for run information")
# parser.add_argument('-s', '--qc_sample_level', action ='append', help = "Files for sample level QC")
# parser.add_argument('-j', '--json_sample', help = "Json file for sample information")
# parser.add_argument('-t', '--token', help = "Access Token")
# parser.add_argument('-n', '--run_name', help = "Specific Run to pull data from sequdas")
# args = parser.parse_args()




# if args.action is None:
#     print('\n'+'Error: --action argument is required. Please choose get, post or update'+'\n')    
#     parser.print_help()
#     sys.exit()

# if args.token is None:
#     print('\n'+'Error: --token argument is required. Please provide a token'+'\n')    
#     parser.print_help()
#     sys.exit()
    
# if(args.json_run):
#     notes = input('\n'+"Would you like to add any note?"+'\n'+'\n')

# def get_run_info(url, token):
#     http = urllib3.PoolManager()
#     headers = {
#         'Authorization': 'token '+token,
#         'Content-Type': 'application/json'
#     }

#     try:
#         response = http.request(
#             'GET',
#             url, 
#             headers=headers
#         )

#         if response.status >= 200 and response.status < 300:
#             # Successful response
#             json_data = json.loads(response.data.decode('utf-8'))
#             pretty_json = json.dumps(json_data, sort_keys=True, indent=4)
#             print(response.status)
#             print(pretty_json)
#         else:
#             # HTTP error response
#             raise Exception(f'HTTP Error: {response.status}')

#     except urllib3.exceptions.HTTPError as e:
#         # Handle HTTP error
#         print('HTTPError:', e)

#     except Exception as e:
#         # Handle other exceptions
#         print('Error:', e)


# def upload_run_info(run_info, url, token):
#     http = urllib3.PoolManager()
#     headers = {
#         'Authorization': 'token '+token,
#         'Content-Type': 'application/json'
#     }
#     json_data = json.dumps(run_info).encode('utf-8')

#     try:
#         response = http.request(
#             'POST',
#             url, 
#             body = json_data,
#             headers=headers
#         )

#         if response.status >= 200 and response.status < 300:
#             # Successful response
#             print(response.status)
#             print(response.data.decode('utf-8'))
#         else:
#             # HTTP error response
#             raise Exception(f'HTTP Error: {response.status}')

#     except urllib3.exceptions.HTTPError as e:
#         # Handle HTTP error
#         print('HTTPError:', e)

#     except Exception as e:
#         # Handle other exceptions
#         print('Error:', e)



# def upload_files_with_urllib3(run_name, file_list, url, token):
#     http = urllib3.PoolManager()
#     headers = {
#         'Authorization': 'token '+token,
#     }
#     fields = [
#         ('name', run_name)
#     ]
#     url=url+run_name+"/"
#     print(url)
#     for file_path in file_list:
#         with open(file_path, 'rb') as file:
#             fields.append(('runfiles', (file_path, file.read())))
            
#     response = http.request('PATCH', url, fields=fields, headers=headers)
#     print(response.status)



# if(args.action == 'get'):
#     if(args.run_name):
#         url = url+args.run_name
#     get_run_info(url, args.token)


# if(args.action == 'post'):
#     with open(args.json_run, 'r') as file:
#         run_info = json.load(file)
#     if(notes):
#         run_info["description"] = notes 
#     upload_run_info(run_info, url, args.token)
#     if(args.qc_run_level):
#         upload_files_with_urllib3(run_info["name"], args.qc_run_level, url2, args.token)
    

# if(args.action == 'update'):
#     if(args.run_name is None):
#         print("\n"+"You must provide a run name when updating information"+"\n")

    


