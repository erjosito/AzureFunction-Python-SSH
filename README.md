# Python Function to send commands over SSH

This function sends commands specified in the body of a POST message (either explicitly or referenced by a URL), optionally returning the command output.

Additionally you can tokenize your configuration, so that you can replace those tokens in real time.

Especially useful for configuring Network Virtual Appliances deployed in the public cloud.

## Deploy to Azure

You can deploy Azure Functions in multiple ways, here what I would consider to be the simplest

1. Fork and clone this repository to your computer
2. Open with with Visual Studio (make sure you fulfill [these prerequisites](https://docs.microsoft.com/en-us/azure/azure-functions/tutorial-vs-code-serverless-python#prerequisites))
3. Deploy using [these instructions](https://docs.microsoft.com/en-us/azure/azure-functions/tutorial-vs-code-serverless-python#deploy-to-azure-functions)

## Usage

Here some examples of JSON payloads to send:

### 1. Specify commands to issue explicitly and wait for the output

Use this for sending a series of commands and returning the output of each of them

```json
{
  "hostname": "1.2.3.4",
  "username": "myuser",
  "password": "mypassword",
  "wait_for_output": "true",
  "commands": [
    "show ip version",
    "show ip interface brief"
  ]
}
```

### 2. Reference to a configuration stored in an URL

Use this for sending a series of commands stored in a configuration file referenced by a URL. Note that you can additionally issue commands that will be prepended to the lines downloaded from the URL.

```json
{
  "hostname": "1.2.3.4",
  "username": "myuser",
  "password": "mypassword",
  "commands_file_url": "https://yoururl.com/configuration.txt",
  "prepend_commands": [
    "config t"
  ]
}
```

### 3. Reference to a configuration stored in an URL and replace tokens

Similar to the previous case, but your configuration file contains tokens that are replaced in real time.

```json
{
  "hostname": "1.2.3.4",
  "username": "myuser",
  "password": "mypassword",
  "commands_file_url": "https://yoururl.com/configuration.txt",
  "prepend_commands": [
    "config t"
  ],
  "translation_dictionary": [
    {
      "old": "**IP_ADDRESS**",
      "new": "1.2.3.4"
    }
  ]
}
```

## Application settings

No application settings required.

## Running Locally

Visual Studio function app project is included.
