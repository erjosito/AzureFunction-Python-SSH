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

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            "Your body does not look to be correct JSON",
            status_code=400
        )
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

    if hostname and (commands or translation_dictionary):
        # ssh = paramiko.SSHClient()
        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ssh.connect(hostname, username=username, password=password)
        # function_output=[]
        # for command in commands:
        #     logging.info('Executing command: ' + command)
        #     command_output = []
        #     try:
        #         (stdin, stdout, stderr) = ssh.exec_command(command)
        #         lines=stdout.readlines()
        #         logging.info('Output received: ' + str(lines))
        #         for line in lines:
        #             command_output.append(line)
        #     except:
        #         command_output = "error"
        #     function_output.append({"command": command, "output": command_output})
        # ssh.close()

        strdata=''
        fulldata=''

        if not commands:
            try:
                data = urllib.request.urlopen(commands_file_url).read()
                text = data.decode('utf-8')
                commands = text.split('\n')
            except Exception as e:
                return func.HttpResponse(
                    "File " + commands_file_url + " could not be downloaded. Error: " + str(e),
                    status_code=400
                )
        
        if prepend_commands:
            commands = prepend_commands + commands
        
        connection = ssh(hostname, username, password)
        connection.openShell()
        function_output=[]
        for command in commands:
            for word in translation_dictionary:
                command = command.replace(word['old'], word['new'])
            logging.info('Executing command: ' + command)
            connection.sendShell(command)
            if wait_for_output == 'true':
                time.sleep(1)
                fulldata = connection.readOutput()
                # Split full data in lines
                fulldata_str = str(fulldata)
                fulldata_str = fulldata_str.replace('\\r', '')
                fulldata_lines = fulldata_str.split('\\n')
                logging.info('Output received: ' + fulldata_str)
            else:
                fulldata_lines=[]
            function_output.append({"command": command, "output": fulldata_lines})
            fulldata=''
        return func.HttpResponse(json.dumps(function_output))
    else:
        return func.HttpResponse(
             "Please pass a hostname on the query string or in the request body",
             status_code=400
        )
