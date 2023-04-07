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
class Operands:
    def __init__(self):
        self.operands = {
            "CREATEFRAME":  0, 
            "PUSHFRAME":    0, 
            "POPFRAME":     0, 
            "RETURN":       0, 
            "BREAK":        0,

            "DEFVAR":       1,
            "CALL":         1,
            "PUSHS":        1,
            "POPS":         1,
            "WRITE":        1,
            "LABEL":        1,
            "JUMP":         1,
            "EXIT":         1,
            "DPRINT":       1,

            "MOVE":         2,
            "INT2CHAR":     2,
            "READ":         2,
            "STRLEN":       2,
            "TYPE":         2,

            "ADD":          3,
            "SUB":          3,
            "MUL":          3,
            "IDIV":         3,
            "LT":           3,
            "GT":           3,
            "EQ":           3,
            "AND":          3,
            "OR":           3,
            "NOT":          3,
            "STRI2INT":     3,
            "CONCAT":       3,
            "GETCHAR":      3,
            "SETCHAR":      3,
            "JUMPIFEQ":     3,
            "JUMPIFNEQ":    3    



        }



class ParseXML:
    def __init__(self):
        self.count = 0
        self.firstLevel = []
        self.operands = Operands()


    def tagsLoad(self, element, e):
        ope = self.operands
        
        if element.tagName != "program":
            exit(e.XML_STRUCTURE)
        if "language" not in element.attributes.keys():
            e.msg("Missing attribute language in <program> element\n")
            exit(e.XML_STRUCTURE)
        for child in element.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                if child.tagName != "instruction":
                    e.msg("Unknow tag found!\n")
                    exit(e.XML_STRUCTURE)
                self.firstLevel.append(child)
                # TODO check instruicton <arg> elements
                new = []
                for sub in child.childNodes:
                    
                    # print(child.getAttribute('opcode'))
                    # print(self.count)
                    try:
                        ope.operands[child.getAttribute('opcode')]
                    except:
                        e.msg("Invalid opcode!\n")
                        exit(e.XML_STRUCTURE)
                    if self.count > ope.operands[child.getAttribute('opcode')]:
                        e.msg("Invalid number of arguments for instruction!\n")
                        exit(e.XML_STRUCTURE)
                        
                    if sub.nodeType == sub.ELEMENT_NODE:
                        self.count += 1
                        arg_pattern = "arg["+str(self.count)+"]"
                        if sub.tagName not in new:
                            if re.match(arg_pattern, sub.tagName):
                                new.append(sub.tagName)
                            else:
                                e.msg("Unknown arg tag!\n")
                                exit(e.XML_STRUCTURE)
                        else:
                            e.msg("Arguments of same number not allowed!\n")
                            exit(e.XML_STRUCTURE)
            self.count = 0
        
        self.firstLevel.sort(key=lambda tag: tag.getAttribute('order')) # Sorts the instructions by order
        prev_order = None
        for tag in self.firstLevel:
            curr_order = tag.getAttribute('order')
            try:    # Check if order is numeric or not
                curr_order = int(curr_order)
            except:
                e.msg("Order value is not integer number!\n")
                exit(e.XML_STRUCTURE)
            if curr_order == "":
                e.msg("Order attribute not found!\n")
                exit(e.XML_STRUCTURE)
            if curr_order == prev_order:
                e.msg("Duplicit order attribute values not allowed!\n")
                exit(e.XML_STRUCTURE)
            if  curr_order <= 0:
                e.msg("Negative or 0 order values not allowed!\n")
                exit(e.XML_STRUCTURE)
            prev_order = curr_order

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
            self.findVar(var, self.GF, e)
            self.GF.append(var)
        elif type == "LF":
            if self.LF is None:
                exit(e.FRAME_NOT_EXIST)
            self.findVar(var, self.LF, e)
            self.LF.append(var)
        elif type == "TF":
            if self.TF is None:
                exit(e.FRAME_NOT_EXIST)
            self.findVar(var, self.TF, e)
            self.TF.append(var)
        

    #TODO def existsVar --> UNDEF_VAR
    def existsVar(self, var, frame, e):
        if var not in frame:
            e.msg("Using undefined variable, probably missing DEFVAR\n")
            exit(e.UNDEF_VAR)
    def pushFrame(self, e):
        if self.TF is None:
            e.msg("TF cannot be pushed since it does not exist.\n")
            exit(e.FRAME_NOT_EXIST)
        
        self.frameStack.append(self.TF)
        self.LF = self.frameStack.pop()
        self.TF = None


    def findVar(self, var, frame, e):
        if var in frame:
            e.msg("Variable cannot be redefined, probably used DEFVAR on same var\n")
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
        # print(op)
        # print(self.element.childNodes)
        pattern_GF = "GF@[^@]+"
        pattern_TF = "TF@[^@]+"
        pattern_LF = "LF@[^@]+"
        for child in children:
                
            for sub_child in child.childNodes:
                curr = sub_child.nodeValue.strip()
                # print(curr)
                
                if op == "DEFVAR":
                    if re.match(pattern_GF, curr):
                        curr = curr.replace("GF@", "")  ## PROBLEM PLACE
                        frame.appendVar(curr, "GF", e)
                    if re.match(pattern_TF, curr):
                        curr = curr.replace("TF@", "")  ## PROBLEM PLACE
                        frame.appendVar(curr, "TF", e)
                    if re.match(pattern_LF, curr):
                        curr = curr.replace("LF@", "")  ## PROBLEM PLACE
                        frame.appendVar(curr, "LF", e)
                # elif op == "WRITE":

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
    try:
        DOM = parse(src)
    except:
        e.msg("Input document is not well-formated!\n")
        exit(e.XML_FORMAT)
    root = DOM.documentElement

    xl.processXML(root, e)
    for tag in xl.firstLevel:
        
        ins = InstructionParser(tag) # New instance of instruction
        ins.execute(e, frame)
        # print(f"Order: {tag.getAttribute('order')} Instruction: {tag.getAttribute('opcode')}")
    frame.listAll(e)
if __name__ == '__main__':
    Prog()