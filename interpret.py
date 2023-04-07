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
    def __init__(self):
        self.TF = None
        self.LF = None
        self.GF = []
        self.frameStack = []

    def appendVar(self, var, type, e):
        if type == "GF":
            self.findVar(self.GF, e)
            self.GF.append(var)
        elif type == "LF":
            if self.LF is None:
                exit(e.FRAME_NOT_EXIST)
            self.findVar(self.LF, e)
            self.LF.append(var)
        elif type == "TF":
            if self.TF is None:
                exit(e.FRAME_NOT_EXIST)
            self.findVar(self.TF, e)
            self.TF.append(var)
        

    #TODO def existsVar --> UNDEF_VAR
    def pushFrame(self, e):
        if self.TF is None:
            e.msg("TF cannot be pushed since it does not exist.\n")
            exit(e.FRAME_NOT_EXIST)
        self.frameStack.append(self.TF)
        self.TF = None


    def findVar(self, var, e):
        if var in self.GF:
            exit(e.SEMANTIC)

    def listAll(self, e):
        for var in self.GF:
            e.msg(var+"\n")
        if self.LF is not None:
            for var in self.LF:
                e.msg(var+"\n")
        if self.TF is not None:
            for var in self.TF:
                e.msg(var+"\n")
    def createFrame(self, e):
        if self.TF is None:
            self.TF = []

class InstructionParser:
    def __init__(self, element):
        self.opcode = element.getAttribute('opcode')
        self.element = element
    def execute(self, e, frame):
        op = self.opcode
        children = self.element.childNodes
        print(op)
        # print(self.element.childNodes)
        for child in children:
                for sub_child in child.childNodes:
                        curr = sub_child.nodeValue.strip()
                        # print(curr)
                        
                        if op == "DEFVAR":
                            if re.match("GF@[^@]+", curr):
                                curr = curr.replace("GF@", "")  ## PROBLEM PLACE
                                frame.appendVar(curr, "GF", e)
                            if re.match("TF@[^@]+", curr):
                                curr = curr.replace("TF@", "")  ## PROBLEM PLACE
                                frame.appendVar(curr, "TF", e)
                        else:
                            exit(11)
                if op == "CREATEFRAME": 
                    frame.createFrame(e)
                elif op == "PUSHFRAME":
                    frame.pushFrame(e)



class Prog:
    # Argument parsing
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=str, help="Vstupní soubor s XML reprezentací zdrojového kódu")
    ap.add_argument('--input', type=str, help="Soubor se vstupy pro samotnou interpretaci zadaného zdrojového kódu")
    args = ap.parse_args()

    # Error instance
    e = Err()
    xl = LoadXML()
    frame = Frame() #global frame

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
        if tag.tagName != "instruction":
            exit(e.XML_STRUCTURE)
        ins = InstructionParser(tag) # New instance of instruction
        ins.execute(e, frame)
        # print(f"Order: {tag.getAttribute('order')} Instruction: {tag.getAttribute('opcode')}")
    frame.listAll(e)
if __name__ == '__main__':
    Prog()