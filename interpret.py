import argparse
import sys
import re
from xml.dom.minidom import parse, parseString

class Err():
    SCRIPT_PARAM = 10
    FILE_NOT_FOUND = 11
    FILE_CANNOT_WRITE = 12

    XML_FORMAT = 31
    XML_STRUCTURE = 32

    SEMANTIC = 52
    OPERAND_TYPE = 53
    UNDEF_VAR = 54
    FRAME_NOT_EXIST = 55
    MISSING_VALUE = 56
    RUNTIME_VALUE = 57
    RUNTIME_STRING = 58
    INTERNAL = 99

    def msg(self, mess):
        sys.stderr.write(mess)
class ParseXML:
    def __init__(self):
        self.count = 0
        self.firstLevel = []

    def tagsLoad(self, element, e):
        if element.tagName != "program":
            exit(e.XML_STRUCTURE)
        if "language" not in element.attributes.keys():
            e.msg("Missing attribute language in <program> element\n")
            exit(e.XML_STRUCTURE)
        for child in element.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                self.count += 1
                self.firstLevel.append(child)
                # TODO check instruicton <arg> elements

        self.firstLevel.sort(key=lambda tag: tag.getAttribute('order')) # Sorts the instructions by order

class LoadXML(ParseXML):
    

    def processXML(self, element, e):
        self.tagsLoad(element, e)

class Frame:
    def __init__(self, type):
        self.vars = []
        self.type = type
    
    def appendVar(self, var, e):
        self.findVar(var, e)
        self.vars.append(var)

    #TODO def existsVar --> UNDEF_VAR

    def findVar(self, var, e):
        if var in self.vars:
            exit(e.SEMANTIC)

    def listAll(self, e):
        for var in self.vars:
            e.msg(var+"\n")

class InstructionParser:
    def __init__(self, element):
        self.opcode = element.getAttribute('opcode')
        self.element = element
    def execute(self, e, frame):
        op = self.opcode
        children = self.element.childNodes
        for child in children:
            if child.nodeType == child.ELEMENT_NODE:
                for sub_child in child.childNodes:
                    if sub_child.nodeType == sub_child.TEXT_NODE:
                        curr = sub_child.nodeValue.strip()
                        # print(curr)
                        if op == "DEFVAR":
                            if re.match("GF@[^@]+", curr):
                                curr = curr.replace("GF@", "")  ## PROBLEM PLACE
                                
                            frame.appendVar(curr, e)



class Prog:
    # Argument parsing
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=str, help="Vstupní soubor s XML reprezentací zdrojového kódu")
    ap.add_argument('--input', type=str, help="Soubor se vstupy pro samotnou interpretaci zadaného zdrojového kódu")
    args = ap.parse_args()

    # Error instance
    e = Err()
    xl = LoadXML()
    GF = Frame("GF") #global frame

    src = args.source
    inp = args.input

    if src is None and inp is None:
        e.msg("Argument --source nebo --input nebyl nalezen\n")
        exit(e.SCRIPT_PARAM) 

    # TODO src is empty or inp is empty

    DOM = parse(src)
    root = DOM.documentElement

    xl.processXML(root, e)
    for tag in xl.firstLevel:
        ins = InstructionParser(tag) # New instance of instruction
        ins.execute(e, GF)
        # print(f"Order: {tag.getAttribute('order')} Instruction: {tag.getAttribute('opcode')}")
    GF.listAll(e)
if __name__ == '__main__':
    Prog()