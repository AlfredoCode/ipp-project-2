import argparse
import sys
import os
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
            "NOT":          2,

            "ADD":          3,
            "SUB":          3,
            "MUL":          3,
            "IDIV":         3,
            "LT":           3,
            "GT":           3,
            "EQ":           3,
            "AND":          3,
            "OR":           3,
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
                # Instruicton <arg> elements check
                new = []

                sorted_children = sorted((node for node in child.childNodes if node.nodeType == node.ELEMENT_NODE), key=lambda child: child.tagName)

                try:
                        ope.operands[child.getAttribute('opcode')]
                except:
                    e.msg("Invalid opcode!\n")
                    exit(e.XML_STRUCTURE)
                for sub in sorted_children:
                    # print(child.getAttribute('opcode'))
                    # print(self.count)
            
                        
                    if sub.nodeType == sub.ELEMENT_NODE:
                        self.count += 1
                        arg_pattern = "arg["+str(self.count)+"]"
                        if sub.tagName not in new:
                            # print(sub.tagName)
                            if re.match(arg_pattern, sub.tagName):
                                new.append(sub.tagName)
                            else:
                                e.msg("Unknown arg tag!\n")
                                exit(e.XML_STRUCTURE)
                        else:
                            e.msg("Arguments of same number not allowed!\n")
                            exit(e.XML_STRUCTURE)
                if self.count < ope.operands[child.getAttribute('opcode')] or self.count > ope.operands[child.getAttribute('opcode')]:
                    e.msg("Invalid number of arguments for instruction!\n")
                    exit(e.XML_STRUCTURE)
            self.count = 0
        try:
            self.firstLevel.sort(key=lambda tag: int(tag.getAttribute('order'))) # Sorts the instructions by order
        except:
            e.msg("Order value is not integer number!\n")
            exit(e.XML_STRUCTURE) 
        prev_order = None
        for tag in self.firstLevel:
            curr_order = tag.getAttribute('order')
            # print(curr_order)
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
        self.data = []
        self.insList = []
        self.labelList = []
        self.inp = None
        self.reader = 0
    def checkOperand(self, op, e):
        op_frame = self.getFrame(op)
        if op_frame is not None:
            self.existsFrame(op_frame, e)
            op = self.strip(op) 
            for item in op_frame:
                # print(frame, var, item[0])
                if item[0] == op:
                    op = item[1]
        return op

    def evaluate(self, dst, op1, op2, mode, t1, t2, e):
        p_mode = ""
        if mode != "JUMPIF":
            frame = self.getFrame(dst)
            self.existsFrame(frame, e)
        
        op1 = self.checkOperand(op1, e)
        op2 = self.checkOperand(op2, e)
        if mode == "JUMPIF":
            # print(op1 == op2)
            return op1 == op2
        diff = False
        try:
            if mode == "SUB":
                tmp = int(op1) - int(op2)
            elif mode == "ADD":
                tmp = int(op1) + int(op2)
            elif mode == "MUL":
                tmp = int(op1) * int(op2)
            elif mode == "IDIV":
                tmp = int(op1) / int(op2)
                tmp = int(tmp)
            elif mode == "AND":
                # print(bool(op1), bool(op2))
                tmp = op1 and op2
            elif mode == "OR":
                tmp = op1 or op2
            elif mode == "NOT":
                if op1 == "false":
                    tmp = "true"
                else:
                    tmp = "false"
            elif mode == "LT" or mode == "GT" or mode == "EQ" or mode == "CONCAT":
                
                if t1 == "nil" or t2 == "nil":
                    if mode == "EQ":
                        tmp = op1 == op2
                    else:
                        e.msg("Cannot compare nil value with LT or GT!\n")
                        exit(e.OPERAND_TYPE)
                elif t1 == "int" and t2 == "int":
                    if mode == "LT":
                        tmp = int(op1) < int(op2)
                    elif mode == "GT":
                        tmp = int(op1) > int(op2) 
                    elif mode == "EQ":
                        tmp = int(op1) == int(op2) 
                    else:
                        diff = True
                        exit(e.OPERAND_TYPE)
                elif t1 == "bool" and t2 == "bool":
                    if mode == "LT":
                        tmp = op1 < op2
                    elif mode == "GT":
                        tmp = op1 > op2 
                    elif mode == "EQ":
                        tmp = op1 == op2 
                    else:
                        diff = True
                        exit(e.OPERAND_TYPE)

                elif t1 == "string" and t2 == "string": # string & string only
                    if mode == "LT":
                        tmp = op1 < op2
                    elif mode == "GT":
                        tmp = op1 > op2 
                    elif mode == "CONCAT":
                        tmp = op1 + op2 # concatenated string    
                    elif mode == "EQ":
                        tmp = op1 == op2
                    else:
                        diff = True
                        exit(e.OPERAND_TYPE)
                elif t1 != t2 and (t1 != "var" or t2 != "var" or t1 != "nil" or t2 != "nil"):
                    diff = True
                    exit(e.OPERAND_TYPE)


                elif t1 == "var":
                    if t2 == "int":
                        if op1 != "nil":
                            if not op1.isdigit():
                                e.msg("Expected int and int logic operation!\n")
                                exit(e.OPERAND_TYPE)
                            if mode == "LT":
                                tmp = int(op1) < int(op2)
                            elif mode == "GT":
                                tmp = int(op1) > int(op2) 
                        else:
                            tmp = op1 == op2
                    elif t2 == "bool":
                        if op1 != "nil":
                            if not (op1 == "false" or op1 == "true"):
                                e.msg("Expected bool and bool logic operation!\n")
                                exit(e.OPERAND_TYPE)
                            if mode == "LT":
                                tmp = op1 < op2
                            elif mode == "GT":
                                tmp = op1 > op2
                        else:
                            tmp = op1 == op2
                    elif t2 == "string":
                        if op1 != "nil":
                            if mode == "LT":
                                tmp = op1 < op2
                            elif mode == "GT":
                                tmp = op1 > op2
                            elif mode == "CONCAT":
                                tmp = op1 + op2 # concatenated string
                        else:
                            tmp = op1 == op2
                elif t2 == "var":
                    if t1 == "int":
                        if op2 != "nil":
                            if not op2.isdigit():
                                e.msg("Expected int and int logic operation!\n")
                                exit(e.OPERAND_TYPE)
                            if mode == "LT":
                                tmp = int(op1) < int(op2)
                            elif mode == "GT":
                                tmp = int(op1) > int(op2)   
                        else:
                            tmp = op1 == op2
                    elif t1 == "bool":
                        if op2 != "nil":
                            if not (op2 == "false" or op2 == "true"):
                                e.msg("Expected bool and bool logic operation!\n")
                                exit(e.OPERAND_TYPE)
                            if mode == "LT":
                                tmp = op1 < op2
                            elif mode == "GT":
                                tmp = op1 > op2
                        else:
                            tmp = op1 == op2
                    elif t1 == "string":
                        if op2 != "nil":
                            if mode == "LT":
                                tmp = op1 < op2
                            elif mode == "GT":
                                tmp = op1 > op2
                            elif mode == "CONCAT":
                                tmp = op1 + op2 # concatenated string
                        else:
                            tmp = op1 == op2
                    
            elif mode == "STRI2INT":
                wanted = op1[int(op2)]
                tmp = ord(wanted)
            elif mode == "GETCHAR":
                tmp = op1[int(op2)]
            elif mode == "SETCHAR":
                var = self.strip(dst)
                for item in frame:
                    if item[0] == var:
                        var = item[1]
                        break

                tmp = var[:int(op1)] + op2[0] + var[int(op1)+1:]   
                # print(dst, op1, op2)
        except:
            if mode == "IDIV":
                e.msg("Zero division not allowed!\n")
                exit(e.RUNTIME_VALUE)
            elif mode == "STRI2INT" or mode == "GETCHAR" or mode == "SETCHAR":
                    e.msg("Cannot convert the character into ordinary value or index out of bounds!\n")
                    exit(e.RUNTIME_STRING)
            elif diff == True:
                e.msg("Cannot perform operations with different types or types other than string!\n")
                exit(e.OPERAND_TYPE)
            else:
                e.msg("One or more uninitialized variables!\n")
                exit(e.MISSING_VALUE)
        # print(tmp, frame, dst)
        tmp = str(tmp).lower()
        self.updateValue(str(tmp), dst, e)

    def dataPush(self, data, e):
        frame = self.getFrame(data)
        if frame is None:
            self.data.append(data)
        else:
            self.existsVar(data, e)
            data = self.strip(data)
            for item in frame:
                if item[0] == data:
                    self.data.append(item[1])

        # print(self.data)
    def dataPop(self, data, e):
        frame = self.getFrame(data)
        self.existsFrame(frame, e)
        
        try:
            popped = self.data.pop()
        except:
            e.msg("Cannot pop value, stack is empty!\n")
            exit(e.MISSING_VALUE)
        self.updateValue(popped, data, e)

    def updateValue(self, value, dst, e):
        frame = self.getFrame(dst)
        dst = self.strip(dst)
        valFrame = self.getFrame(value)
        if valFrame != None:
            self.existsVar(value, e)
        for item in frame:
            if item[0] == dst:
                item[1] = value  
                break

    def appendVar(self, var, e):
        type = self.getFrame(var)
        var = self.strip(var)

        if type is self.GF:
            self.findVar(var, self.GF, e)
            self.GF.append([var, None])
        elif type is self.LF:
            if self.LF is None:
                e.msg("LF does not exist!\n")
                exit(e.FRAME_NOT_EXIST)
            self.findVar(var, self.LF, e)
            self.LF.append([var, None])
        elif type is self.TF:
            if self.TF is None:
                e.msg("TF does not exist!\n")
                exit(e.FRAME_NOT_EXIST)
            self.findVar(var, self.TF, e)
            self.TF.append([var, None])
    def labelExists(self, label, e):
        for lab in self.labelList:
            # print(lab[0], label)
            if lab[0] == label:
                e.msg("LABEL redefinition not allowed!\n")
                exit(e.SEMANTIC)
    def appendLabel(self, label, pos, e):
        pos = pos

        self.labelExists(label, e)
        self.labelList.append((label, pos))
        
    def getFrame(self, var):
        
        pattern_GF = "GF@[^@]+"
        pattern_TF = "TF@[^@]+"
        pattern_LF = "LF@[^@]+"
        frame = None
        if re.match(pattern_GF, var):
            frame = self.GF
        elif re.match(pattern_TF, var):
            frame = self.TF
        elif re.match(pattern_LF, var):
            frame = self.LF
        return frame
    def strip(self, var):
        frame = self.getFrame(var) 
        if frame is self.GF:
            var = var.replace("GF@", "")  ## PROBLEM PLACE
        elif frame is self.TF:
            var = var.replace("TF@", "")  ## PROBLEM PLACE
        elif frame is self.LF:
            var = var.replace("LF@", "")  ## PROBLEM PLACE
        return var

    def existsFrame(self, frame, e):
        if frame is None:
            e.msg("Frame does not exist!\n")
            exit(e.FRAME_NOT_EXIST)
    def existsVar(self, var, e):
        frame = self.getFrame(var)
        # print(frame, var)
        self.existsFrame(frame, e)
        var = self.strip(var)
        found = False
        for item in frame:
            # print(frame, var, item[0])
            if item[0] == var:
                found = True
                break
        if not found:
            e.msg("Using undefined variable, probably missing DEFVAR\n")
            exit(e.UNDEF_VAR)
        
    def pushFrame(self, e):
        # print(self.frameStack)
        if self.TF is None:
            e.msg("TF cannot be pushed since it does not exist.\n")
            exit(e.FRAME_NOT_EXIST)
        
        self.frameStack.append(self.TF)
        self.LF = self.frameStack.pop()
        self.TF = None
        self.frameStack.append(self.LF)
    def popFrame(self, e):
        if self.frameStack == []:
            e.msg("No LF to pop available!\n")
            exit(e.FRAME_NOT_EXIST)
        self.TF = self.frameStack.pop()
        self.LF = self.frameStack.pop()
        self.frameStack.append(self.LF)
        # print(self.LF, self.TF)

    def findVar(self, var, frame, e):
        if var in frame:
            e.msg("Variable cannot be redefined, probably used DEFVAR on same var\n")
            exit(e.SEMANTIC)
    def printVar(self, var, t1, mode, e):   # Existence of variable needs to be checked before calling the method
        if t1 == "var":
            frame = self.getFrame(var)
            # print(frame, var)
            self.existsFrame(frame, e)
            var = self.strip(var) 
            for item in frame:
                # print(frame, var, item[0])
                if item[0] == var:
                    if mode == "normal":
                        if item[1] is None:
                            e.msg("Variable not initialized!\n")
                            exit(e.MISSING_VALUE)
                        print(item[1], end="")
                    elif mode == "stderr":
                        sys.stderr.write(item[1])
                    break 
        else:
            sys.stderr.write(var)
    def convertInt(self, dst, value, e):
        self.existsVar(dst, e)
        try:
            tmp = chr(int(value))
        except:
            e.msg("Wrong value to convert!\n")
            exit(e.RUNTIME_STRING)
        self.updateValue(tmp, dst, e)
    def getLength(self, dst, op1, e):
        self.existsVar(dst, e)
        try:
            if op1 == "":
                tmp = 0
            else:    
                tmp = len(op1)
        except:
            e.msg("Something wrong happened when executing STRLEN!\n")
            exit(e.RUNTIME_STRING)
        self.updateValue(str(tmp), dst, e)
    def getType(self, dst, op1, e):
        frame = self.getFrame(op1)
        type = ""
        if frame is not None:
            self.existsFrame(frame, e)
            op1 = self.strip(op1) 
            for item in frame:
                # print(frame, var, item[0])
                if item[0] == op1:
                    op1 = item[1]
                    break
        if op1 is None:
            type = ""
        elif not op1.isdigit():
            if op1 == "true" or op1 == "false":
                type = "bool"
            elif op1 == "nil":
                type = "nil"
            else:
                type = "string"
        else:
            type = "int"
        self.updateValue(str(type), dst, e)
    def jumpIf(self, dst, op1, op2, t1, t2, e):
        jump = self.evaluate(dst, op1, op2, "JUMPIF", t1, t2, e)
        # print(jump)
        return jump
    def listAll(self, e):   # Lists all variables in all available frames -- DEBUG INFO
        insCount = len(self.insList)
        e.msg(f">>> Number of used instructions: {insCount}\n")
        if self.LF is not []:
            e.msg(">>> GF Variables\n")
            for var in self.GF:
                e.msg("\t"+str(var)+"\n")
        if self.LF is not None:
            e.msg(">>> LF Variables\n")
            for var in self.LF:
                e.msg("\t"+str(var)+"\n")
        if self.TF is not None:
            e.msg(">>> TF Variables\n")
            for var in self.TF:
                e.msg("\t"+str(var)+"\n")
        if self.frameStack != []:
            e.msg(">>> Frame Stack\n")   
            for var in self.frameStack:
                e.msg("\t"+str(var)+"\n")
        self.allLabels(e)
        self.allInstructions(e)
    def readValue(self, dst, type, e):
        tmp = "nil"
        # print(dst, type)
        if self.inp is None:
            if type == "int":
                try:
                    tmp = str(int(input()))
                except:
                    tmp = "nil"
            elif type == "string":
                tmp = str(input())
            elif type == "bool":
                try:
                    tmp = str(bool(input())).lower()
                except:
                    tmp = "nil"
        else:
            inp = str(self.inp).splitlines()
            # print(inp)
            if type == "int":
                # print(inp[self.reader], self.reader)
                try:
                    tmp = str(int(inp[self.reader]))
                except:
                    tmp = "nil"
            elif type == "string":
                tmp = str(inp[self.reader])
            elif type == "bool":
                if str(inp[self.reader]).lower() == "true":
                    tmp = "true"
                else:
                    tmp = "false"
        self.reader += 1
        self.updateValue(tmp, dst, e)
    def allLabels(self, e):
        e.msg(">>> Label List\n")   
        for var in self.labelList:
            e.msg("\t"+str(var)+"\n")
    def allInstructions(self, e):
        e.msg(">>> Used instructions so far\n")
        allIns = self.insList
        
        for var in allIns:
            var = (var[0].getAttribute('opcode'),) + var[1:]    
            e.msg("\t"+str(var)+"\n")
    def createFrame(self, e):
        self.TF = []

class InstructionParser:
    def __init__(self, element, pos, inp):
        self.opcode = element.getAttribute('opcode')
        self.element = element
        self.pos = pos
        self.inp = inp
    def getPos(self):
        return self.pos    
    def execute(self, e, frame):
        op = self.opcode
        children = [node for node in self.element.childNodes if node.nodeType == node.ELEMENT_NODE]
        sorted_children = sorted(children, key=lambda node: node.tagName)
        # print(op)
        # print(self.element.childNodes)
        arg_counter = 0 
        dst = ""
        # print(op)
        for child in sorted_children:
            if child.nodeType == child.ELEMENT_NODE:
                # print(child.tagName)
                for sub_child in child.childNodes:
                    # print(child.tagName)
                    curr = sub_child.nodeValue.strip()
                    # print(curr)
                    arg_counter += 1
                    if op == "DEFVAR":
                        frame.appendVar(curr, e)
                    elif op == "MOVE":
                        if arg_counter == 1:
                            # print(arg_counter)
                            dst = curr
                            frame.existsVar(dst, e)
                        else:
                            frame.updateValue(curr, dst, e)   
                    elif op == "WRITE":
                        t1 = child.getAttribute('type')
                        if child.getAttribute('type') == 'bool' or child.getAttribute('type') == 'nil':
                            pass
                        elif child.getAttribute('type') == 'var':
                            frame.existsVar(curr, e)
                            frame.printVar(curr, t1, "normal", e)
                        elif child.getAttribute('type') == 'int' or child.getAttribute('type') == 'string':
                            print(curr, end="")
                        # elif child.getAttribute('type') == 'float':
                        #     print(float.hex(float.fromhex(curr)), end="")
                    
                    elif op == "EXIT":
                        if child.getAttribute('type') == 'int':
                            exit(int(curr))  
                        else:
                            e.msg("Invalid exit code!\n")
                            exit(e.XML_STRUCTURE)
                    elif op == "PUSHS":
                        frame.dataPush(curr, e)
                    elif op == "POPS":
                        frame.dataPop(curr, e)
                    elif op == "DPRINT":
                        t1 = child.getAttribute('type')
                        if t1 == "var":
                            frame.existsVar(curr, e)
                        frame.printVar(curr, t1, "stderr", e)   
                    elif op == "LABEL":
                        # frame.appendLabel(curr, e)
                        pass
                    elif op == "JUMP":
                        for lab in frame.labelList:
                            if lab[0] == curr:
                                self.pos = lab[1]

                                    
                    else:
                        if arg_counter == 1:
                            dst = curr
                        elif arg_counter == 2:
                            op1 = curr
                            t1 = child.getAttribute('type')
                            if op == "NOT":
                                frame.evaluate(dst, op1, "", "NOT", t1, t2, e)  
                            elif op == "INT2CHAR":
                                frame.convertInt(dst, op1, e)
                            elif op == "STRLEN":
                                frame.getLength(dst, op1, e)
                            elif op == "TYPE":
                                frame.getType(dst, op1, e)
                            elif op == "READ":
                                frame.readValue(dst, op1, e)
                            
                        else:   # TODO arithmetic - int & var only, logic - bool & var only
                            op2 = curr
                            t2 = child.getAttribute('type')
                            if op == "ADD":
                                frame.evaluate(dst, op1, op2, "ADD", t1, t2, e)
                            elif op == "SUB":
                                frame.evaluate(dst, op1, op2, "SUB", t1, t2, e)    
                            elif op == "MUL":
                                frame.evaluate(dst, op1, op2, "MUL", t1, t2, e) 
                            elif op == "IDIV":
                                frame.evaluate(dst, op1, op2, "IDIV", t1, t2, e) 
                            elif op == "AND":
                                frame.evaluate(dst, op1, op2, "AND", t1, t2, e) 
                            elif op == "OR":
                                frame.evaluate(dst, op1, op2, "OR", t1, t2, e)
                            elif op == "LT":
                                frame.evaluate(dst, op1, op2, "LT", t1, t2, e)
                            elif op == "GT":
                                frame.evaluate(dst, op1, op2, "GT", t1, t2, e)
                            elif op == "EQ":
                                frame.evaluate(dst, op1, op2, "EQ", t1, t2, e)
                            elif op == "STRI2INT":
                                frame.evaluate(dst, op1, op2, "STRI2INT", t1, t2, e)
                            elif op == "CONCAT":
                                frame.evaluate(dst, op1, op2, "CONCAT", t1, t2, e)
                            elif op == "GETCHAR":
                                frame.evaluate(dst, op1, op2, "GETCHAR", t1, t2, e)
                            elif op == "SETCHAR":
                                frame.evaluate(dst, op1, op2, "SETCHAR", t1, t2, e)
                            elif op == "JUMPIFEQ":
                                # print(dst, op1, op2)
                                if frame.jumpIf(dst, op1, op2, t1, t2, e):
                                    for lab in frame.labelList:
                                        if lab[0] == dst:
                                            self.pos = lab[1]  
                            elif op == "JUMPIFNEQ":
                                # print(dst, op1, op2)
                                if not frame.jumpIf(dst, op1, op2, t1, t2, e):
                                    for lab in frame.labelList:
                                        if lab[0] == dst:
                                            self.pos = lab[1]  
                
                if op == "STRLEN" and child.childNodes.length + 1 == 1: # empty string
                    frame.getLength(dst, "", e)

        if op == "CREATEFRAME": 
            frame.createFrame(e)
        elif op == "PUSHFRAME":
            frame.pushFrame(e)
        elif op == "POPFRAME":
            frame.popFrame(e)
        elif op == "BREAK":
            frame.listAll(e)
            exit(0)

class progCounter:
    def __init__(self):
        self.pc = 1
    def inc(self, pc):
        pc += 1
        self.pc = pc
        # print(self.pc)
        return pc

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
    # print(src, inp)
    if src is None:
        if inp is None:
            e.msg("Argument --source nebo --input nebyl nalezen\n")
            exit(e.SCRIPT_PARAM) 
        src = sys.stdin.read()
        try:
            DOM = parseString(src)
        except:
            e.msg("Input document is not well-formated!\n")
            exit(e.XML_FORMAT)
    else:
        if not os.path.exists(src):
            e.msg("File does not exist!\n")
            exit(e.FILE_NOT_FOUND)
        try:
            DOM = parse(src)
        except:
            e.msg("Input document is not well-formated!\n")
            exit(e.XML_FORMAT)
    if inp is None:
        inp = sys.stdin.read()
    else:
        try:
            with open(inp, "r") as file:
                inp = file.read()
        except:
            e.msg("File does not exist!\n")
            exit(e.FILE_NOT_FOUND)    
    frame.inp = inp
    
    root = DOM.documentElement

    xl.processXML(root, e)
    pos = progCounter()
    lab_cnt = 1
    for child in xl.firstLevel:
        # print(child.getAttribute('opcode'))
        if child.nodeType == child.ELEMENT_NODE and child.getAttribute('opcode') == "LABEL":
            for sub in child.childNodes:
                if sub.nodeType == sub.ELEMENT_NODE:
                    for ss in sub.childNodes:
                        frame.appendLabel(ss.nodeValue, lab_cnt, e)
        lab_cnt += 1
    while pos.pc <= len(xl.firstLevel):
        # print(pos.pc)
        tag = xl.firstLevel[pos.pc - 1]
        ins = InstructionParser(tag, pos.pc, inp) # New instance of instruction
        frame.insList.insert(pos.pc, (tag, pos.pc))
        ins.execute(e, frame)
        pc = ins.getPos()
        pos.inc(pc)
        # print(f"Order: {tag.getAttribute('order')} Instruction: {tag.getAttribute('opcode')}")
    # frame.listAll(e)
if __name__ == '__main__':
    Prog()