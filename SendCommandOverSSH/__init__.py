import logging, json
import azure.functions as func
import paramiko, threading, time, urllib.request

strdata=''
fulldata=''

class ssh:
    shell = None
    client = None
    transport = None
 
    def __init__(self, address, username, password):
        print("Connecting to server on ip", str(address) + ".")
        self.client = paramiko.client.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        self.client.connect(address, username=username, password=password, look_for_keys=False)
        self.transport = paramiko.Transport((address, 22))
        self.transport.connect(username=username, password=password)
 
        thread = threading.Thread(target=self.process)
        thread.daemon = True
        thread.start()
 
    def closeConnection(self):
        if(self.client != None):
            self.client.close()
            self.transport.close()
 
    def openShell(self):
        self.shell = self.client.invoke_shell()
 
    def sendShell(self, command):
        if(self.shell):
            self.shell.send(command + "\n")
        else:
            print("Shell not opened.")

    def readOutput(self) -> str:
        if(self.shell) and self.shell.recv_ready():
                fulldata = self.shell.recv(1024)
                while self.shell.recv_ready():
                    fulldata += self.shell.recv(1024)
        else:
            print("Shell not opened.")
            fulldata = ''
        return fulldata

    def process(self):
        global connection
 
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Extracting the parameters out of the JSON body
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Your body does not look to be correct JSON", status_code=400)
    else:
        hostname = req_body.get('hostname')
        username = req_body.get('username')
        password = req_body.get('password')
        try:
            commands = req_body.get('commands')
        except:
            commands = []
        try:
            prepend_commands = req_body.get('prepend_commands')
        except:
            prepend_commands = []
        try:
            append_commands = req_body.get('append_commands')
        except:
            append_commands = []
        try:
            wait_for_output = req_body.get('wait_for_output')
        except:
            wait_for_output = "false"
        try:
            commands_file_url = req_body.get('commands_file_url')
        except:
            commands_file_url = ''
        try:
            translation_dictionary = req_body.get('translation_dictionary')
        except:
            translation_dictionary = []

    # Verify that the minimum required arguments have been supplied
    if hostname and username and password and (commands or translation_dictionary):

        # If there are no explicit commands, there has to be a URL to a config file
        if not commands:
            try:
                data = urllib.request.urlopen(commands_file_url).read()
                text = data.decode('utf-8')
                commands = text.split('\n')
            except Exception as e:
                # 400: file could not be found
                return func.HttpResponse("File " + commands_file_url + " could not be downloaded. Error: " + str(e), status_code=400)

        # Check for append/prepend.
        # One example of prepend commands could be ['config t']
        # One example of append commands would be ['exit', 'write running-config'] 
        if prepend_commands:
            commands = prepend_commands + commands
        if append_commands:
            commands = commands + append_commands
        
        # Connect to the SSH host
        connection = ssh(hostname, username, password)
        connection.openShell()

        # Issue one command after each other, and pause to read the output if required
        function_output=[]
        for command in commands:
            # Translate any tokens in the translation dictionary
            for word in translation_dictionary:
                command = command.replace(word['old'], word['new'])
            logging.info('Executing command: ' + command)
            connection.sendShell(command)
            # Only pause and read the output if wait_for_output is true.
            # Otherwise the command output will not be returned
            if wait_for_output == 'true':
                # 1 second is typically enough. This should probably be parametrized
                time.sleep(1)
                fulldata = connection.readOutput()
                fulldata_str = str(fulldata)
                # The characters in the output probably depend on the SSH host
                fulldata_str = fulldata_str.replace('\\r', '')
                fulldata_lines = fulldata_str.split('\\n')
                logging.info('Output received: ' + fulldata_str)
            else:
                fulldata_lines=[]
            # The output will contain the command executed after tokenization, and optionally its output
            function_output.append({"command": command, "output": fulldata_lines})
        # If we came down to here, it is a 200
        return func.HttpResponse(json.dumps(function_output))
    else:
        # 400: insufficient parameters passed on
        return func.HttpResponse(
             "Please pass a hostname, username and password on the query string or in the request body",
             status_code=400
        )
