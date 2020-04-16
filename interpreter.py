import re

variables = {}


class Code_analysis:
    input_string = []  # содержание строк
    while_count = 0
    while_stack = []
    analysis_error = 0
    signs = ['+', '-', '*', '/', '<', '>', '<=', '>=', '==', '!=', '{', '}', '(', ')', ';']
    number_str = []  # номер строк
    error_dict = {1: "the semicolon symbol is missing in line {}", 2: "incorrect variable name in line {}",
                  3: "incorrect character assignment in line {}", 4: "incorrect expression in line {}",
                  5: "words after brace in line {}", 6: "incorrect word in line {}",
                  7: "the brace is missing in line {}",
                  8: "an expression cannot start with an operator in line {}",
                  9: "the expression cannot end with the operator in line {}",
                  10: "the operator cannot follows the operator or brace in line {}",
                  11: "the operand cannot follows the operand in line {}",
                  12: "the brace cannot follows the brace in line {}", 13: "curly brace is not needed in line {}",
                  14: "using an undeclared variable in line {}", 15: "re-declaring a variable in line {}",
                  16: "a variable without a value is used in line {}"}
    var_types = ["int", "float", "double", "bool", "char"]
    tokens = {r"int|while|float|double|bool": "keyword", r"[(){};]": "separator",
              r"!=|>=|<=|==|[+\-<>=\/*]": "operator", r"true|false|\d+(.\d+)?": "literal",
              r"[a-zA-Z]*[\w]*": "identifier"}
    types = {1: "define_check", 2: "assign_check", 3: "cycle_check", 4: "braces_check", 5: "end_while"}

    def expression_check(self, def_string, number_string):
        """
        функция проверяет проверяет выражение в def_string
        :param def_string: список кортежей лексем (токен, слово)
        :param number_string: номер строки
        :return: error - кортеж ошибок (ошибка, строка)
        """
        expression = Expressions()
        expression.check_expression(def_string, number_string)
        error = expression.errors
        return error

    def print_error(self, error):
        """
        Выводит ошибки
        :param error: кортеж (номер ошибки, номер строки)
        :return:
        """
        for error_tuple in error:
            print("Error: " + self.error_dict[error_tuple[0]].format(error_tuple[1]))

    def end_check(self, end, number_string):
        """
        Проверяет, является ли end - ;
        :param end: символ
        :param number_string: номер строки
        :return: или пустой список или список с кортежем ошибки (номер ошибки, номер строки)
        """
        if end != ";":
            return [(1, number_string)]
        return []

    def equal_check(self, equal, number_string):
        """
        Сравнивает символ в equal с "="
        :param equal: символ
        :param number_string: номер строки
        :return: или пустой список или список с кортежем ошибки(номер ошибки, номер строки)
        """
        if equal != "=":
            return [(3, number_string)]
        return []

    def braces_check(self, def_string, number_string, len_string=0):
        # {
        # }
        """
        Проверяет строки с фигурными скобками:
        Если закрывающая, то проверяет, что цикл открыт по стеку и вынимает значение из стека
        Если открывающая, то проверяет, что стек не пустой, что в нем единица и выводит ошибки,
        если в стеке статус 1, то меняет его на ноль
        Также добавляет ошибку, если длина больше единицы
        :param def_string: список с кортежами (тип лексемы, лексема)
        :param number_string: номер строки
        :param len_string: длина строки
        :return: или пустой список или список с кортежем ошибки(номер ошибки, номер строки), экземпляр листа(SynTree)
        """
        sheet = SynTree()
        error = []
        if def_string[0][1] == '}':
            sheet.str_type = 5
            if not self.while_stack:
                error.append((13, number_string))
            else:
                from_stack = self.while_stack.pop()
                sheet.var_name = from_stack[0]
        else:
            if not self.while_stack:
                error.append((13, number_string))
            elif self.while_stack[-1][1] != 1:
                error.append((13, number_string))
            else:
                from_stack = self.while_stack.pop()
                sheet.var_name = from_stack[0]
                self.while_stack.append((from_stack[0], 0))
        if len_string > 1:
            error.append((5, number_string))
        return error, sheet

    def cycle_check(self, def_string, number_string, len_string):
        # while (expression){
        # while (expression)
        """
        Обрабатывает строки с циклом: проверяет значение в круглых скобках, создает экземпляр листа (SynTree)
        Если фигурная скобка есть, то добавляет в стек кортеж (имя цикла, 0)
        Если фигурной нет, то добавляет в стек кортеж (имя цикла, 1)
        Проверяет на ошибки
        :param def_string: список с кортежами (тип лексемы, лексема)
        :param number_string: номер строки
        :param len_string: длина строки
        :return: или пустой список или список с кортежем ошибки(номер ошибки, номер строки), экземпляр листа(SynTree)
        """
        status = 0
        error = []
        sheet = SynTree(str_type=3, var_name="while{}".format(self.while_count))
        if def_string[len_string - 1][1] == '{':
            error.extend(self.expression_check(def_string[1:-1], number_string))
            sheet.value = def_string[1:-1]
        else:
            error.extend(self.expression_check(def_string[1:], number_string))
            sheet.value = def_string[1:]
            status = 1
        self.while_stack.append(("while{}".format(self.while_count), status))
        self.while_count += 1
        return error, sheet

    def assign_check(self, def_string, number_string, len_string):
        # identifier = expression;
        """
        Проверяет присвоение
        Если переменной нет в таблице переменных, добавляет ошибку
        Проверяет окончание строки, знак равно и выражение
        Создает экземпляр листа (SynTree) и заполняет его поля
        :param def_string: список с кортежами (тип лексемы, лексема)
        :param number_string: номер строки
        :param len_string: длина строки
        :return: или пустой список или список с кортежем ошибки(номер ошибки, номер строки), экземпляр листа(SynTree)
        """
        error = []
        sheet = SynTree(str_type=2, var_name=def_string[0][1])
        if variables.get(sheet.var_name) is None:
            error.append((14, number_string))
        else:
            sheet.var_type = variables.get(sheet.var_name)[0]
        error.extend(self.end_check(def_string[len_string - 1][1], number_string))
        error.extend(self.equal_check(def_string[1][1], number_string))
        error.extend(self.expression_check(def_string[2:len_string - 1], number_string))
        sheet.value = def_string[2:len_string - 1]
        return error, sheet

    def define_check(self, def_string, number_string, len_string):
        # keyword identifier [= expression];
        """
        Проверяет инициализацию переменной, заносит ее в таблицу
        Если переменная уже в таблицу или что-то не так в объявлении - добавляет ошибку
        Создает и заполняет экземпляр листа SynTree
        :param def_string: список с кортежами (тип лексемы, лексема)
        :param number_string: номер строки
        :param len_string: длина строки
        :return: или пустой список или список с кортежем ошибки(номер ошибки, номер строки), экземпляр листа(SynTree)
        """
        error = []
        sheet = SynTree(str_type=1, var_type=def_string[0][1])
        if def_string[1][0] == "identifier":
            sheet.var_name = def_string[1][1]
        else:
            error.append((2, number_string))
        error.extend(self.end_check(def_string[len_string - 1][1], number_string))
        if variables.get(sheet.var_name) is None:
            variables[sheet.var_name] = (sheet.var_type, None)
        else:
            error.append((15, number_string))
        if len_string > 3:
            error.extend(self.equal_check(def_string[2][1], number_string))
            error.extend(self.expression_check(def_string[3:len_string - 1], number_string))
            sheet.value = def_string[3:len_string - 1]
            variables[sheet.var_name] = (sheet.var_type, sheet.value)
        return error, sheet

    def type_analysis(self, untype_string, number_string):
        """
        Проверяет первое слово строки и возвращает ее тип
        :param untype_string: список кортежей (токен, слово)
        :param number_string: номер строки
        :return: тип строки
        """
        if untype_string[0][0] == "keyword":
            if untype_string[0][1] == "while":
                return 3
            elif untype_string[0][1] in self.var_types:
                return 1
        elif untype_string[0][1] == "}" or untype_string[0][1] == "{":
            return 4
        elif untype_string[0][0] == "identifier":
            return 2
        else:
            print("Syntax error in line {} in word {}".format(number_string, untype_string[0][1]))
            return 0

    def do_syntax_analysis(self):
        """
        Создает дерево. Бежит по строкам, получает тип строки, функцию ее обработки, результат обработки.
        Если ошибка - вызывает печать ошибок.
        Добавляет элемент в дерево, проверяет, закрыт ли цикл.
        :return: root - дерево
        """
        root = SynTree()
        for one_str in self.input_string:
            current_number = self.number_str[self.input_string.index(one_str)]
            result = self.type_analysis(one_str, current_number)
            if result == 0:
                self.analysis_error = 1
            f = getattr(Code_analysis, self.types[result])
            result = f(self, one_str, current_number, len(one_str))
            if result[0]:
                self.print_error(result[0])
                self.analysis_error = 1
            if root.root is None:
                root = result[1]
                root.root = result[1]
            else:
                root.add_item(result[1], check_obj=self)
                if self.while_stack:
                    # если в стеке статус 1, а текущий элемент элемент не цикл, то после него добавляем закрытие цикла
                    if self.while_stack[-1][1] == 1 and result[1].str_type != 3:
                        from_stack = self.while_stack.pop()
                        sheet = SynTree(str_type=5, var_name=from_stack[0])
                        root.add_item(sheet, check_obj=self)
        # если цикл не закрыт
        if self.while_stack:
            print("Error: the loop was not closed")
        elif self.analysis_error == 0:
            root.print_sheet()
        return root

    def give_token(self, word, number_string):
        """
        Проверяет входное слово регулярками и дает токен
        :param word: лексема
        :param number_string: номер строки
        :return: возвращает кортеж (токен, слово)
        """
        keys = self.tokens.keys()
        for key in keys:
            if re.match(key, word):
                return self.tokens[key], word
        print("Error: incorrect word {} in line {}".format(word, number_string))

    def do_lexical_analysis(self, filename):
        """
        Считывает построчно с файла. Удаляет комментарии, пробелы, пустые строки.
        Делит по словам, получает токены слов, отправляет строки в self.input_string
        :param filename: имя файла на вход
        :return:
        """
        f = open(filename, 'r')
        i = 0
        for line in f:
            i += 1
            if not re.match(r"\s*\n", line):  # проверка на пустую строку
                if re.match(r"(.*)//", line):  # проверка на комментарии
                    line = re.match(r"(.*)//", line).group(1)
                    if not re.match(r"\w", line):  # проверка на наличие букв
                        continue
                line = re.sub(r"\t", "", line)
                line = re.sub(r"\n", "", line)
                words_in_line = []
                word = ""
                for letter in line:
                    if letter in self.signs:
                        if word:
                            if word + letter in self.signs:
                                words_in_line.append(word + letter)
                                word = ""
                            else:
                                words_in_line.append(word)
                                word = letter
                        else:
                            word = letter
                    elif letter == " ":
                        if word:
                            words_in_line.append(word)
                            word = ""
                    else:
                        if word in self.signs:
                            words_in_line.append(word)
                            word = ""
                        word += letter
                if word:
                    words_in_line.append(word)
                current_string = []  # список лексем в строке
                for word_in_line in words_in_line:
                    current_string.append(self.give_token(word_in_line, i))
                self.input_string.append(current_string)  # добавление списка слов в строке в список строк
                self.number_str.append(i)
        f.close()


class SynTree:
    types = {1: "define", 2: "assign", 3: "begin_cycle", 4: "braces", 5: "end_cycle"}

    def __init__(self, str_type=None, root=None, parent=None, child=None, value=None, var_name=None,
                 var_type=None):
        self.var_type = var_type
        self.var_name = var_name
        self.value = value
        self.child = child
        self.parent = parent
        self.str_type = str_type
        self.root = root

    def __str__(self):
        return "Type_var: {}, name: {}, value: {}, type_str: {}".format(self.var_type, self.var_name, self.value,
                                                                        self.str_type)

    def add_item(self, obj, check_obj=None):
        """
        Рекурсивно добавляет obj в конец дерева.
        Если добавляем закрытие цикла после цикла - кидает ошибку.
        :param obj: объект типа листа SynTree
        :param check_obj: Объект анализатора кода для ошибки
        :return:
        """
        if obj.str_type is not None:
            if self.child is None:
                if obj.str_type == 5 and self.str_type == 3:
                    print("Error: the loop cannot be empty")
                    check_obj.analysis_error = 1
                self.child = obj
                self.child.parent = self
            else:
                self.child.add_item(obj)

    def print_sheet(self):
        """
        Рекурсивно выводит дерево
        :return:
        """
        print("Тип переменной: {}, имя переменной: {}, значение переменной: {}, тип строки: {}".format(self.var_type,
                                                                                                       self.var_name,
                                                                                                       self.value,
                                                                                                       self.types[
                                                                                                           self.str_type]))
        if self.child is not None:
            self.child.print_sheet()


class Expressions:
    signs = ['+', '-', '*', '/', '<', '>', '<=', '>=', '==', '!=']
    status = {'+': 2, '-': 2, '*': 3, '/': 3, '(': 0, '<': 1, '>': 1, '<=': 1, '>=': 1, '==': 1, '!=': 1}

    def __init__(self):
        self.stack = []
        self.errors = []

    def check_expression(self, expression, number_string):
        """
        Проверяет всевозможные ошибки выражений, переменных, скобок
        :param expression: список кортежей (токен, слово)
        :param number_string: номер строки
        :return: ничего, но потом ошибки берутся из self.errors[]
        """
        last_element = ""
        for element in expression:
            if not (element[0] == "literal" or element[0] == "identifier"):
                if last_element == "" and element[1] != '(':
                    self.errors.append((8, number_string))
                action = 0
                if element[1] in self.signs:
                    if last_element == "operator" or last_element == "open_brace":
                        self.errors.append((10, number_string))
                    last_element = "operator"
                    if len(self.stack) == 0:
                        self.stack.append(element[1])
                    else:
                        self.add_in_stack(element[1])
                    action = 1
                if element[1] == '(':
                    if last_element == "close_brace":
                        self.errors.append((12, number_string))
                    last_element = "open_brace"
                    self.stack.append(element[1])
                    action = 1
                if element[1] == ')':
                    if last_element == "open_brace" or last_element == "operator":
                        self.errors.append((12, number_string))
                    last_element = "close_brace"
                    self.close_braces(number_string)
                    action = 1
                if action == 0:
                    self.errors.append((6, number_string))
            else:
                if element[0] == "identifier":
                    if variables.get(element[1]) is None:
                        self.errors.append((14, number_string))
                    elif variables.get(element[1])[1] is None:
                        self.errors.append((16, number_string))
                if last_element != "var":
                    last_element = "var"
                else:
                    self.errors.append((11, number_string))
        if last_element == "operator":
            self.errors.append((9, number_string))
        while len(self.stack) != 0:
            current_element = self.stack.pop()
            if current_element == '(':
                self.errors.append((7, number_string))

    def add_in_stack(self, current_operator):
        """
        Добавляет оператор в стек, если статус в элемента стеке больше или равен.
        :param current_operator: оператор для стека
        :return:
        """
        while len(self.stack) != 0 and self.status[current_operator] <= self.status[self.stack[-1]]:
            self.stack.pop()
        self.stack.append(current_operator)

    def close_braces(self, number_string):
        """
        Ищет в стеке открывающую скобку и выкидывает все до нее из стека.
        :param number_string: номер строки
        :return: ничего, добавляет ошибку, если есть
        """
        if len(self.stack) == 0:
            self.errors.append((7, number_string))
            return
        while self.stack[len(self.stack) - 1] != "(":
            self.stack.pop()
            if len(self.stack) == 0:
                self.errors.append((7, number_string))
                return
        self.stack.pop()


class Generator:
    def __init__(self):
        self.Q = 1
        self.quest = "Q{}: {}\n"
        self.answer = "A{}: {}\n"
        self.variable = "&{}&"

    def generate(self, tree_root, file_name):
        """
        Открывает файл, выводит туда все строки, закрывает.
        :param tree_root: первый элемент дерева
        :param file_name: имя файла
        :return:
        """
        f = open(file_name, 'w')
        self.string_generator(tree_root, f)
        f.close()

    def value_to_code(self, value_list):
        """
        Парсит список в строку, добавляя пробелы и обрамляя переменные в '&'.
        :param value_list: список с кортежами лексем
        :return: Выходная строка
        """
        output_str = ""
        for value in value_list:
            if value[0] == "identifier":
                output_str += self.variable.format(value[1]) + " "
            else:
                output_str += value[1] + " "
        return output_str

    def string_generator(self, sheet, file):
        """
        В зависимости от типа строки генерит нужную выходную строку и печатает в файл.
        Рекурсивно вызывается от ребенка листа.
        :param sheet: лист дерева
        :param file: файл для записи
        :return:
        """
        if sheet.str_type == 1:
            file.write(self.quest.format(self.Q, self.variable.format(sheet.var_name)))
            if sheet.value is not None:
                file.write(self.answer.format(self.Q + 0.1, self.value_to_code(sheet.value)))
            else:
                file.write(self.answer.format(self.Q + 0.1, ""))
        elif sheet.str_type == 2:
            file.write(self.quest.format(self.Q, self.variable.format(sheet.var_name) + " := " + self.value_to_code(
                sheet.value)))
        elif sheet.str_type == 3:
            file.write(self.quest.format(self.Q, "LABEL " + self.variable.format(sheet.var_name)))
            self.Q += 1
            file.write(self.quest.format(self.Q, "IF " + self.value_to_code(sheet.value) + " THEN BEGIN"))
        elif sheet.str_type == 5:
            file.write(self.quest.format(self.Q, "END ELSE GOTO " + self.variable.format(sheet.var_name + "end")))
            self.Q += 1
            file.write(self.quest.format(self.Q, "LABEL " + self.variable.format(sheet.var_name + "end")))
        self.Q += 1
        if sheet.child is not None:
            self.string_generator(sheet.child, file)


program = Code_analysis()
program.do_lexical_analysis('input.txt')
for word in program.input_string:
    print(word)
tree = program.do_syntax_analysis()
code = Generator()
code.generate(tree, 'output.txt')
