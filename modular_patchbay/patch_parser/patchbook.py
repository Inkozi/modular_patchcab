#!/usr/bin/env python3
"""
PATCHBOOK MARKUP LANGUAGE & PARSER
UPDATED VERSION FROM SPECTROAUDIO
"""

import sys
import re
import os
import argparse
import json



class patchParser:

    def __init__(self, debugMode=False, quiet=True):
        # Parser INFO
        self.parserVersion = "c1"

        # Reset main dictionary
        self.mainDict = {
            "info": {"patchbook_version": self.parserVersion},
            "modules": {},
            "comments": []
        }

        # Available connection types
        self.connectionTypes = {
            "->": "audio",
            ">>": "cv",
            "p>": "pitch",
            "g>": "gate",
            "t>": "trigger",
            "c>": "clock"
        }


        # Reset global variables
        self.lastModuleProcessed = ""
        self.lastVoiceProcessed = ""

        self.connectionID = 0

        self.quiet = quiet
        self.debugMode = debugMode

    def clear(self):
        self.mainDict = {
            "info": {"patchbook_version": self.parserVersion},
            "modules": {},
            "comments": []
        }

        self.lastModuleProcessed = ""
        self.lastVoiceProcessed = ""

        self.connectionID = 0


    def parseFile(self, filename):
        # This function reads the txt file and process each line.

        self.clear()
        lines = []
        try:
            if not self.quiet: print("Loading file: " + filename)
            with open(filename, "r") as file:
                for l in file:
                    lines.append(l)
                    self.regexLine(l)
        except TypeError:
            print(filename)
            print("ERROR. Please add text file path after the script.")
        except FileNotFoundError:
            print("ERROR. File not found.")
        if not self.quiet:
            print("File successfully processed.")
            print()

    def regexLine(self, line):

        if self.debugMode:
            print()
        if self.debugMode:
            print("Processing: " + line)

        # CHECK FOR COMMENTS
        if self.debugMode:
            print("Checking input for comments...")
        re_filter = re.compile(r"^\/\/\s?(.+)$")  # Regex for "// Comments"
        re_results = re_filter.search(line.strip())
        try:
            comment = re_results.group().replace("//", "").strip()
            if self.debugMode:
                print("New comment found: " + comment)
                self.addComment(comment)
            return
        except AttributeError:
            pass

        # CHECK FOR VOICES
        if self.debugMode:
            print("Cheking input for voices...")
        re_filter = re.compile(r"^(.+)\:$")  # Regex for "VOICE 1:"
        re_results = re_filter.search(line)
        try:
            # For some reason the Regex filter was still detecting parameter declarations as voices,
            # so I'm also running the results through an if statement.
            results = re_results.group().replace(":", "")
            if "*" not in results and "-" not in results and "|" not in results:
                if self.debugMode:
                    print("New voice found: " + results.upper())
                self.lastVoiceProcessed = results.upper()
                return
        except AttributeError:
            pass

        # CHECK FOR CONNECTIONS
        if self.debugMode:
            print("Cheking input for connections...")
        re_filter = re.compile(
            r"\-\s(.+)[(](.+)[)]\s(\>\>|\-\>|[a-z]\>)\s(.+)[(](.+)[)]\s(\[.+\])?$")
        re_results = re_filter.search(line)
        try:
            results = re_results.groups()
            voice = self.lastVoiceProcessed
            if len(results) == 6:
                if self.debugMode:
                    print("New connection found, parsing info...")
                # results = results[:5]
                self.addConnection(results, voice)
                return
        except AttributeError:
            pass

        # CHECK PARAMETERS
        if self.debugMode:
            print("Checking for parameters...")
        # If single-line parameter declaration:
        re_filter = re.compile(r"^\*\s(.+)\:\s?(.+)?$")
        re_results = re_filter.search(line.strip())
        try:
            # Get module name
            results = re_results.groups()
            module = results[0].strip().lower()
            if self.debugMode:
                print("New module found: " + module)
            if results[1] != None:
                # If parameters are also declared
                parameters = results[1].split(" | ")
                for p in parameters:
                    p = p.split(" = ")
                    self.addParameter(module, p[0].strip().lower(), p[1].strip())
                return
            elif results[1] == None:
                if self.debugMode:
                    print("No parameters found. Storing module as global variable...")
                self.lastModuleProcessed = module
                return
        except AttributeError:
            pass

        # If multi-line parameter declaration:
        if "|" in line and "=" in line and "*" not in line:
            module = self.lastModuleProcessed.lower()
            if self.debugMode:
                print("Using global variable: " + module)
            parameter = line.split(" = ")[0].replace("|", "").strip().lower()
            value = line.split(" = ")[1].strip()
            self.addParameter(module, parameter, value)
            return

    def addConnection(self, list, voice="none"):
        self.connectionID += 1

        if self.debugMode:
            print("Adding new connection...")
            print("-----")

        output_module = list[0].lower().strip()
        output_port = list[1].lower().strip()

        if self.debugMode:
            print("Output module: " + output_module)
            print("Output port: " + output_port)

        try:
            connection_type = self.connectionTypes[list[2].lower()]
            if self.debugMode:
                print("Matched connection type: " + connection_type)
        except KeyError:
            print("Invalid connection: " + list[2])
            connection_type = "cv"

        input_module = list[3].lower().strip()
        input_port = list[4].lower().strip()

        if self.debugMode:
            print("Input module: " + input_module)
            print("Input port: " + output_port)

        self.checkModuleExistence(output_module, output_port, "out")
        self.checkModuleExistence(input_module, input_port, "in")

        if self.debugMode:
            print("Appending output and input connections to mainDict...")

        output_dict = {
            "input_module": input_module,
            "input_port": input_port,
            "connection_type": connection_type,
            "voice": voice,
            "id": self.connectionID}

        input_dict = {
            "output_module": output_module,
            "output_port": output_port,
            "connection_type": connection_type,
            "voice": voice,
            "id": self.connectionID}

        self.mainDict["modules"][output_module]["connections"]["out"][output_port].append(
            output_dict)
        self.mainDict["modules"][input_module]["connections"]["in"][input_port] = input_dict
        if self.debugMode:
            print("-----")


    def checkModuleExistence(self, module, port="port", direction=""):

        if self.debugMode:
            print("Checking if module already existing in main dictionary: " + module)

        # Check if module exists in main dictionary
        if module not in self.mainDict["modules"]:
            self.mainDict["modules"][module] = {
                "parameters": {},
                "connections": {"out": {}, "in": {}}
            }

        # If it exists, check if the port exists
        if direction == "in":
            if port not in self.mainDict["modules"][module]["connections"]["in"]:
                self.mainDict["modules"][module]["connections"]["in"][port] = []

        if direction == "out":
            if port not in self.mainDict["modules"][module]["connections"]["out"]:
                self.mainDict["modules"][module]["connections"]["out"][port] = []


    def addParameter(self, module, name, value):
        self.checkModuleExistence(module)
        # Add parameter to self.mainDict
        if self.debugMode:
            print("Adding parameter: " + module + " - " + name + " - " + value)
        self.mainDict["modules"][module]["parameters"][name] = value


    def addComment(self, value):
        self.mainDict["comments"].append(value)

    def _print_module(self, module):
        print("-------")
        print("Showing information for module: " + module.upper())
        print()
        print("Inputs:")
        for c in self.mainDict["modules"][module]["connections"]["in"]:
            keyvalue = self.mainDict["modules"][module]["connections"]["in"][c]
            print(keyvalue["output_module"].title() + " (" + keyvalue["output_port"].title(
            ) + ") > " + c.title() + " - " + keyvalue["connection_type"].title())
        print()

        print("Outputs:")
        for x in self.mainDict["modules"][module]["connections"]["out"]:
            port = self.mainDict["modules"][module]["connections"]["out"][x]
            for c in port:
                keyvalue = c
                print(x.title() + " > " + keyvalue["input_module"].title() + " (" + keyvalue["input_port"].title(
                ) + ") " + " - " + keyvalue["connection_type"].title() + " - " + keyvalue["voice"])
        print()

        print("Parameters:")
        for p in self.mainDict["modules"][module]["parameters"]:
            value = self.mainDict["modules"][module]["parameters"][p]
            print(p.title() + " = " + value)
        print()

        if not self.quiet: print("-------")

    def detailModule(self, all=False):
        if not all:
            module = input("Enter module name: ").lower()
            if module in self.mainDict["modules"]:
                _print_module(module)
        else:
            for module in self.mainDict["modules"]:
                _print_module(module)


    def printConnections(self):
        print()
        print("Printing all connections by type...")
        print()

        for ctype in self.connectionTypes:
            ctype_name = self.connectionTypes[ctype]
            print("Connection type: " + ctype_name)
            # For each module
            for module in self.mainDict["modules"]:
                # Get all outgoing connections:
                connections = self.mainDict["modules"][module]["connections"]["out"]
                for c in connections:
                    connection = connections[c]
                    for subc in connection:
                        # print(connection)
                        if subc["connection_type"] == ctype_name:
                            print(module.title(
                            ) + " > " + subc["input_module"].title() + " (" + subc["input_port"].title() + ") ")
            print()


    def exportJSON(self):
        # Exports mainDict as json file
        # name = filename.split(".")[0]
        # filepath = getFilePath(name + '.json')
        # print("Exporting dictionary as file: " + filepath)
        # with open(filepath, 'w') as fp:
        #     json.dump(mainDict, fp)
        print(json.dumps(self.mainDict))


    def printDict(self):
        for key in self.mainDict["modules"]:
            print(key.title() + ": " + str(self.mainDict["modules"][key]))


