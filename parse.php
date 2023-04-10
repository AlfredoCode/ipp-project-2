<?php
ini_set('display_errors', 'stderr');
$empty_pattern = "/^$/";
$split_pattern = "/\s+/";


/**
 * Enum of possible error codes
 */
enum Errors: int{
    const ERR_SWITCH = 10;
    const ERR_HEADER = 21;
    const ERR_OP_CODE = 22;
    const ERR_SRC = 23;
}

/**
 * Enum of possible configurations
 */
enum Params: int{
    const NO_REQ = 0;   
    const REQ = 1;              // <var>
    const REQ_OPT = 2;          // <var> <symbol>
    const REQ_OPT_OPT = 3;      // <var> <symbol> <symbol>
    const REQ_SET = 4;          // <var> has already been set
    const REQ_TYPE = 5;         // <var> <type>
    const OPT = 6;              // <symbol>
    const LAB = 7;              // <label>
    const LAB_OPT_OPT = 8;      // <label> <symbol> <symbol>
    const REQ_TYPE_SET = 9;     // <var> type set
    const LAB_SET = 10;         // <label> was set
}
/**
 * Removes comments from function parameter, which is one line obtained from input file
 * Returns new string without additional comments
 */
function removeComments($str)
{
    $newString = "";
    $space = -1; // -1 Means we are on the beginning of the string so there is no need to put additional space
    for ($i = 0; $i < strlen($str); $i++) {
        if ($str[$i] == '#') {
            break;
        } 
        elseif ($str[$i] == " ") {  // If the string is something like DEFVAR GF@x #comment, there is additional space between GF@x and #comment which needs to be removed.
            if($space == 0){
                $space = 1;
            }
            continue;
        } 
        else {
            if ($space == 1) {
                $newString .= " ";
            }
            $newString .= $str[$i];
            $space = 0;
        }
    }
    return $newString;
}

/**
 * The function is looking for special characters in string that can be represented specially in XML and replaces them with suitable sequences
 * Parameter of function checkSpecialChars() is string obtained from string@...
 */
function checkSpecialChars($str){
    $newString = ""; 
    for ($i = 0; $i < strlen($str); $i++) {
        switch($str[$i]){
            case '<':
                $newString .= '&lt;';
                break;
            case '>':
                $newString .= '&gt;';
                break;
            case '&':
                $newString .= '&amp;';
                break;
            default:
                $newString .= $str[$i];
                break;
        }
    }
    return $newString;
}

/**
 * Checks for most of the syntax and lexical analysis
 * Sorts the instructions into groups by their arguments
 * Gradually appends new XML constructs into string of already existing constructs
 */
function generateInstructions($ins)
{
    $i = 0;
    global $xml, $order;
    $maxArgs = 0;
    $var_req = Params::NO_REQ;
    $type = "";
    $xml .= '<instruction order="' . $order . '" opcode="' . strtoupper($ins[$i]) . '">' . "\n";
    switch (strtoupper($ins[$i])) {             // Sorted instructions into little groups by count and type of arguments
        case "MOVE":
        case "STRLEN":
        case "TYPE":
        case "INT2CHAR":
        case "NOT":
            $maxArgs = 2;
            $var_req = Params::REQ_OPT;
            break;
        case "DEFVAR":
        case "POPS":
            $maxArgs = 1;
            $var_req = Params::REQ;
            break;
        case "PUSHS":
        case "WRITE":
        case "EXIT":
        case "DPRINT":
            $maxArgs = 1;
            $var_req = Params::OPT;
            break;
        case "CREATEFRAME":
        case "PUSHFRAME":
        case "POPFRAME":
        case "RETURN":
        case "BREAK":
            $var_req = Params::NO_REQ;
            break;
        case "CALL":
        case "LABEL":
        case "JUMP":
            $maxArgs = 1;
            $var_req = Params::LAB;
            break;

        case "JUMPIFEQ":
        case "JUMPIFNEQ":
            $maxArgs = 3;
            $var_req = Params::LAB_OPT_OPT;
            break;

        case "ADD":
        case "SUB":
        case "MUL":
        case "IDIV":
        case "LT":
        case "GT":
        case "EQ":
        case "AND":
        case "OR":
        case "STRI2INT":
        case "CONCAT":
        case "GETCHAR":
        case "SETCHAR":
            $maxArgs = 3;
            $var_req = Params::REQ_OPT_OPT;
            break;
        
        case "READ":
            $maxArgs = 2;
            $var_req = Params::REQ_TYPE;
            break;
        default:
            exit(Errors::ERR_OP_CODE);
    }
    $i++;


    // Regex collection for data types and frames
    // #####################################################################
    $frame_pattern = '/(GF|TF|LF)@[a-zA-Z_\-\$&%*!?]+[a-zA-Z_\-\$&%*!?0-9]*/';
    $string_pattern = '/^string@([^\\\\]*(?:\\\\\d{3})?)+$/u';
    $bool_pattern = '/^bool@(true|false)$/';
    $int_pattern = '/^int@(\+|-)?(0[0-7]*|[1-9]\d*|0[xX]+[0-9A-Fa-f]+)$/';
    $nil_pattern = '/^nil@nil$/';

    $label_pattern = '/^[[:alnum:]_\-\$&%*!?]+$/u';
    // #####################################################################
   
    while ($i < count($ins)) {
        if($i > $maxArgs) {             // Simple check if more arguments than supported are included in instruction
            exit(Errors::ERR_SRC);
        }
        // Filtering arguments of individual instructions and sets their type
        if(preg_match($frame_pattern, $ins[$i])){
            switch($var_req){
                case Params::NO_REQ:
                    exit(Errors::ERR_SRC);
                case Params::LAB_SET:
                    if($i != 1 and $var_req != Params::LAB_SET){
                        exit(Errors::ERR_SRC);
                    }
                case Params::REQ:
                case Params::REQ_OPT:
                case Params::REQ_OPT_OPT:
                case Params::OPT:
                    
                    $type = "var";
                    break;
                case Params::REQ_TYPE:
                    if($i != 1 and $var_req != Params::REQ_SET){
                        exit(Errors::ERR_SRC);
                    }
                    $var_req = Params::REQ_TYPE_SET; // First param is <var>
                    $type = "var";
                    break;
                
                case Params::LAB:
                default:
                    exit(Errors::ERR_SRC);  
            }
            $ins[$i] = checkSpecialChars($ins[$i]);
        }
            
        else{
            if($var_req == Params::OPT or $var_req == Params::LAB_SET or !($var_req == Params::LAB or $var_req == Params::REQ or $var_req == Params::REQ_TYPE or $var_req == Params::REQ_TYPE_SET or $i == 1)){
                if(preg_match($string_pattern . 'u', $ins[$i])){
                    if($type == "string" and $var_req != Params::REQ_OPT_OPT and $var_req != Params::LAB_SET){
                        exit(Errors::ERR_SRC);  // string@ declaration multiple times
                    }
                    $ins[$i] = str_replace("string@", "", $ins[$i]);
                    $ins[$i] = checkSpecialChars($ins[$i]);
                    $type = "string";
                } 
                else if(preg_match($int_pattern . 'u', $ins[$i])){
                    if($type == "int" and $var_req != Params::REQ_OPT_OPT and $var_req != Params::LAB_SET){
                        exit(Errors::ERR_SRC);  // int@ declaration multiple times
                    }
                    $ins[$i] = str_replace("int@", "", $ins[$i]);
                    $type = "int";
                }
                else if(preg_match($bool_pattern . 'u', $ins[$i])){
                    if($type == "bool" and $var_req != Params::REQ_OPT_OPT and $var_req != Params::LAB_SET){
                        exit(Errors::ERR_SRC);  // bool@ declaration multiple times
                    }
                    $ins[$i] = str_replace("bool@", "", $ins[$i]);
                    $type = "bool";
                }
                else if(preg_match($nil_pattern . 'u', $ins[$i])){
                    if($type == "nil" and $var_req != Params::REQ_OPT_OPT and $var_req != Params::LAB_SET){
                        exit(Errors::ERR_SRC);  // nil@ declaration multiple times
                    }
                    $ins[$i] = str_replace("nil@", "", $ins[$i]);
                    $type = "nil";
                }
                else{
                    exit(Errors::ERR_SRC);
                }
            }
            else if(preg_match($label_pattern, $ins[$i]) and $type == "" and ($var_req == Params::LAB or $var_req == Params::LAB_OPT_OPT)){
                $type = "label";
                $var_req = Params::LAB_SET; // First param is <label>
            } 
            else if($var_req == Params::REQ_TYPE_SET){
                switch($ins[$i]){
                    case "int":
                    case "bool":
                    case "string":
                        $type = "type";
                        break;
                    default:
                        exit(Errors::ERR_SRC);
                }
            }
            else{
                exit(Errors::ERR_SRC);
            }
        }
        $xml .= '<arg' . $i . ' type="' . $type . '">';
        $xml .= $ins[$i];
        $xml .= '</arg' . $i . '>' . "\n";
        $i++;
    }
    if($i <= $maxArgs){
        exit(Errors::ERR_SRC);  // Not enough instruction arguments
    }
    $xml .= "</instruction>\n";
    $order++;
}





//  #####################################################################################################################
//  @                                                   MAIN PROGRAM                                                    @
//  #####################################################################################################################
/**
 * Checks if --help at startup is present or not, how many arguments is the program started with
 * Initializes the output XML string, order of instructions
 * Loads individual lines of input file and calls appropriate functions to check syntax / lexical analysis, remove comments
 */
$header = FALSE;
$opts = getopt("", ["help"]);

$xml = '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
$order = 1;

if (isset($opts["help"])) {
    echo("┌>>>>>>>> IPPcode23 into XML parser 1.0 <<<<<<<<\n");
    echo("|\n");
    echo("└>> Requirements\n");
    echo("|\t└>> PHP version 8.1 or later\n");
    echo("|\n");
    echo("└>> Usage\n");
    echo("|\t└>> ./php8.1 parse.php [OPTIONS] < file\n");
    echo("|\t└>> ./php parse.php [OPTIONS] < file\n");
    echo("|\n");
    echo("└>> Arguments\n");
    echo("|\t└>> file\n");
    echo("|\t|\t└>> File containing IPPcode23 assembly code\n");
    echo("|\t|\t└>> Can also be read from STDIN\n");
    
    echo("|\t|\n");
    echo("|\t└>> [OPTIONS]\n");
    echo("|\t\t└>> --help >> Simple help written to user\n");
    echo("|\n");
    echo("└>> ERROR CODES\n");
    echo("\t└>> 10 - Invalid argument when executing script.\n");
    echo("\t└>> 21 - Missing or invalid header in IPPcode23.\n");
    echo("\t└>> 22 - Invalid op code.\n");
    echo("\t└>> 23 - Lexical / syntax error.\n");

    
    
    exit(0);
} else if (count($argv) > 1) {
    exit(Errors::ERR_SWITCH);
}

while (!feof(STDIN)) {
    $line = rtrim(fgets(STDIN), "\r\n");
    $line = removeComments($line);
    if (preg_match($empty_pattern, $line)) {  // If line is empty
        continue;
    }
    if ($line == ".IPPcode23") {
        if (!$header) {
            $header = TRUE;
            $xml .= '<program language="IPPcode23">' . "\n";
        } else {
            exit(Errors::ERR_OP_CODE);      // Multiple headers 
        }
    } else {
        if (!$header) {
            exit(Errors::ERR_HEADER);   // Header not defined
        }
        $result = preg_split($split_pattern, $line);

        generateInstructions($result);
    }
}
if($header){    // If header exists, end the program tag correctly and outputs the whole structured XML string
    $xml .= "</program>";
    echo $xml;
}
else{   // Empty file
    exit(Errors::ERR_HEADER);
}
?>

